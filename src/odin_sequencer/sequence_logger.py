"""Small module providing a logger class for sequence modules, enabling log levels.
Mika Shearwood, STFC DSSG"""

class SequenceLogger:
    """Logger injected into sequence modules as 'log' to provide levels.
    This class replicates typical 'logger' functionality.
    Arguments receive a message and args used to augment the message string.
    This allows for formatting of strings in expected formats:
    - f"", .format, "%d" % var, ("%d", var)
    for multi-string parsing like `print("foo", "bar")`, use print
    """

    def __init__(self, sink):
        """Initialize the logger.
        
        :param sink: the logging function to send log messages to (e.g., manager.log_message)
        """
        self.sink = sink

    def debug(self, msg, *args):
        """Log a debug level message."""
        self._emit(msg, "debug", *args)

    def info(self, msg, *args):
        """Log an info level message."""
        self._emit(msg, "info", *args)
    
    def warning(self, msg, *args):
        """Log a warning level message."""
        self._emit(msg, "warning", *args)
    
    def error(self, msg, *args):
        """Log an error level message."""
        self._emit(msg, "error", *args)
    
    def _emit(self, msg, level, *args):
        """Emit a log message at the specified level.
        
        :param level: the log level as string (e.g. 'info', 'debug', etc.)
        :param *args: variable list of positional arguments to form the log message
        """
        if args:
            try:
                msg = msg % args
            except Exception as e:
                msg = f"Error in log format: {e}. MSG: {msg} ARGS: {args}"
                level="error"

        self.sink(msg, level=level)