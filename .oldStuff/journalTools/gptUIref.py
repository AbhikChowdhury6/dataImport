import tkinter as tk
from tkinter import Label, Entry
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from PIL import Image, ImageTk

# Create main window
root = tk.Tk()
root.title("Dynamic Interface")
root.geometry("1000x600")

# Frame for images and graphs
frame = tk.Frame(root)
frame.pack()

# Load placeholder images
image_files = ["image1.png", "image2.png", "image3.png", "image4.png", "image5.png"]
images = []
labels = []
for i, file in enumerate(image_files):
    try:
        img = Image.open(file).resize((100, 100))
        img = ImageTk.PhotoImage(img)
    except:
        img = ImageTk.PhotoImage(Image.new('RGB', (100, 100), (200, 200, 200)))
    images.append(img)
    lbl = Label(frame, image=img)
    lbl.grid(row=0, column=i)
    labels.append(lbl)

# Generate initial graphs
figures = []
canvas_list = []
for i in range(5):
    fig = Figure(figsize=(2, 2))
    ax = fig.add_subplot(111)
    x = np.linspace(0, 10, 100)
    y = np.sin(x + i)
    ax.plot(x, y)
    figures.append(fig)
    
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.get_tk_widget().grid(row=1, column=i)
    canvas_list.append(canvas)

# Text boxes
text_entries = []
for i in range(3):
    entry = Entry(root)
    entry.pack()
    text_entries.append(entry)

# Function to update graphs on key press
def update_graphs(event):
    for i, canvas in enumerate(canvas_list):
        fig = figures[i]
        fig.clear()
        ax = fig.add_subplot(111)
        x = np.linspace(0, 10, 100)
        y = np.cos(x + i + np.random.rand())  # Change function dynamically
        ax.plot(x, y, color='red')
        canvas.draw()

root.bind("<KeyPress>", update_graphs)

root.mainloop()
