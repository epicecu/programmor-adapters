from shared.api import API
from flask import Flask


class Endpoint():
    """Endpoint Interface
    """

    def __init__(self, app: Flask, api: API) -> None:
        self.app = app
        self.api = api

    def start(self) -> None:
        """Starts the Endpoint application
        """
        raise NotImplementedError("Start method not implemented")

    def stop(self) -> None:
        """Stops the Endpoint application
        """
        raise NotImplementedError("Stop method not implemented")
