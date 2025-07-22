import tkinter as tk
from tkinter import font as tkfont

# Create main window
root = tk.Tk()
root.title("Tkinter Test")
root.geometry("600x600")  # Set window size

# Create a custom font
custom_font = tkfont.Font(size=14, weight="bold")

# Create a centered label
label = tk.Label(
    root,
    text="You have Tkinter installed!",
    font=custom_font,
    pady=20  # Add vertical padding
)

# Center the label using pack()
label.pack(expand=True)  # expand=True centers the widget

# Start the main event loop
root.mainloop()
