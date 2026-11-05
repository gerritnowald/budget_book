"""Extracts German bank statements from a text-based PDF and appends them to the database CSV, one row per transaction. 

Transaction amounts are signed (`debit` transactions are negative), and `Kontostand` is the running balance calculated from the statement's opening balance. 
The calculated final balance must match the statement's closing balance.
"""

import argparse
import re
import sys
import os
import warnings
from decimal import Decimal, InvalidOperation
from pathlib import Path

import numpy as np
import pandas as pd
from pypdf import PdfReader
from joblib import load
import yaml

# read settings from config file
with open("config.ini", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
clm = cfg['column names database']

CSV_FIELDS = [clm["date"], clm["type"], clm["text"], clm["amount"], clm["category"], clm["balance"], "confidence"]

# -----------------------------------------------------------------------------------
# parse PDF text into transactions

AMOUNT_RE = re.compile(r"^(?P<sign>[+-])\s*(?P<Betrag>[\d.]+,\d{2})(?P<tail>.*)$")
DATE_RE = re.compile(r"\b(?P<day>\d{2})\.(?P<month>\d{2})\.\s*(?P<year>\d{4})\b")
DATE_PART_RE = re.compile(r"^(?:\d{2}\.\d{2}\.|\d{4})$")
REFERENCE_MARKER = re.compile(r"^Verwendungszweck/\s*Kundenreferenz\s*$", re.I)
FOOTER_RE = re.compile(r"\bNeuer\s+Saldo\s+[+-]\s*[\d.]+,\d{2}\s*EUR\b", re.I)
NOISE_RE = re.compile(r"^(HabenSollVorgangValutaBuchung|IBANvonSeiteAuszug|\d+\s*/\s*\d+\s*/\s*\d+)$")

def normalize_lines(text: str) -> list[str]:
    """Normalize extracted PDF text and remove known statement noise."""
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if line and not NOISE_RE.fullmatch(line):
            lines.append(line)
    return lines


def extract_blocks(reader: PdfReader) -> list[list[str]]:
    """Split PDF text into transaction blocks."""
    blocks: list[list[str]] = []
    current: list[str] = []
    for page in reader.pages:
        for line in normalize_lines(page.extract_text() or ""):
            amount_match = AMOUNT_RE.match(line)
            is_balance_header = amount_match and (
                amount_match.group("tail").startswith("EUR")
                or "IBAN" in amount_match.group("tail")
            )
            if amount_match and not is_balance_header:
                if current:
                    blocks.append(current)
                current = [line]
            elif current:
                current.append(line)
        if current:
            blocks.append(current)
            current = []
    return blocks


def parse_amount(value: str) -> Decimal:
    """Convert a German-formatted amount string to a decimal value."""
    return Decimal(value.replace(".", "").replace(",", "."))


def parse_statement_balances(reader: PdfReader) -> dict[str, Decimal]:
    """Extract the opening and closing balances from a bank statement PDF."""
    text = " ".join(
        line
        for page in reader.pages
        for line in normalize_lines(page.extract_text() or "")
    )
    balance_pattern = r"(?P<sign>[+-])\s*(?P<Betrag>[\d.]+,\d{2})\s*EUR"
    opening_match = re.search(r"Alter Saldo.*?" + balance_pattern, text, re.I)
    closing_match = re.search(r"Neuer Saldo.*?" + balance_pattern, text, re.I)
    if not opening_match or not closing_match:
        raise ValueError("Could not find opening and closing statement balances")

    def signed_balance(match: re.Match[str]) -> Decimal:
        """Convert a signed balance match to a decimal value."""
        Betrag = parse_amount(match.group(clm["amount"]))
        return Betrag if match.group("sign") == "+" else -Betrag

    return {
        "opening": signed_balance(opening_match),
        "closing": signed_balance(closing_match),
    }


def parse_block(lines: list[str]) -> dict[str, Decimal | str | int]:
    """Parse one extracted statement block into a transaction."""
    match = AMOUNT_RE.match(lines[0])
    if not match:
        raise ValueError(f"Block does not start with an amount: {lines[0]!r}")

    Betrag = parse_amount(match.group(clm["amount"]))
    if match.group("sign") == "-":
        Betrag = -Betrag
    first_tail = match.group("tail").strip()
    body = [first_tail, *lines[1:]] if first_tail else lines[1:]
    body = [line for line in body if line]

    dates = DATE_RE.findall(" ".join(body))
    parsed_dates = [f"{year}-{month}-{day}" for day, month, year in dates[:2]]

    reference_index = next(
        (index for index, line in enumerate(body) if REFERENCE_MARKER.match(line)),
        None,
    )
    header_lines = body[:reference_index] if reference_index is not None else body
    purpose_lines = body[reference_index + 1 :] if reference_index is not None else []
    
    Buchungstext = " ".join(line for line in purpose_lines if not DATE_PART_RE.fullmatch(line))
    Buchungstext = FOOTER_RE.split(Buchungstext, maxsplit=1)[0].rstrip()

    # split a header like: "Überweisung an Max Mustermann" into:
    # type = "Überweisung"
    # role = "an"
    # party = "Max Mustermann"
    Vorgang = ""
    Glaeubiger = ""
    header = " ".join(line for line in header_lines if not DATE_PART_RE.fullmatch(line))
    type_match = re.match(r"(?P<type>.+?)(?:\s+(?P<role>von|an)\s+(?P<party>.+))?$", header, re.I)
    if type_match:
        Vorgang = type_match.group("type").strip()
        Glaeubiger = (type_match.group("party") or "").strip()
        if type_match.group("role") and not Glaeubiger:
            Vorgang = header    # fallback for incomplete data like "Überweisung an" or "Zahlung von"
    if Glaeubiger:
        Buchungstext = Glaeubiger + " " + Buchungstext

    return {
        clm["amount"]: Betrag,
        clm["date"]: parsed_dates[1] if len(parsed_dates) > 1 else (parsed_dates[0] if parsed_dates else ""),
        clm["type"]: Vorgang,
        clm["text"]: Buchungstext,
        clm["category"]: "",
        "confidence": 0,
    }

# -----------------------------------------------------------------------------------
# classify new transactions

def categorize_transactions(transactions: pd.DataFrame) -> None:
    """Assign categories and confidence scores using the configured classifier."""

    # add rows and exit early if there are no transactions to classify
    if transactions.empty:
        transactions[clm["category"]] = pd.Series(dtype="object")
        transactions["confidence"]    = pd.Series(dtype="int64")
        return

    # prepare model input
    model_input = transactions[
        [clm["date"], clm["type"], clm["text"], clm["amount"]]
    ].copy()
    model_input[clm["date"]] = pd.to_datetime(model_input[clm["date"]])
    model_input[clm["amount"]] = model_input[clm["amount"]].astype(float)

    # predict categories based on confidence scores
    classifier = load(cfg["categorizer file"] + ".joblib")
    probabilities = np.round(classifier.predict_proba(model_input) * 100)   # ndarray of shape (n_samples, n_classes)
    max_indices   = np.argmax(probabilities, axis=1)
    transactions[clm["category"]] = classifier.classes_[max_indices]
    transactions["confidence"]    = probabilities[np.arange(probabilities.shape[0]), max_indices].astype(int)
    transactions.loc[transactions["confidence"] < 50, clm["category"]] = "Unbekannt"

# -----------------------------------------------------------------------------------
# write transactions to CSV

def write_csv(
    path: Path,
    transactions: pd.DataFrame,
    opening_balance: Decimal,
) -> None:
    """Append transactions unless their date range overlaps the database."""
    Kontostand = opening_balance
    if path.exists() and path.stat().st_size > 0:
        existing_rows = pd.read_csv(
            path,
            dtype=str,
            keep_default_na=False,
            encoding="ISO-8859-1",
        )
        if not existing_rows.empty:
            Kontostand = Decimal(existing_rows.iloc[-1][clm["balance"]])
    else:
        existing_rows = pd.DataFrame(columns=CSV_FIELDS)

    existing_rows = existing_rows.reindex(columns=CSV_FIELDS, fill_value="")
    if not transactions.empty:
        transaction_dates = pd.to_datetime(transactions[clm["date"]], errors="coerce")
        if transaction_dates.isna().any():
            raise ValueError("Cannot check database date range: a new transaction has no valid date")

        existing_dates = pd.to_datetime(existing_rows[clm["date"]], errors="coerce").dropna()
        if not existing_dates.empty:
            new_start = transaction_dates.min()
            new_end = transaction_dates.max()
            database_start = existing_dates.min()
            database_end = existing_dates.max()
            if new_end < database_start:
                raise ValueError(
                    f"Transaction date range {new_start:%Y-%m-%d} to {new_end:%Y-%m-%d} "
                    f"predates database date range {database_start:%Y-%m-%d} "
                    f"to {database_end:%Y-%m-%d}; only later ranges can be appended"
                )
            if new_start <= database_end and new_end >= database_start:
                raise ValueError(
                    f"Transaction date range {new_start:%Y-%m-%d} to {new_end:%Y-%m-%d} "
                    f"overlaps database date range {database_start:%Y-%m-%d} "
                    f"to {database_end:%Y-%m-%d}"
                )

    new_rows = transactions.reindex(
        columns=[field for field in CSV_FIELDS if field != clm["balance"]],
        fill_value="",
    ).copy()
    amounts = new_rows[clm["amount"]].map(
        lambda amount: amount if isinstance(amount, Decimal) else Decimal(str(amount))
    )
    new_rows[clm["amount"]] = amounts.map(lambda amount: f"{amount:.2f}")
    new_rows[clm["balance"]] = amounts.cumsum().map(
        lambda balance: f"{Decimal(str(balance)) + Kontostand:.2f}"
    )

    combined_rows = pd.concat(
        [existing_rows, new_rows.reindex(columns=CSV_FIELDS)],
        ignore_index=True,
    )
    combined_rows.to_csv(path, index=False, encoding="ISO-8859-1")

# -----------------------------------------------------------------------------------
# main program

def main() -> int:
    """Parse arguments and import transactions from the selected PDF files."""

    # parse command-line arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-p",
        "--pdf",
        type=Path,
        nargs="*",
        help="Input bank-statement PDF(s); defaults to all PDFs in the current folder",
    )
    parser.add_argument(
        "-d",
        "--database",
        type=Path,
        default=Path("Umsaetze_DONT_SORT.csv"),
        help="Existing transaction database CSV to append to",
    )
    args = parser.parse_args()

    # find PDF files to process
    pdfs: list[Path] = args.pdf or sorted(Path.cwd().glob("*.pdf"))
    if not pdfs:
        parser.error("No PDF files found")

    if not args.database.exists():
        warnings.warn(f"Database {args.database} does not exist; creating it")

    # process each PDF and append transactions to the database
    total_transactions = 0
    for pdf in pdfs:
        print(f"parsing {pdf}")
        reader = PdfReader(str(pdf))
        statement_balances = parse_statement_balances(reader)
        transaction_data = pd.DataFrame.from_records(
            [parse_block(lines) for lines in extract_blocks(reader)],
            columns=[field for field in CSV_FIELDS if field != clm["balance"]],
        )
        calculated_balance = statement_balances["opening"] + sum(
            (Decimal(str(amount)) for amount in transaction_data[clm["amount"]]),
            Decimal("0"),
        )
        if calculated_balance != statement_balances["closing"]:
            raise ValueError(
                "Calculated closing balance "
                f"{calculated_balance:.2f} does not match statement closing balance "
                f"{statement_balances['closing']:.2f}"
            )
        print('finished parsing new transactions')
        
        categorize_transactions(transaction_data)
        print('finished categorizing new transactions')

        write_csv(args.database, transaction_data, statement_balances["opening"])
        total_transactions += len(transaction_data)
        print(f'new transactions appended to database')

    print(f"Wrote {total_transactions} transactions from {len(pdfs)} PDFs to {args.database}")

    # open transaction editor
    print('start transaction editor')
    os.system(f"python transaction_editor.py -r {total_transactions - 1}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (InvalidOperation, OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)