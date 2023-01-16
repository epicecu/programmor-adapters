from shared.endpoint import Endpoint
from shared.api import API
from flask import Flask, jsonify
from flask_classful import FlaskView

# Logging
import logging
logger = logging.getLogger(__name__)


class RestEndpoint(Endpoint):

    class ApiView(FlaskView):
        
        """ API Reference
        """
        api: API
        
        """domain:port/api/ View
        Helper library: http://flask-classful.teracy.org/
        """
        def index(self):
            return jsonify({'test': 'test1'})

        def get_devices(self):
            return jsonify({'devices': self.api.get_devices()})

        def check_status(self, device_id: str):
            return jsonify({'status': self.api.check_device(device_id)})

        def connect_device(self, device_id: str):
            return jsonify({'connected': self.api.connect_device(device_id)})

        def disconnect_device(self, device_id: str):
            return jsonify({'disconnected': self.api.disconnect_device(device_id)})

        def request_share(self, device_id: str, share_id: int):
            return jsonify({'data': self.api.request_share_async(device_id, share_id, 1)})

        def publish_share(self, device_id: str, share_id:int, data: bytes):
            return jsonify({'None': self.api.publish_share(device_id, share_id, data)})

        def set_scheduled_message(self, device_id: str, share_id: int, interval: int):
            return jsonify({'None': self.api.set_scheduled_message(device_id, share_id, interval)})

        def clear_scheduled_message(self, device_id: str, share_id: int):
            return jsonify({'None': self.api.clear_scheduled_message(device_id, share_id)})


    """REST Endpoint
    """
    def __init__(self, app: Flask, api: API) -> None:
        super().__init__(app, api)
        self.ApiView.api = api
        self.ApiView.register(self.app)

    def start(self) -> None:
        """Starts the Flask app
        """
        self.app.run()

    def stop(self) -> None:
        """Stops the application
        """
        pass
