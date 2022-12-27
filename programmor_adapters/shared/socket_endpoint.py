import asyncio
import socketio
from shared.endpoint import Endpoint
from shared.api import API



class SocketEndpoint(Endpoint):
    """SocketIO Endpoint
    """
    def __init__(self, loop: asyncio.AbstractEventLoop, api: API) -> None:
        super().__init__(loop, api)
        # Starts the SocketIO Endpoint Application
        self.app = socketio.AsyncServer()
        self.loop.run_until_complete(self.app)

    def stop(self) -> None:
        """Stops the SocketIO Endpoint Application
        """
        self.app.stop()
