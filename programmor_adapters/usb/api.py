from usb.usb import USB
from typing import List, Dict, Any, Protocol, Callable
from uuid import uuid4
from datetime import datetime
from tinydb import TinyDB, Query

# Transaction Protobuf File
import usb.proto.transaction_pb2 as transaction_pb2

# Logging
import logging
logger = logging.getLogger(__name__)

# Defaults
DATA_MAX_SIZE = 80
TRANSACTION_MESSAGE_SIZE = 99

"""Developer Notes:
Tiny DB Reference - https://tinydb.readthedocs.io/en/latest/getting-started.html
Writing docs - https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html 

"""


class Transaction(Protocol):
    """API Tranactions with the device
    """
    id: int
    device_path: str
    sent_at: datetime
    received_at: datetime
    created_at: datetime = datetime.now()


class API():
    """This is the API implementation of the USB communication method. The API class will
    package provided data into a transaction message and then rely on the USB implementation
    to package the data into Frames.
    """

    def __init__(self, database_storage_location: str = "./usb-db") -> None:
        """Constructor method
        """
        self.connections: Dict[str, USB] = dict()
        self.fns: List[str, Callable[[bytes], None]] = dict()
        self.transactions: List[Transaction] = list()
        self.db = TinyDB(f"{database_storage_location}.json")

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
        request_message = self._request_message(shareId)
        # Generate transaction record
        record = Transaction()
        record.id = request_message.token
        record.device_path = path
        record.sent_at = datetime.now()
        self.transactions.append(record)
        # Convert message to bytes
        request_message_bytes = request_message.SerializeToString()
        # Send data
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
        request_message_bytes = self._request_message(shareId).SerializeToString()
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
        # Check & Fetch device
        device = self.get_device(path)
        if device == None:
            return
        # Generate publish message
        publish_message = self._publish_message(shareId, data)
        # Generate transaction record
        record = Transaction()
        record.id = publish_message.token
        record.device_path = path
        record.sent_at = datetime.now()
        self.transactions.append(record)
        # Convert message to bytes
        publish_message_bytes = publish_message.SerializeToString()
        # Send data
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
        # Confirm the received data is in response of a transaction
        filtered_transactions = filter(lambda record: record.id == response.token, self.transactions)
        if len(filtered_transactions) == 0:
            logger.debug("Could not match received data to a transaction record")
            #TODO Potentially handle other alt receive modes 
            return
        # Update transaction, then remove
        record: Transaction = filtered_transactions[0]
        record.received_at = datetime.now()
        logger.info(record)
        self.transactions.remove(record)
        # Save data to database
        self.db.insert({"id": record.id, "action": response.action, "shareId": response.shareId ,"data": response.data, "requestedAt": record.sent_at, "receivedAt": record.received_at})
        # Pass data to callback functions
        self.callback(response.data)

    def register_callback(self, fn: Callable[[bytes], None]) -> None:
        """Register a receive callback function.

        :param fn: Callback function
        :type fn: Callable function 
        """
        self.fns.append(fn)

    def clear_callback(self):
        """Clear all the callback functions
        """
        self.fns.clear()

    def callback(self, data: bytes) -> None:
        """Calls all registered callback functions.

        :param data: Return data from the device
        :type data: bytes
        """
        for fn in self.fns:
            try:
                # Pass data to callback function
                fn(data)
            except:
                logger.debug("Callback function failed to execute")
