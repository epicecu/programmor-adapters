import asyncio
from shared.api import API


class Endpoint():
    """Endpoint Interface
    """
    def __init__(self, loop: asyncio.AbstractEventLoop, api:API) -> None:
        self.loop = loop
        self.api = api

    def stop(self) -> None:
        """Stops the Endpoint application
        """
        raise NotImplementedError("Stop method not implemented")