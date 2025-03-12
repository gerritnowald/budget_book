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
        data = pd.read_csv(file_path, encoding = 'ISO-8859-1').iloc[::-1] # Reverse the order of the rows
        
        # plot data
        ax.clear()
        ax.plot(data.iloc[:, 0], data.iloc[:, 2])
        ax.set_xlabel(data.columns[0])
        ax.set_ylabel(data.columns[2])
        ax.grid()

        xlabelinput.delete(0,tk.END)
        xlabelinput.insert(0,data.columns[0])
        ylabelinput.delete(0,tk.END)
        ylabelinput.insert(0,data.columns[2])

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

def update_labels():
    xlabel = xlabelinput.get()
    ylabel = ylabelinput.get()
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    canvas.draw()

def save_plot():
    file_path = tk.filedialog.asksaveasfilename(filetypes=[("PNG files", "*.png")])
    if file_path:
        fig.savefig(file_path)

# ----------------------------------------------------------------------
# create GUI elements

root = tk.Tk()
root.title("plot balance over time")


# Load CSV button
button = tk.Button(root, text="Load CSV", command=load_csv)
button.pack()


# figure and plot
fig = Figure(figsize=(5, 4), dpi=100)
ax = fig.add_subplot(111)
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.draw()
canvas.get_tk_widget().pack()


# frame for input elements
input_frame = tk.Frame(root)
input_frame.pack()


# sliders to adjust x-axis limits
slider_frame = tk.Frame(input_frame)
slider_frame.pack(side=tk.LEFT)

slider_min = tk.Scale(slider_frame, from_=0, to=N, orient=tk.HORIZONTAL, label="X min", command=update_xlim, length=200)
slider_min.pack()
slider_max = tk.Scale(slider_frame, from_=0, to=N, orient=tk.HORIZONTAL, label="X max", command=update_xlim, length=200)
slider_max.set(N)
slider_max.pack()


# textboxes to set x and y labels
textbox_frame = tk.Frame(input_frame)
textbox_frame.pack(side=tk.RIGHT)

# x label
xlabel_frame = tk.Frame(textbox_frame)
xlabel_frame.pack(side=tk.TOP)

xlabel = tk.Label(xlabel_frame, text="X label")
xlabel.pack(side=tk.LEFT)

xlabelinput = tk.Entry(xlabel_frame)
xlabelinput.pack(side=tk.RIGHT)

# y label
ylabel_frame = tk.Frame(textbox_frame)
ylabel_frame.pack()

ylabel = tk.Label(ylabel_frame, text="Y label")
ylabel.pack(side=tk.LEFT)

ylabelinput = tk.Entry(ylabel_frame)
ylabelinput.pack(side=tk.RIGHT)

# set labels button
button = tk.Button(textbox_frame, text="set labels", command=update_labels)
button.pack(side=tk.BOTTOM)


# button to save
button = tk.Button(input_frame, text="Save plot", command=save_plot)
button.pack(side=tk.BOTTOM, padx=20, pady=40)


root.mainloop()