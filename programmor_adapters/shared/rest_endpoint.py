import asyncio
from aiohttp import web
from shared.endpoint import Endpoint
from shared.api import API


class RestEndpoint(Endpoint):
    """REST Endpoint
    """
    def __init__(self, loop: asyncio.AbstractEventLoop, api: API) -> None:
        super().__init__(loop, api)
        # Starts the REST Endpoint Application
        self.app = web.Application()
        self.loop.run_until_complete(self.app)

    def stop(self) -> None:
        """Stops the REST Endpoint Application
        """
        self.app.stop()
