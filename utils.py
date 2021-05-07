import tkinter as tk
from tkinter import messagebox


def display_message(center):
    top = tk.Tk()
    top.withdraw()
    messagebox.showinfo("Cowin registration", f"{center}", master=top)
    top.destroy()
