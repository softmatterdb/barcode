import time


def get_time_as_string(time_s: float) -> str:
    """Convert time in seconds to a formatted string."""
    if time_s / 3600 > 1:
        t_hr = int(time_s // 3600)
        t_min = (time_s - (t_hr * 3600)) / 60
        return f"{t_hr:.2f} hours, {t_min:.2f} minutes"
    elif time_s / 60 > 1:
        t_min = time_s / 60
        return f"{t_min:.2f} minutes"
    else:
        return f"{time_s:.2f} seconds"


class Timer:
    """A simple timer class to log elapsed time to a file and console."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.file = None
        self.start_time = None
        self.last_log_time = None
        self.end_time = None

    def start(self):
        """Start the timer and open the log file."""
        self.file = open(self.filepath, "w", encoding="utf-8")
        self.file.write(self.filepath + "\n")
        self.start_time = time.time()
        self.last_log_time = self.start_time

    def _log_time_since(self, _time: float, message: str = "") -> str:
        """Log a message with the time elapsed since a given time."""
        current_time = time.time()
        elapsed_time = current_time - _time
        elapsed_time_str = get_time_as_string(elapsed_time)

        log_message = f"{message}: {elapsed_time_str}" if message else elapsed_time_str
        self.file.write(f"{log_message}\n")
        
        # Import vprint locally to avoid circular import
        from utils import vprint
        vprint(log_message)
        self.last_log_time = current_time

        return log_message

    def log_time_since_last_log(self, message: str = "") -> str:
        """Log the time elapsed since the last log."""
        return self._log_time_since(self.last_log_time, message)

    def log_time_since_start(self, message: str = "") -> str:
        """Log the time elapsed since the timer started."""
        return self._log_time_since(self.start_time, message)

    def stop(self):
        """Stop the timer and close the log file."""
        self.end_time = time.time()
        self.file.close()
