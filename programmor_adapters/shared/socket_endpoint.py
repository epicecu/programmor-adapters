from shared.endpoint import Endpoint
from shared.api import API
from shared.types import MessageType, ResponseType
from flask import Flask
from flask_socketio import SocketIO, Namespace, emit
import base64

# Logging
import logging
logger = logging.getLogger(__name__)


class SocketEndpoint(Endpoint):

    """Socket Endpoint
    Provides a SocketIO API endpoint for applications to interface with Programmor
    compatiable devices.
    """

    class ApiNamespace(Namespace):

        """ API Reference
        """
        api: API

        """Socket Namespace
        """

        def on_connect(self):
            """Client Connects
            """
            logger.info("Socket client connected")

        def on_disconnect(self):
            """Client Disconnects
            """
            logger.info("Socket client disconnected")
            self.api.disconnect_all_devices()

        def on_get_devices(self, _):
            """Get Devices
            """
            emit('devices', self.api.get_devices())

        def on_get_devices_detailed(self, _):
            """Get Devices Detailed
            """
            emit('devices_detailed', self.api.get_devices_detailed())

        def on_check_status(self, device_id: str):
            """Check Status

            :param device_id: A Programmor compatible device id
            :type device_id: str
            """
            emit('status', self.api.check_device(device_id))

        def on_connect_device(self, device_id: str):
            """Connect Devices

            :param device_id: A Programmor compatible device id
            :type device_id: str
            """
            if self.api.connect_device(device_id):
                emit('connected', device_id)
            else:
                emit('connected_failed', device_id)

        def on_disconnect_device(self, device_id: str):
            """Disconnect Device

            :param device_id: A Programmor compatible device id
            :type device_id: str
            """
            if self.api.disconnect_device(device_id):
                emit('disconnected', device_id)
            else:
                emit('disconnected_failed', device_id)

        def on_request_common(self, device_id: str, share_id: int):
            """Request Common Message

            :param device_id: A Programmor compatible device id
            :type device_id: str
            :param share_id: Protobuf model share id
            :type device_id: str
            """
            self.api.request_message(device_id, MessageType.COMMON, share_id)

        def on_publish_common(self, device_id: str, share_id: int, data_urlfriendly: str):
            """Publish Common Message
            The data should be encoded using a base64 url friendly function

            :param device_id: A Programmor compatible device id
            :type device_id: str
            :param share_id: Protobuf model share id
            :type device_id: int
            :param data_urlfriendly: Protobuf share data encoded in base64 urlfriendly
            :type data_urlfriendly: str
            """
            data = base64.urlsafe_b64decode(data_urlfriendly)
            self.api.publish_message(device_id, MessageType.COMMON, share_id, data)

        def on_set_scheduled_common(self, device_id: str, share_id: int, interval: int):
            """Set Scheduled Common Message

            :param device_id: A Programmor compatible device id
            :type device_id: str
            :param share_id: Protobuf model share id
            :type device_id: int
            :param interval: Scheduled interval to request share in milliseconds
            :type interval: int
            """
            self.api.set_scheduled_message(device_id, MessageType.COMMON, share_id, interval)

        def on_clear_scheduled_common(self, device_id: str, share_id: int):
            """Clear Scheduled Common Message

            :param device_id: A Programmor compatible device id
            :type device_id: str
            :param share_id: Protobuf model share id
            :type device_id: str
            """
            self.api.clear_scheduled_message(device_id, MessageType.COMMON, share_id)

        def on_request_share(self, device_id: str, share_id: int):
            """Request Share

            :param device_id: A Programmor compatible device id
            :type device_id: str
            :param share_id: Protobuf model share id
            :type device_id: str
            """
            self.api.request_message(device_id, MessageType.SHARE, share_id)

        def on_publish_share(self, device_id: str, share_id: int, data_urlfriendly: str):
            """Publish Share
            The data should be encoded using a base64 url friendly function

            :param device_id: A Programmor compatible device id
            :type device_id: str
            :param share_id: Protobuf model share id
            :type device_id: int
            :param data_urlfriendly: Protobuf share data encoded in base64 urlfriendly
            :type data_urlfriendly: str
            """
            data = base64.b64decode(data_urlfriendly)
            self.api.publish_message(device_id, MessageType.SHARE, share_id, data)

        def on_set_scheduled_share(self, device_id: str, share_id: int, interval: int):
            """Set Scheduled Share Message

            :param device_id: A Programmor compatible device id
            :type device_id: str
            :param share_id: Protobuf model share id
            :type device_id: int
            :param interval: Scheduled interval to request share in milliseconds
            :type interval: int
            """
            self.api.set_scheduled_message(device_id, MessageType.SHARE, share_id, interval)

        def on_clear_scheduled_share(self, device_id: str, share_id: int):
            """Clear Scheduled Share Message

            :param device_id: A Programmor compatible device id
            :type device_id: str
            :param share_id: Protobuf model share id
            :type device_id: str
            """
            self.api.clear_scheduled_message(device_id, MessageType.SHARE, share_id)

    """SocketIO Endpoint; This is a singleton
    """

    def __init__(self, app: Flask, api: API) -> None:
        super().__init__(app, api)
        self.socket: SocketIO = SocketIO(app, async_mode="gevent", cors_allowed_origins="*")
        self.ns = self.ApiNamespace('/api')
        self.ns.api = api
        self.ns.api.register_callback(lambda data: self.emit_data(data))
        self.socket.on_namespace(self.ns)

    def emit_data(self, response: ResponseType):
        """Emit Data
        """
        self.ns.emit('message_data', response, namespace='/api')

    def start(self) -> None:
        """Starts both the Flask, and the Socket app
        """
        self.socket.run(self.app)

    def stop(self) -> None:
        """Stops the application
        """
        self.socket.stop()
