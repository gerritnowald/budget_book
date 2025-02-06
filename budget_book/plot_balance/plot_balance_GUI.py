import pandas as pd
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

N = 10  # start value for slider

# ----------------------------------------------------------------------
# functions

def load_csv():
    file_path = tk.filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        data = pd.read_csv(file_path).iloc[::-1] # Reverse the order of the rows
        
        # plot data
        ax.clear()
        ax.plot(data.iloc[:, 0], data.iloc[:, 2])
        ax.set_xlabel(data.columns[0])
        ax.set_ylabel(data.columns[2])
        ax.grid()

        # adjust sliders
        N = data.iloc[:, 0].unique().size   # multiple values with same date
        slider_min.config(to=N)
        slider_max.config(to=N)
        slider_min.set(0)
        slider_max.set(N)

        canvas.draw()

def update_xlim(val):
    Nmin = slider_min.get()
    Nmax = slider_max.get()
    ax.set_xlim(Nmin, Nmax)
    slider_min.config(to = Nmax - 1)
    slider_max.config(from_ = Nmin + 1)
    canvas.draw()

# ----------------------------------------------------------------------
# create GUI elements

root = tk.Tk()
root.title("plot balance over time")

# Load CSV button
button = tk.Button(root, text="Load CSV", command=load_csv)
button.pack()

# figure and plot
fig = Figure(figsize=(10, 8), dpi=100)
ax = fig.add_subplot(111)
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.draw()
canvas.get_tk_widget().pack()

# sliders to adjust x-axis limits
slider_min = tk.Scale(root, from_=0, to=N, orient=tk.HORIZONTAL, label="X min", command=update_xlim, length=400)
slider_min.pack()
slider_max = tk.Scale(root, from_=0, to=N, orient=tk.HORIZONTAL, label="X max", command=update_xlim, length=400)
slider_max.set(N)
slider_max.pack()

root.mainloop()