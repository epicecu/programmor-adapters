from usb.usb import USB
from typing import List, Dict, Any
from uuid import uuid4
from datetime import datetime

# Transaction Protobuf File
import usb.proto.transaction_pb2 as transaction_pb2

# Logging
import logging
logger = logging.getLogger(__name__)

# Defaults
DATA_MAX_SIZE = 80
TRANSACTION_MESSAGE_SIZE = 99



class API():

    # API Init 
    def __init__(self) -> None:
        self.connections: Dict[str, USB] = dict()

    # Get a list of connected Programmor compatiable device ids
    def get_devices(self) -> List[str]:
        usb = USB()
        return usb.get_device_paths()

    def get_device(self, path: str) -> USB:
        # Check if device is in the list of connections
        return self.connections.get(path, None)

    def check_device(self, path: str) -> bool:
        return self.get_device(path) == None 

    # Connect to a USB device
    def connect_device(self, path: str) -> bool:
        if self.check_device(path):
            return False
        # Create USB Connection and connect
        self.connections[path] = USB()
        self.connections[path].set_received_message_callback(lambda data: self._on_receive(path, data))
        return self.connections[path].connect(path)

    # Disconnect from a USB device
    def disconnect_device(self, path: str) -> None:
        if not self.check_device(path):
            return
        # Close connection and delete
        self.connections[path].close()
        del self.connections[path]

    # Request shareid
    def request_share(self, path: str, shareId: int) -> bytes:
        device = self.get_device(path)
        if device == None:
            return bytes()
        # Request share from device
        request_message_bytes = self._request_message_as_bytes(shareId)
        device.send_message(request_message_bytes)
        
    # Publish shareid
    def publish_share(self, path: str, shareId: int, data: bytes) -> None:
        device = self.get_device(path)
        if device == None:
            return
        # Publish share to device
        publish_message_bytes = self._publish_message_as_bytes(shareId, data)
        device.send_message(publish_message_bytes)

    # Private Request Message
    def _request_message(self, shareId: int) -> transaction_pb2.TransactionMessage:
        requestMessage = transaction_pb2.TransactionMessage()
        requestMessage.token = uuid4().int >> 96
        requestMessage.action = transaction_pb2.TransactionMessage.REQUEST
        requestMessage.shareId = shareId
        requestMessage.dataLength = 1
        requestMessage.data = bytes(DATA_MAX_SIZE)
        return requestMessage

    # Private Request Message as Bytes
    def _request_message_as_bytes(self, shareId: int) -> bytes:
        return self._request_message(shareId).SerializeToString()

    # Private Publish Message
    def _publish_message(self, shareId: int, data: bytes) -> transaction_pb2.TransactionMessage:
        publishMessage = transaction_pb2.TransactionMessage()
        publishMessage.token = uuid4().int >> 96
        publishMessage.action = transaction_pb2.TransactionMessage.PUBLISH
        publishMessage.shareId = shareId
        if data is None:
            data = bytes(0)
        # Check that the data is DATA_MAX_SIZE bytes or less
        if len(data) > DATA_MAX_SIZE:
            data = bytes(0)
        publishMessage.dataLength = len(data)
        publishMessage.data = data + bytes(DATA_MAX_SIZE - len(data))
        # print(publishMessage)
        # print(publishMessage.data.hex(" "))
        return publishMessage
    
    # Private Publish Message as Bytes
    def _publish_message_as_bytes(self, shareId: int, data: bytes) -> bytes:
        return self._publish_message(shareId, data).SerializeToString()

    def _on_receive(self, path: str, data: bytes) -> None:
        pass