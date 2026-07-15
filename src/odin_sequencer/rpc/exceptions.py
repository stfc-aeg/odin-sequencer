

class RpcServerError(Exception):
    """Exception raised for errors encountered in the RPC server.

    Attributes:
        code: Error code associated with the exception.
        message: Description of the error.
        data: Additional data related to the error.

    """

    def __init__(self, code, message, data):
        """Initialize RpcServerError with error code, message, and additional data.

        Args:
            code: Error code associated with the exception.
            message: Description of the error.
            data: Additional data related to the error.

        """
        super().__init__(f"{message}: {data}")
        self.code = code
        self.message = message
        self.data = data

