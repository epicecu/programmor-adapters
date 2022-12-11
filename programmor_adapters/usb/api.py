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
        return USB.get_device_paths()

    # Connect to a USB device
    def connect_device(self, path: str) -> bool:
        if path in self.connections:
            return False
        # Create USB Connection and connect
        self.connections[path] = USB()
        self.connections[path].set_received_message_callback(lambda data: self._on_receive(path, data))
        return self.connections[path].connect(path)

    # Disconnect from a USB device
    def disconnect_device(self, path: str) -> None:
        if path not in self.connections:
            return
        # Close connection and delete
        self.connections[path].close()
        del self.connections[path]

    # Request shareid
    def request_share(self, path: str, shareId: int) -> bytes:
        if path not in self.connections:
            return bytes()
        # Request share from device
        data = self._request_message_as_bytes(shareId)
        self.connections[path].send_message(data)
        
    # Publish shareid
    def publish_share(self, path: str, shareId: int, data: bytes) -> None:
        if path not in self.connections:
            return
        # Publish share to device
        pass

    # Private Request Message
    def _request_message(self, shareId: int) -> Any:
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
    def _publish_message(self, shareId: int, data: bytes) -> Any:
        publishMessage = transaction_pb2.TransactionMessage()
        publishMessage.token = uuid4().int >> 96
        publishMessage.action = transaction_pb2.TransactionMessage.PUBLISH
        publishMessage.shareId = shareId
        if data is None:
            return bytes(0)
        # Check that the data is DATA_MAX_SIZE bytes or less
        if len(data) > DATA_MAX_SIZE:
            return bytes(0)
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