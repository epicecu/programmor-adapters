import threading
from typing import Any, List, Callable
from shared.endpoint import Endpoint
from shared.api import API
from shared.types import MessageType, ResponseType

import asyncio
import uvicorn
import json
import base64
import queue
from starlette.applications import Starlette
from starlette.endpoints import WebSocketEndpoint
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocket
from starlette.middleware import Middleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

# Logging
import logging

import uvicorn.config
logger = logging.getLogger(__name__)


class SocketEndpoint(Endpoint):

    """Socket Endpoint
    Provides a Socket API endpoint for applications to interface with Programmor
    compatible devices.
    """

    encoding = "text"

    class ApiNamespace(WebSocketEndpoint):
        api: API
        ws_connections: List[WebSocket]
        emit: Callable

        async def get_devices(self, _):
            """Get Devices
            """
            await self.emit('devices', self.api.get_devices())

        async def get_devices_detailed(self, _):
            """Get Devices Detailed
            """
            await self.emit('devices_detailed', self.api.get_devices_detailed())

        async def check_status(self, device_id: str):
            """Check Status

            :param device_id: A Programmor compatible device id
            :type device_id: str
            """
            await self.emit('status', self.api.check_device(device_id))

        async def connect_device(self, device_id: str):
            """Connect Devices

            :param device_id: A Programmor compatible device id
            :type device_id: str
            """
            if self.api.connect_device(device_id):
                await self.emit('connected', device_id)
            else:
                await self.emit('connected_failed', device_id)

        async def disconnect_device(self, device_id: str):
            """Disconnect Device

            :param device_id: A Programmor compatible device id
            :type device_id: str
            """
            if self.api.disconnect_device(device_id):
                await self.emit('disconnected', device_id)
            else:
                await self.emit('disconnected_failed', device_id)

        def request_common(self, device_id: str, share_id: int):
            """Request Common Message

            :param device_id: A Programmor compatible device id
            :type device_id: str
            :param share_id: Protobuf model share id
            :type device_id: str
            """
            self.api.request_message(device_id, MessageType.COMMON, share_id)

        def publish_common(self, device_id: str, share_id: int, data_urlfriendly: str):
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

        def set_scheduled_common(self, device_id: str, share_id: int, interval: int):
            """Set Scheduled Common Message

            :param device_id: A Programmor compatible device id
            :type device_id: str
            :param share_id: Protobuf model share id
            :type device_id: int
            :param interval: Scheduled interval to request share in milliseconds
            :type interval: int
            """
            self.api.set_scheduled_message(device_id, MessageType.COMMON, share_id, interval)

        def clear_scheduled_common(self, device_id: str, share_id: int):
            """Clear Scheduled Common Message

            :param device_id: A Programmor compatible device id
            :type device_id: str
            :param share_id: Protobuf model share id
            :type device_id: str
            """
            self.api.clear_scheduled_message(device_id, MessageType.COMMON, share_id)

        def request_share(self, device_id: str, share_id: int):
            """Request Share

            :param device_id: A Programmor compatible device id
            :type device_id: str
            :param share_id: Protobuf model share id
            :type device_id: str
            """
            self.api.request_message(device_id, MessageType.SHARE, share_id)

        def publish_share(self, device_id: str, share_id: int, data_urlfriendly: str):
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

        def set_scheduled_share(self, device_id: str, share_id: int, interval: int):
            """Set Scheduled Share Message

            :param device_id: A Programmor compatible device id
            :type device_id: str
            :param share_id: Protobuf model share id
            :type device_id: int
            :param interval: Scheduled interval to request share in milliseconds
            :type interval: int
            """
            self.api.set_scheduled_message(device_id, MessageType.SHARE, share_id, interval)

        def clear_scheduled_share(self, device_id: str, share_id: int):
            """Clear Scheduled Share Message

            :param device_id: A Programmor compatible device id
            :type device_id: str
            :param share_id: Protobuf model share id
            :type device_id: str
            """
            self.api.clear_scheduled_message(device_id, MessageType.SHARE, share_id)

        async def on_connect(self, websocket):
            logger.info(f'Websocket: Connected {websocket.url}')
            self.event_loop = asyncio.get_event_loop()
            self.ws_connections.append(websocket)
            await websocket.accept()

        async def on_disconnect(self, websocket, close_code):
            logger.info(f'Websocket: Disconnected {websocket.url}')
            self.api.disconnect_all_devices()
            self.ws_connections.remove(websocket)

        async def on_receive(self, websocket, data):
            message = json.loads(data)
            print('on_receive')
            print(message)
            eventName: str = message['event']
            args: List[Any] = message['args']
            if hasattr(self, eventName):
                f = getattr(self, eventName)
                if callable(f):
                    try:
                        if asyncio.iscoroutinefunction(f):
                            send_back = await f(*args)
                        else:
                            send_back = f(*args)
                        if send_back:
                            self.emit(send_back)
                    except Exception as e:
                        logger.debug('on_receive: Failed to parse route and args')
                        logger.debug(data)
                        logger.debug(e)

    """Socket Endpoint; This is a singleton
    """
    def __init__(self, api: API, port: int) -> None:
        Endpoint.__init__(self, api, port)
        # WebSocketEndpoint.__init__(self)
        middleware = [
            Middleware(
                TrustedHostMiddleware,
                allowed_hosts=['*'],
            ),
        ]
        routes = [WebSocketRoute('/', self.ApiNamespace)]
        self.ws_connections: List[WebSocket] = []
        self.ApiNamespace.ws_connections = self.ws_connections
        self.ApiNamespace.api = api
        self.ApiNamespace.emit = self.emit
        api.register_callback(lambda data: self.emit_data(data))
        self.app = Starlette(routes=routes, middleware=middleware, on_startup=[self.start_thread])
        self.message_queue = queue.Queue()
        self.stop_event = threading.Event()
        logger.debug('Websocket Endpoint Initialised')

    def start_thread(self):
        self.event_loop = asyncio.get_event_loop()
        self.sender_thread = threading.Thread(target=self.send_messages, args=(None, self.event_loop))
        self.sender_thread.start()

    def send_messages(self, _, event_loop):
        while not self.stop_event.is_set():
            try:
                # Get message from queue with timeout to check for stop event
                message = self.message_queue.get(timeout=1)
                asyncio.run_coroutine_threadsafe(self.emit('message_data', message), event_loop)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Exception in send_messages thread: {e}")

    def emit_data(self, response: ResponseType) -> None:
        """Emit Data
        """
        self.message_queue.put(response)

    async def emit(self, eventName: str, arg):
        message = {'event': eventName, 'args': [arg]}
        message_string = json.dumps(message)
        for ws in self.ws_connections:
            await ws.send_text(message_string)

    def start(self) -> None:
        """Starts the endpoint
        """
        config = uvicorn.Config(self.app, host="0.0.0.0", port=self.port, reload=False, log_level="info", workers=1, limit_concurrency=1, limit_max_requests=1)
        server = uvicorn.Server(config)

        orig_log_started_message = server._log_started_message

        def server_started(server):
            for server in server.servers:
                for socket in server.sockets:
                    _, port = socket.getsockname()
                    logger.info(f'port:{port}')

        def patch_log_started_message(listeners):
            orig_log_started_message(listeners)
            server_started(server)

        server._log_started_message = patch_log_started_message
        logger.debug('Starting socket endpoint')
        server.run()

    def stop(self) -> None:
        """Stops the endpoint
        """
        self.stop_event.set()
        for ws in self.ws_connections:
            ws.close()
