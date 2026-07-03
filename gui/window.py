import sys

import tkinter as tk
from tkinter import ttk


def setup_main_window():
    """Create and configure the main application window"""
    root = tk.Tk()
    root.title(
        "BARCODE: Biomaterial Activity Readouts to Categorize, Optimize, Design, and Engineer"
    )
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    # Configure styling
    style = ttk.Style()
    style.configure("TNotebook", borderwidth=0, relief="flat")
    style.map("TNotebook.Tab", focuscolor=[("", "")])

    return root


def setup_scrollable_container(root):
    """Create scrollable container for the GUI"""
    container = ttk.Frame(root)
    container.grid(row=0, column=0, sticky="nsew")

    canvas = tk.Canvas(container, bd=0, highlightthickness=0, takefocus=0)
    v_scroll = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    h_scroll = ttk.Scrollbar(container, orient="horizontal", command=canvas.xview)
    canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

    v_scroll.pack(side="right", fill="y")
    h_scroll.pack(side="bottom", fill="x")
    canvas.pack(side="left", fill="both", expand=True)

    scrollable_frame = ttk.Frame(canvas)
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    def on_frame_config(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    scrollable_frame.bind("<Configure>", on_frame_config)

    # Mouse wheel scrolling
    canvas.bind_all(
        "<MouseWheel>",
        lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"),
    )
    canvas.bind_all(
        "<Shift-MouseWheel>",
        lambda e: canvas.xview_scroll(int(-1 * (e.delta / 120)), "units"),
    )

    return scrollable_frame, canvas


def setup_log_window(root):
    """Create the processing log window and redirect stdout/stderr"""
    log_win = tk.Toplevel(root)
    log_win.title("Processing Log")

    log_frame = ttk.Frame(log_win)
    log_frame.pack(fill="both", expand=True)
    log_frame.rowconfigure(0, weight=1)
    log_frame.columnconfigure(0, weight=1)

    log_text = tk.Text(log_frame, state="disabled", wrap="word", font=("Segoe UI", 10))
    log_text.pack(side="left", fill="both", expand=True)

    log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=log_text.yview)
    log_scroll.pack(side="right", fill="y")
    log_text.configure(yscrollcommand=log_scroll.set)

    class TextRedirector:
        def __init__(self, widget):
            self.widget = widget

        def write(self, msg):
            try:
                self.widget.configure(state="normal")
                self.widget.insert("end", msg)
                self.widget.see("end")
                self.widget.configure(state="disabled")
            except:
                raise Exception("Program Terminated Early")

        def flush(self):
            pass

    sys.stdout = TextRedirector(log_text)
    sys.stderr = TextRedirector(log_text)

    return log_win
