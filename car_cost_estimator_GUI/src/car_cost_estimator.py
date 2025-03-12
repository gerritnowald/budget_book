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
    consumption_electric = slider_electric_consumption.get()
    consumption_gasoline = slider_gasoline_consumption.get()

    price_electric = slider_electric_price.get() / 100
    price_gasoline = slider_gasoline_price.get()

    fix_electric = slider_electric_fix.get()
    fix_gasoline = slider_gasoline_fix.get()

    # calculation
    cost_electric = distance_per_year / 100 * consumption_electric * price_electric + fix_electric
    cost_gasoline = distance_per_year / 100 * consumption_gasoline * price_gasoline + fix_gasoline

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
fig = Figure(figsize=(5, 4), dpi=100)
ax = fig.add_subplot(111)
plot_electric, = ax.plot(distance_per_year, distance_per_year, label="electric")
plot_gasoline, = ax.plot(distance_per_year, distance_per_year, label="gasoline")
ax.set_xlabel("distance per year / km")
ax.set_ylabel("yearly operating costs / €")
ax.legend(loc="upper left")
ax.grid()
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack()

# sliders
frame_gasoline = tk.Frame(root)
frame_gasoline.pack(side=tk.LEFT)

label_gasoline = tk.Label(frame_gasoline, text="Combustion Car")
label_gasoline.pack()

slider_gasoline_consumption = tk.Scale(frame_gasoline, from_=3, to=15, resolution=0.5, orient=tk.HORIZONTAL, label="consumption / l/100km", command=update_plot, length=200)
slider_gasoline_consumption.set(consumption_gasoline)
slider_gasoline_consumption.pack()

slider_gasoline_price = tk.Scale(frame_gasoline, from_=1, to=3, resolution=0.1, orient=tk.HORIZONTAL, label="gasoline price / €/l", command=update_plot, length=200)
slider_gasoline_price.set(price_gasoline)
slider_gasoline_price.pack()

slider_gasoline_fix = tk.Scale(frame_gasoline, from_=0, to=2000, resolution=10, orient=tk.HORIZONTAL, label="fixed costs / €", command=update_plot, length=200)
slider_gasoline_fix.set(500)
slider_gasoline_fix.pack()


frame_electric = tk.Frame(root)
frame_electric.pack(side=tk.RIGHT)

label_electric = tk.Label(frame_electric, text="Electric Car")
label_electric.pack()

slider_electric_consumption = tk.Scale(frame_electric, from_=10, to=30, orient=tk.HORIZONTAL, label="consumption / kWh/100km", command=update_plot, length=200)
slider_electric_consumption.set(consumption_electric)
slider_electric_consumption.pack()

slider_electric_price = tk.Scale(frame_electric, from_=0, to=100, orient=tk.HORIZONTAL, label="electricity price / ct/kWh", command=update_plot, length=200)
slider_electric_price.set(price_electric)
slider_electric_price.pack()

slider_electric_fix = tk.Scale(frame_electric, from_=0, to=2000, resolution=10, orient=tk.HORIZONTAL, label="fixed costs / €", command=update_plot, length=200)
slider_electric_fix.set(500)
slider_electric_fix.pack()


root.mainloop()