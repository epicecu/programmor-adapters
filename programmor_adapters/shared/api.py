from shared.comm import Comm
from shared.datetime import diff_ms
from datetime import datetime
from time import sleep
from typing import List, Dict, Any, Protocol, Callable
from uuid import uuid4
from tinydb import TinyDB, Query
import copy
import threading

# Transaction Protobuf File
import shared.proto.transaction_pb2 as transaction_pb2

# Logging
import logging
logger = logging.getLogger(__name__)

# Defaults
DATA_MAX_SIZE = 80

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


class ScheduledMessage(Protocol):
    """Scheduled Message Object
    """
    device_path: str
    share_id: int
    interval_ms: int
    last_scheduled: datetime
    updated_at: datetime
    created_at: datetime = datetime.now()
    def tick(self):
        self.last_scheduled = datetime.now()
    def update_interval(self, interval_ms: int):
        self.interval_ms = interval_ms
        self.updated_at = datetime.now()


class API(threading.Thread):
    """API
    The API interface between the communications device and Programmor HMI. The API class will
    package provided data into a transaction message and then rely on the Comms implementation
    to package the data into Frames.
    """

    def __init__(self, comms_method: Comm,  database_storage_file: str = "./comm-db.json") -> None:
        """Constructor method
        """
        # Thread
        threading.Thread.__init__(self)
        self.stop_flag: bool = False
        # Process scheduled messages loop 
        self.scheduled: List[ScheduledMessage] = list()
        # API
        self.connections: Dict[str, Comm] = dict()
        self.fns: List[str, Callable[[Transaction, bytes], None]] = dict()
        self.transactions: List[Transaction] = list()
        self.db = TinyDB(f"{database_storage_file}")
        self.comm = comms_method

    def start(self) -> None:
        """Starts the thread
        """
        threading.Thread.start(self)
        logger.info("Starting Comms Thread")

    def stop(self) -> None:
        """Stops the thread
        """
        logger.info("Stopping Comms Thread")
        self.stop_flag = True

    def run(self) -> None:
        """Run method used by python threading
        """
        while True:
            # Stop thread
            if self.stop_flag:
                logger.info("Stopped API Thread")
                break

            # Process logic
            self._process_scheduled_messages(self)

            # Sleep the thread
            sleep(0.0001)  # 0.1ms

    def _process_scheduled_messages(self) -> None:
        """Process Scheduled Messages
        Loop through the schedules and determin if the process time 
        has elapsed the interval time.
        """
        for schedule in self.scheduled:
            if diff_ms(datetime.now(), schedule.last_scheduled) > schedule.interval_ms:
                self.request_share(schedule.device_path, schedule.share_id)
                schedule.tick()

    def set_scheduled_message(self, path: str, shareId: int, interval_ms: float = 100) -> None:
        """Set Schedule Message
        """
        # Check if schedule already exists
        schedule = next(filter(lambda schedule: schedule.share_id == shareId and schedule.device_path == path, self.scheduled), None)
        # Create or modify the schedule
        if schedule == None:
            # Create new schedule
            schedule = ScheduledMessage()
            self.scheduled.append(schedule)
        else:
            # Update the schedule
            schedule.update_interval(interval_ms)

    def clear_scheduled_message(self, path: str, shareId: int) -> None:
        """Clear Scheduled Message
        """
        schedule = next(filter(lambda schedule: schedule.share_id == shareId and schedule.device_path == path, self.scheduled), None)
        if schedule != None:
            self.scheduled.remove(schedule)

    def get_devices(self) -> List[str]:
        """Returns a list of Programmor compatible device paths.

        :return: A list of device paths
        :rtype: str
        """
        comm = self.comm() # This may be an anti pattern, fix latter
        return comm.get_devices()

    def get_device(self, path: str) -> Comm:
        """Gets a connected Comms device by path, returns None if the device is not connected.

        :param path: A Comms device path
        :type path: str
        """
        return self.connections.get(path, None)

    def check_device(self, path: str) -> bool:
        """Checks if a device is avaliable and connected.

        :param path: A Comms device path
        :type path: str
        """
        return self.get_device(path) != None 

    def connect_device(self, path: str) -> bool:
        """Connects to a Programmor compatible Comms device. 

        :param path: A Comms device path
        :type path: str
        """
        if self.check_device(path):
            return False
        # Create USB Connection and connect
        self.connections[path] = self.comm()
        self.connections[path].set_received_message_callback(lambda data: self._on_receive(path, data))
        self.connections[path].start()
        if not self.connections[path].connect(path):
            self.connections[path].stop()
            return False
        return True

    def disconnect_device(self, path: str) -> None:
        """Disconnects a Comms device.

        :param path: A Comms device path
        :type path: str
        """
        if not self.check_device(path):
            return
        # Close connection and delete
        self.connections[path].close()
        self.connections[path].stop()
        del self.connections[path]

    def request_share(self, path: str, shareId: int) -> None:
        """Request a Share from the Comms device

        :param path: A Comms device path
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
        """Request a Share from the Comms device and wait for a response within the timeout.

        :param path: A Comms device path
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
        """Publish a Share to the Comms device

        :param path: A Comms device path
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

    def get_shares(self, path:str, to_time: datetime, from_time: datetime, shareId: int) -> List[bytes]:
        """Get a range of shares from the database.

        :param path: A Comms device path
        :type path: str
        :param to_time: To datetime range
        :type to_time: datetime
        :param from_time: From datetime range
        :type datetime: datetime
        :param shareId: A share id
        :type shareId: int
        """
        item = Query()
        items = self.db.search(item.device == path and item.shareId == shareId and item.receivedAt >= to_time and item.receivedAt <= from_time )
        messages = list()
        for i in items:
            messages.append(i.data)
        return messages

    def _on_receive(self, path: str, data: bytes) -> None:
        """A Request Message as bytes

        :param path: A Comms device path
        :type path: str
        :param data: Return data from the device
        :type data: bytes
        """
        response = transaction_pb2.TransactionMessage()
        try:
            response.ParseFromString(data)
        except BaseException:
            return
        # Confirm the received data is in response to a transaction
        filtered_transactions = filter(lambda record: record.id == response.token and record.device_path == path, self.transactions)
        if len(filtered_transactions) == 0:
            logger.debug("Could not match received data to a transaction record")
            return
        # Update transaction, then remove
        metadata: Transaction = copy.copy(filtered_transactions[0])
        metadata.received_at = datetime.now()
        logger.info(metadata)
        self.transactions.remove(metadata) # Deepcopy, Remove for now, we may attempt to implement advance request/response handling later..
        # Save data to database
        self.db.insert({"id": metadata.id, "device": path, "action": response.action, "shareId": response.shareId ,"data": response.data, "requestedAt": metadata.sent_at, "receivedAt": metadata.received_at})
        # Pass data to callback functions
        self._callback(metadata, response.data)

    def register_callback(self, fn: Callable[[Transaction, bytes], None]) -> None:
        """Register a receive callback function.

        :param fn: Callback function
        :type fn: Callable function
        """
        self.fns.append(fn)

    def clear_callback(self):
        """Clear all the callback functions
        """
        self.fns.clear()

    def _callback(self, metadata: Transaction, data: bytes) -> None:
        """Calls all registered callback functions.

        :param data: Return data from the device
        :type data: bytes
        """
        for fn in self.fns:
            try:
                # Pass data to callback function
                fn(metadata, data)
            except:
                logger.debug("Callback function failed to execute")
