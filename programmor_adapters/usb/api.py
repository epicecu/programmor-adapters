from usb.usb import USB
from typing import List, Dict, Any, Protocol
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

class Transaction(Protocol):
    """API Tranactions with the device
    """
    device_path: str
    request_message_token: int
    response_message_token: int


class API():
    """This is the API implementation of the USB communication method. The API class will
    package provided data into a transaction message and then rely on the USB implementation
    to package the data into Frames.
    """

    def __init__(self) -> None:
        """Constructor method
        """
        self.connections: Dict[str, USB] = dict()

    def get_devices(self) -> List[str]:
        """Returns a list of Programmor compatiable device paths.

        :return: A list of device paths
        :rtype: str
        """
        usb = USB()
        return usb.get_device_paths()

    def get_device(self, path: str) -> USB:
        """Gets a connected USB device by path, returns None if the device is not connected.

        :param path: A USB device path
        :type path: str
        """
        return self.connections.get(path, None)

    def check_device(self, path: str) -> bool:
        """Checks if a device is avaliable and connected.

        :param path: A USB device path
        :type path: str
        """
        return self.get_device(path) != None 

    def connect_device(self, path: str) -> bool:
        """Connects to a Programmor compatiable USB device. 

        :param path: A USB device path
        :type path: str
        """
        if self.check_device(path):
            return False
        # Create USB Connection and connect
        self.connections[path] = USB()
        self.connections[path].set_received_message_callback(lambda data: self._on_receive(path, data))
        self.connections[path].start()
        if not self.connections[path].connect(path):
            self.connections[path].stop()
            return False
        return True

    def disconnect_device(self, path: str) -> None:
        """Disconnects a USB device.

        :param path: A USB device path
        :type path: str
        """
        if not self.check_device(path):
            return
        # Close connection and delete
        self.connections[path].close()
        self.connections[path].stop()
        del self.connections[path]

    def request_share(self, path: str, shareId: int) -> None:
        """Request a Share from the USB device

        :param path: A USB device path
        :type path: str
        :param shareId: A share id
        :type shareId: int
        """
        device = self.get_device(path)
        if device == None:
            return
        # Request share from device
        request_message_bytes = self._request_message_as_bytes(shareId)
        device.send_message(request_message_bytes)

    async def request_share_async(self, path: str, shareId: int, timeout_s: float = 1) -> bytes:
        """Request a Share from the USB device and wait for a response within the timeout.

        :param path: A USB device path
        :type path: str
        :param shareId: A share id
        :type shareId: int
        :param timeout_s: Waiting timeout in seconds
        :type timeout_s: float 
        :return: A response share
        :rtype: bytes
        """
        device = self.get_device(path)
        if device == None:
            return bytes(0)
        # Request share from device
        request_message_bytes = self._request_message_as_bytes(shareId)
        response = transaction_pb2.TransactionMessage()
        try:
            response.ParseFromString(await device.send_then_receive_message(request_message_bytes, timeout_s))
        except BaseException:
            return bytes(0)
        return response.data

    def publish_share(self, path: str, shareId: int, data: bytes) -> None:
        """Publish a Share to the USB device

        :param path: A USB device path
        :type path: str
        :param shareId: A share id
        :type shareId: int
        :param data: The share to publish to the device
        :type data: bytes
        """
        device = self.get_device(path)
        if device == None:
            return
        # Publish share to device
        publish_message_bytes = self._publish_message_as_bytes(shareId, data)
        device.send_message(publish_message_bytes)

    # Private Request Message
    def _request_message(self, shareId: int) -> transaction_pb2.TransactionMessage:
        """A Request Message

        :param shareId: A share id
        :type shareId: int
        :return: A transaction message
        :rtype: transaction_pb2.TransactionMessage
        """
        requestMessage = transaction_pb2.TransactionMessage()
        requestMessage.token = uuid4().int >> 96
        requestMessage.action = transaction_pb2.TransactionMessage.REQUEST
        requestMessage.shareId = shareId
        requestMessage.dataLength = 1
        requestMessage.data = bytes(DATA_MAX_SIZE)
        return requestMessage

    def _request_message_as_bytes(self, shareId: int) -> bytes:
        """A Request Message as bytes

        :param shareId: A share id
        :type shareId: int
        :return: A transaction message as bytes
        :rtype: bytes
        """
        message: transaction_pb2.TransactionMessage = self._request_message(shareId)
        # TODO: Store reference to message
        return message.SerializeToString()

    def _publish_message(self, shareId: int, data: bytes) -> transaction_pb2.TransactionMessage:
        """A Publish Message

        :param shareId: A share id
        :type shareId: int
        :return: A transaction message
        :rtype: transaction_pb2.TransactionMessage
        """
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

    def _publish_message_as_bytes(self, shareId: int, data: bytes) -> bytes:
        """A Publish Message as bytes

        :param shareId: A share id
        :type shareId: int
        :return: A transaction message as bytes
        :rtype: bytes
        """
        message: transaction_pb2.TransactionMessage = self._publish_message(shareId, data)
        # TODO: Store reference to message
        return message.SerializeToString()

    def _on_receive(self, path: str, data: bytes) -> None:
        """A Request Message as bytes

        :param path: A USB device path
        :type path: str
        :param data: Return data from the device
        :type data: bytes
        """
        response = transaction_pb2.TransactionMessage()
        try:
            response.ParseFromString(data)
        except BaseException:
            return
        
        #TODO Add response to the reponse pool or callback function?