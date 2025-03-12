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

# but there'll be some standard methods we'll use to handle the varying intervals 

# we'll have a target timestamp in the top left and then boxes to type in a new target timestamp
# prepopulated with the current target timestamp or the current target timestamp if not set

# based on that timestamp we'll do a closest matching for the frame
# for the graph we'll just do a query of the 1s dense df of the hr values and display 2 minutes




# how about we do the frames once we settle into the new video schema
# let's start with the time series data

# this UI will be for displaying and modifying intervals
# we already have a method for defining intervals for point measurements like HR
# funny enough this is based on the estimated covariance
# but yes editing the intervals is interesting


#intervals to edit manually
# action triplets
# video to delete
# who knows HR samples while someone else was wearing a device of mine
# similar to sleep









