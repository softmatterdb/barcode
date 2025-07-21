import tkinter as tk
from tkinter import ttk

def create_home_page(parent, switch_page):
    frame = tk.Frame(parent)
    frame.pack(fill="both", expand=True)

    content = tk.Frame(frame)
    content.place(relx=0.5, rely=0.5, anchor="center")

    label = tk.Label(content, text="BARCODE", font=("Helvetica", 36, "bold"))
    label.pack(pady=(0, 20))

    process_button = ttk.Button(content, text="Process Data", command=lambda: switch_page("process"))
    process_button.pack(pady=5)

    combine_button = ttk.Button(content, text="Combine Barcodes")
    combine_button.pack(pady=5)

    return frame