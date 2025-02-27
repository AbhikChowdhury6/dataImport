import tkinter as tk
from tkinter import Label, Entry
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# Create main window
root = tk.Tk()
root.title("Dynamic Interface")
root.geometry("1000x600")

# Frame for images and graphs
frame = tk.Frame(root)
frame.pack()


# global context will be be the current timestamp

# the videos we'll be pulling from
# desk
# mobile
# bathroom
# kitchen

# the time series we'll pull from are 
# apple
# polar
# fitbit

# how about we load up all of the dataframes

# but there'll be some standard methods we'll use to handle the varysing 
#


