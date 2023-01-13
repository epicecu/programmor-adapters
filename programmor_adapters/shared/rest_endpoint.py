from shared.endpoint import Endpoint
from shared.api import API
from flask import Flask, jsonify
from flask_classful import FlaskView


class RestEndpoint(Endpoint):

    class ApiView(FlaskView):
        """domain:port/api/ View
        Helper library: http://flask-classful.teracy.org/
        """
        def index(self):
            return jsonify({'test': 'test1'})

    """REST Endpoint
    """
    def __init__(self, app: Flask, api: API) -> None:
        super().__init__(app, api)
        self.ApiView.register(self.app)

    def start(self) -> None:
        """Starts the Flask app
        """
        self.app.run()

    def stop(self) -> None:
        """Stops the application
        """
        pass
