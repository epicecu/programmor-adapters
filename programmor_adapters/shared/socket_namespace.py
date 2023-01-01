from socketio import AsyncServer, AsyncNamespace
from shared.api import API

#NOTE https://python-socketio.readthedocs.io/en/latest/server.html#class-based-namespaces


class SocketNamespace(AsyncNamespace):
    """SocketIO Namespace; This is a singleton
    """
    def on_connect(self, sid: AsyncServer, environ):
        """Client Connects
        """
        pass

    def on_disconnect(self, sid: AsyncServer):
        """Client Disconnects
        """
        pass

    def on_my_event_name(self):
        """My Event Name
        Event name must be prefixed with `on_`.
        """
        pass

    def on_get_devices(self, sid: AsyncServer):
        pass