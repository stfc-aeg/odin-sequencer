"""Small module providing a logger class for sequence modules, enabling log levels.
Mika Shearwood, STFC DSSG"""

class SequenceLogger:
    """Logger injected into sequence modules as 'log' to provide levels."""

    def __init__(self, sink):
        """Initialize the logger.
        
        :param sink: the logging function to send log messages to (e.g., manager.log_message)
        """
        self.sink = sink

    def debug(self, *args):
        """Log a debug level message."""
        self._emit("debug", *args)

    def info(self, *args):
        """Log an info level message."""
        self._emit("info", *args)
    
    def warning(self, *args):
        """Log a warning level message."""
        self._emit("warning", *args)
    
    def error(self, *args):
        """Log an error level message."""
        self._emit("error", *args)
    
    def _emit(self, level, *args):
        """Emit a log message at the specified level.
        
        :param level: the log level as string (e.g. 'info', 'debug', etc.)
        :param *args: variable list of positional arguments to form the log message
        """
        self.sink(*args, level=level)