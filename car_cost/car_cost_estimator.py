import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import numpy as np

# ----------------------------------------------------------------------
# input

consumption_electric = 20 # kWh/100km
consumption_gasoline = 6 # l/100km

price_electric = 30  # ct/kWh
price_gasoline = 1.5 # €/l

distance_per_year = np.linspace(0, 30000, 100) # km

# ----------------------------------------------------------------------
# functions

def update_plot(val):
    # get values
    consumption_electric = slider_consumption_electric.get()
    consumption_gasoline = slider_consumption_gasoline.get()

    price_electric = slider_price_electric.get() / 100
    price_gasoline = slider_price_gasoline.get()

    # calculation
    cost_electric = distance_per_year / 100 * consumption_electric * price_electric
    cost_gasoline = distance_per_year / 100 * consumption_gasoline * price_gasoline

    # plot data
    plot_electric.set_ydata(cost_electric)
    plot_gasoline.set_ydata(cost_gasoline)
    ax.set_ylim(0, 5_000)
    canvas.draw()

# ----------------------------------------------------------------------
# create GUI elements

root = tk.Tk()
root.title("estimate car operating costs")

# figure and plot
fig = Figure(figsize=(6, 5), dpi=100)
ax = fig.add_subplot(111)
plot_electric, = ax.plot(distance_per_year, distance_per_year, label="electric")
plot_gasoline, = ax.plot(distance_per_year, distance_per_year, label="gasoline")
ax.set_xlabel("distance per year / km")
ax.set_ylabel("operating costs / €")
ax.legend()
ax.grid()
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack()

# sliders
frame_gasoline = tk.Frame(root)
frame_gasoline.pack(side=tk.LEFT)

slider_consumption_gasoline = tk.Scale(frame_gasoline, from_=3, to=15, orient=tk.HORIZONTAL, label="consumption gasoline / l/100km", command=update_plot, length=200)
slider_consumption_gasoline.set(consumption_gasoline)
slider_consumption_gasoline.pack()

slider_price_gasoline = tk.Scale(frame_gasoline, from_=1, to=3, resolution=0.1, orient=tk.HORIZONTAL, label="price gasoline / €/l", command=update_plot, length=200)
slider_price_gasoline.set(price_gasoline)
slider_price_gasoline.pack()


frame_electric = tk.Frame(root)
frame_electric.pack(side=tk.RIGHT)

slider_consumption_electric = tk.Scale(frame_electric, from_=10, to=30, orient=tk.HORIZONTAL, label="consumption electric / kWh/100km", command=update_plot, length=200)
slider_consumption_electric.set(consumption_electric)
slider_consumption_electric.pack()

slider_price_electric = tk.Scale(frame_electric, from_=0, to=100, orient=tk.HORIZONTAL, label="price electric / ct/kWh", command=update_plot, length=200)
slider_price_electric.set(price_electric)
slider_price_electric.pack()


root.mainloop()