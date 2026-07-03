import matplotlib
import tkinter as tk

# import GUI pages directly
from gui.pages.home_page import create_home_page
from gui.pages.processing_page import create_process_page
from gui.pages.analysis_page import create_combine_page

# optional: if setup_main_window is in another file, import directly
from gui.window import setup_main_window, setup_scrollable_container  # or wherever it lives

matplotlib.use("Agg")

def main():
    """Main application entry point"""

    root = setup_main_window()
    # set window size
    window_width = 1000
    window_height = 800

    # get screen dimensions
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # calculate position for centering
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)

    # set geometry with position
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    def switch_page(page_name):
        for widget in root.winfo_children():
            widget.destroy()

        scrollable_frame, canvas = setup_scrollable_container(root)
        if page_name == "home":
            create_home_page(canvas, switch_page)
        elif page_name == "process":
            create_process_page(scrollable_frame, switch_page)
        elif page_name == "combine":
            create_combine_page(scrollable_frame, switch_page)

    # load home page by default
    create_home_page(root, switch_page)
    root.mainloop()


if __name__ == "__main__":
    main()