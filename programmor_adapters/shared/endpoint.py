from shared.api import API


class Endpoint():
    """Endpoint Interface
    """

    def __init__(self, api: API, port: int) -> None:
        self.api = api
        self.port = port

    def start(self) -> None:
        """Starts the Endpoint application
        """
        raise NotImplementedError("Start method not implemented")

    def stop(self) -> None:
        """Stops the Endpoint application
        """
        raise NotImplementedError("Stop method not implemented")
