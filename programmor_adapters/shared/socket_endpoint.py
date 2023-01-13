from shared.endpoint import Endpoint
from shared.api import API
from flask import Flask
from flask_socketio import SocketIO, Namespace


class SocketEndpoint(Endpoint):

    class SocketNamespace(Namespace):
        """Socket Namespace
        """
        def on_connect(self):
            """Client Connects
            """
            pass

        def on_disconnect(self):
            """Client Disconnects
            """
            pass

        def on_my_event_name(self):
            """My Event Name
            Event name must be prefixed with `on_`.
            """
            pass

        def on_get_devices(self, data):
            pass

    """SocketIO Endpoint; This is a singleton
    """
    def __init__(self, app: Flask, api: API) -> None:
        super().__init__(app, api)
        self.socket: SocketIO = SocketIO(app)
        self.socket.on_namespace(self.SocketNamespace('/'))

    def start(self) -> None:
        """Starts both the Flask, and the Socket app
        """
        self.socket.run(self.app)

    def stop(self) -> None:
        """Stops the application
        """
        self.socket.stop()
