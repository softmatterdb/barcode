from gui.pages.home_page import create_home_page
from gui.pages.processing_page import create_process_page
from gui.pages.analysis_page import create_combine_page
from gui.frames.analysis.barcode_tab import create_barcode_frame
from gui.frames.process.binarization_tab import create_binarization_frame
from gui.frames.analysis.comparison_tab import create_comparison_frame
from gui.frames.process.execution_tab import create_execution_frame
from gui.frames.process.flow_tab import create_flow_frame
from gui.frames.process.intensity_tab import create_intensity_frame

from gui.window import setup_main_window, setup_scrollable_container, setup_log_window
#hi
__all__ = [
    "create_home_page",
    "create_process_page",
    "create_combine_page",
    "create_barcode_frame",
    "create_binarization_frame",
    "create_comparison_frame",
    "create_execution_frame",
    "create_flow_frame",
    "create_intensity_frame",
    "setup_main_window",
    "setup_scrollable_container",
    "setup_log_window",
]
