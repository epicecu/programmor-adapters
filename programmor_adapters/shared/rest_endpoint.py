from shared.endpoint import Endpoint
from shared.api import API
from flask import Flask, jsonify
from flask_classful import FlaskView
import base64

# Logging
import logging

from shared.types import MessageType
logger = logging.getLogger(__name__)


class RestEndpoint(Endpoint):

    """REST Endpoint
    Provides a REST API endpoint for applications to interface with Programmor
    compatible devices.
    """

    class ApiView(FlaskView):

        """ API Reference
        """
        api: API

        def index(self):
            """Index

            GET: /api/
            """
            return jsonify({'Programmor-Adapter': 'USB'})

        def get_devices(self):
            """Get Devices

            GET: /api/get_devices/
            """
            return jsonify({'devices': self.api.get_devices()})

        def check_status(self, device_id: str):
            """Check Status

            GET: /api/check_status

            :param device_id: A Programmor compatible device id
            :type device_id: str
            """
            return jsonify({'status': self.api.check_device(device_id)})

        def connect_device(self, device_id: str):
            """Connect Devices

            GET: /api/connect_device/<device_id>/

            :param device_id: A Programmor compatible device id
            :type device_id: str
            """
            return jsonify({'connected': self.api.connect_device(device_id)})

        def disconnect_device(self, device_id: str):
            """Disconnect Device

            GET: /api/disconnect_device/<device_id>/

            :param device_id: A Programmor compatible device id
            :type device_id: str
            """
            return jsonify({'disconnected': self.api.disconnect_device(device_id)})

        def request_share(self, device_id: str, share_id: int):
            """Request Share

            GET: /api/request_share/<device_id>/<share_id>/

            :param device_id: A Programmor compatible device id
            :type device_id: str
            :param share_id: Protobuf model share id
            :type device_id: str
            """
            data = self.api.request_message_sync(device_id, MessageType.SHARE, share_id, 1)
            encoded = base64.urlsafe_b64encode(data)
            data_urlfriendly = encoded.rstrip("=".encode())
            return jsonify({'data': data_urlfriendly})

        def publish_share(self, device_id: str, share_id: int, data_urlfriendly: str):
            """Publish Share
            The data should be encoded using a base64 url friendly function

            GET: /api/publish_share/<device_id>/<share_id>/<data>/

            :param device_id: A Programmor compatible device id
            :type device_id: str
            :param share_id: Protobuf model share id
            :type device_id: int
            :param data_urlfriendly: Protobuf share data encoded in base64 urlfriendly
            :type data_urlfriendly: str
            """
            padding = 4 - (len(data_urlfriendly) % 4)
            data_urlfriendly_mod = data_urlfriendly + ("=" * padding)
            data = base64.urlsafe_b64decode(data_urlfriendly_mod)
            self.api.publish_message(device_id, MessageType.SHARE, share_id, data)
            return jsonify({'None': None})

        def set_scheduled_message_common(self, device_id: str, share_id: int, interval: int):
            """Set Scheduled Message

            GET: /api/set_scheduled_message_common/<device_id>/<common_id>/<interval>/

            :param device_id: A Programmor compatible device id
            :type device_id: str
            :param share_id: Protobuf model share id
            :type device_id: int
            :param interval: Scheduled interval to request share in milliseconds
            :type interval: int
            """
            self.api.set_scheduled_message(device_id, MessageType.COMMON, share_id, interval)
            return jsonify({'None': None})

        def set_scheduled_message_share(self, device_id: str, share_id: int, interval: int):
            """Set Scheduled Message

            GET: /api/set_scheduled_message_share/<device_id>/<share_id>/<interval>/

            :param device_id: A Programmor compatible device id
            :type device_id: str
            :param share_id: Protobuf model share id
            :type device_id: int
            :param interval: Scheduled interval to request share in milliseconds
            :type interval: int
            """
            self.api.set_scheduled_message(device_id, MessageType.SHARE, share_id, interval)
            return jsonify({'None': None})

        def clear_scheduled_message_common(self, device_id: str, share_id: int):
            """Clear Scheduled Message

            GET: /api/clear_scheduled_message_common/<device_id>/<common_id>/

            :param device_id: A Programmor compatible device id
            :type device_id: str
            :param share_id: Protobuf model share id
            :type device_id: str
            """
            self.api.clear_scheduled_message(device_id, MessageType.COMMON, share_id)
            return jsonify({'None': None})

        def clear_scheduled_message_share(self, device_id: str, share_id: int):
            """Clear Scheduled Message

            GET: /api/clear_scheduled_message_share/<device_id>/<share_id>/

            :param device_id: A Programmor compatible device id
            :type device_id: str
            :param share_id: Protobuf model share id
            :type device_id: str
            """
            self.api.clear_scheduled_message(device_id, MessageType.SHARE, share_id)
            return jsonify({'None': None})

    def __init__(self, app: Flask, api: API, port: int) -> None:
        """REST Endpoint
        """
        super().__init__(app, api, port)
        self.ApiView.api = api
        self.ApiView.register(self.app)

    def start(self) -> None:
        """Starts the Flask app
        """
        self.app.run(host="0.0.0.0", port=self.port)

    def stop(self) -> None:
        """Stops the application
        """
        pass
