from shared.comm import Comm
from shared.datetime import diff_ms
from shared.types import MessageType, ResponseType
from datetime import datetime
from time import sleep
from typing import List, Dict, Callable
from uuid import uuid4
from tinydb import TinyDB, Query
import threading
import base64

# Transaction Protobuf File
from google.protobuf.json_format import MessageToJson
import shared.proto.transaction_pb2 as transaction_pb2

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


class ScheduledRequest():
    """Scheduled Request Message Object
    """
    device_id: str
    message_type: MessageType
    share_id: int
    interval_ms: int
    last_scheduled: datetime = datetime.now()
    updated_at: datetime
    created_at: datetime = datetime.now()

    def tick(self):
        self.last_scheduled = datetime.now()

    def update_interval(self, interval_ms: int):
        self.interval_ms = interval_ms
        self.updated_at = datetime.now()

    def __str__(self) -> str:
        return f"ScheduledRequest(device_id: {self.device_id} message_type: {self.message_type} share_id: {self.share_id} interval: {self.interval_ms})"


class RequestRecord():
    """API Transactions with the device
    """
    id: int
    device_id: str
    sent_at: datetime = datetime.now()
    received_at: datetime = None
    created_at: datetime = datetime.now()

    def __str__(self) -> str:
        if self.received_at is not None:
            return f"""RequestRecord(id: {self.id} device_id: {self.device_id} sent_at: {self.sent_at}
            received_at: {self.received_at} created_at: {self.created_at} duration: {self.received_at - self.sent_at})"""
        else:
            return f"RequestRecord(id: {self.id} device_id: {self.device_id} sent_at: {self.sent_at} created_at: {self.created_at})"


class API(threading.Thread):

    """API
    The API interface between the communications device and Programmor HMI. The API class will
    package provided data into a transaction message and then rely on the Comms implementation
    to package the data into Frames.
    """

    def __init__(self, comms_method: Comm,  database_storage_file: str = "./adapter-db.json") -> None:
        """Constructor method
        """
        # Thread
        threading.Thread.__init__(self)
        self.stop_flag: bool = False
        # Process scheduled messages loop
        self.scheduled: List[ScheduledRequest] = list()
        # API
        self.connections: Dict[str, Comm] = dict()
        self.fns: List[Callable[[ResponseType], None]] = list()
        self.transactions: List[RequestRecord] = list()
        self.db = TinyDB(f"{database_storage_file}")
        self.comm = comms_method

    def start(self) -> None:
        """Starts the thread
        """
        threading.Thread.start(self)
        logger.info("Starting Api Thread")

    def stop(self) -> None:
        """Stops the thread
        """
        logger.info("Stopping Api Thread")
        # Close all connections
        for _, con in self.connections.items():
            con.stop()
        # Stops the thread
        self.stop_flag = True

    def run(self) -> None:
        """Run method used by python threading
        """
        logger.info("API Thread Running...")
        while True:
            # Stop thread
            if self.stop_flag:
                logger.info("API Thread Stopped")
                break

            # Process logic
            self._process_scheduled_messages()

            # Sleep the thread
            sleep(0.0001)  # 0.1ms

    def _process_scheduled_messages(self) -> None:
        """Process Scheduled Messages
        Loop through the schedules and determine if the process time
        has elapsed the interval time.
        """
        for schedule in self.scheduled:
            if diff_ms(datetime.now(), schedule.last_scheduled) > schedule.interval_ms:
                self.request_message(schedule.device_id, schedule.message_type, schedule.share_id)
                logger.debug(f"Processing schedule {schedule.share_id} {schedule.interval_ms}")
                schedule.tick()

    def set_scheduled_message(self, device_id: str, message_type: MessageType, shareId: int, interval_ms: float = 100) -> None:
        """Set Schedule Message

        :param device_id: A Comms device id
        :type device_id: str
        :param shareId: A share id
        :type device_id: int
        :param interval_ms: The scheduled interval time
        :type device_id: float
        """
        # Check if schedule already exists
        schedule = next(filter(lambda schedule: schedule.share_id == shareId and schedule.device_id ==
                        device_id and schedule.message_type == message_type, self.scheduled), None)
        # Create or modify the schedule
        if schedule is None:
            # Create new schedule
            schedule = ScheduledRequest()
            schedule.device_id = device_id
            schedule.message_type = message_type
            schedule.share_id = shareId
            schedule.interval_ms = interval_ms
            self.scheduled.append(schedule)
            logger.info(f"Added schedule {shareId} {interval_ms}")
        else:
            # Update the schedule
            schedule.update_interval(interval_ms)
            logger.info(f"Updated schedule {shareId} {interval_ms}")

    def clear_scheduled_message(self, device_id: str, message_type: MessageType, shareId: int) -> None:
        """Clear Scheduled Message

        :param device_id: A Comms device id
        :type device_id: str
        :param shareId: A share id
        :type device_id: int
        """
        schedule = next(filter(lambda schedule: schedule.share_id == shareId and schedule.device_id ==
                        device_id and schedule.message_type == message_type, self.scheduled), None)
        if schedule is not None:
            self.scheduled.remove(schedule)
            logger.info(f"Removed schedule {shareId}")

    def clear_all_schedules(self, device_id: str) -> None:
        """Clear All Schedules
        Clears all schedules for a given device.

        :param device_id: A Comms device id
        :type device_id: str
        """
        schedules = filter(lambda schedule: schedule.device_id == device_id, self.scheduled)
        if schedules is not None:
            for schedule in schedules:
                self.scheduled.remove(schedule)

    def get_devices(self) -> List[str]:
        """Returns a list of Programmor compatible device ids.

        :return: A list of device ids
        :rtype: str
        """
        comm = self.comm()  # This may be an anti pattern, fix latter
        return comm.get_devices()

    def get_devices_detailed(self) -> List[object]:
        """Get Devices Detailed
        """
        device_ids = self.get_devices()
        devices = list()
        # Request the common 1 message for each device
        for device_id in device_ids:
            self.connect_device(device_id)
            common = transaction_pb2.Common1()
            try:
                common.ParseFromString(self.request_message_sync(device_id, MessageType.COMMON, 1))
            except BaseException as e:
                print(f"Failed to parse common message: {e}")
                continue
            device = {
                "deviceId": device_id,
                "common1": MessageToJson(common)
            }
            devices.append(device)
            self.disconnect_device(device_id)
        return devices

    def get_device(self, device_id: str) -> Comm:
        """Gets a connected Comms device by id, returns None if the device is not connected.

        :param device_id: A Comms device id
        :type device_id: str
        :return: A Comm object
        :rtype: Comm
        """
        return self.connections.get(device_id, None)

    def check_device(self, device_id: str) -> bool:
        """Checks if a device is available and connected.

        :param device_id: A Comms device id
        :type device_id: str
        :return: Status
        :rtype: bool
        """
        if self.get_device(device_id) is not None:
            return True
        else:
            return False

    def connect_device(self, device_id: str) -> bool:
        """Connects to a Programmor compatible Comms device.

        :param device_id: A Comm's device id
        :type device_id: str
        :return: Status
        :rtype: bool
        """
        if self.check_device(device_id):
            print(self.connections)
            logger.info(f"Device already connected {device_id}")
            return False
        # Create USB Connection and connect
        logger.debug("Creating a new comms obj")
        self.connections[device_id] = self.comm()
        self.connections[device_id].set_received_message_callback(lambda data: self._on_receive(device_id, data))
        self.connections[device_id].get_devices()
        self.connections[device_id].start()
        if not self.connections[device_id].connect(device_id):
            logger.debug(f"Failed to connect to device {device_id}")
            self.connections[device_id].stop()
            del self.connections[device_id]
            return False
        logger.info(f"Connected to device {device_id}")
        return True

    def disconnect_device(self, device_id: str) -> bool:
        """Disconnects a Comms device.

        :param device_id: A Comm's device id
        :type device_id: str
        :return: Status
        :rtype: bool
        """
        if not self.check_device(device_id):
            return
        # Close connection and delete
        try:
            # Clear all schedules with this device
            self.clear_all_schedules(device_id)
            # Close
            self.connections[device_id].close()
            self.connections[device_id].stop()
            del self.connections[device_id]
            return True
        except Exception as e:
            logger.error(e)
            return False

    def disconnect_all_devices(self) -> None:
        """Disconnects all devices from the adapter
        """
        list_of_devices: List[str] = list()
        for device_id, _ in self.connections.items():
            list_of_devices.append(device_id)
        # Stores a list of ids to Prevent the iteration failing for deletion of the connection
        for device_id in list_of_devices:
            self.disconnect_device(device_id)

    def request_message(self, device_id: str, message_type: MessageType, shareId: int) -> None:
        """Request a Share from the Comms device

        :param device_id: A Comm's device id
        :type device_id: str
        :param shareId: A share id
        :type shareId: int
        """
        device = self.get_device(device_id)
        if device is None:
            return
        # Request share from device
        request_message = self._request_message(message_type, shareId)
        # Generate transaction record
        record = RequestRecord()
        record.id = request_message.token
        record.device_id = device_id
        record.sent_at = datetime.now()
        self.transactions.append(record)
        # Convert message to bytes
        request_message_bytes = request_message.SerializeToString()
        # Send data
        device.send_message(request_message_bytes)

    def request_message_sync(self, device_id: str, message_type: MessageType, shareId: int, timeout_s: float = 1) -> bytes:
        """Request a Share from the Comms device and wait for a response within the timeout.

        :param device_id: A Comms device id
        :type device_id: str
        :param shareId: A share id
        :type shareId: int
        :param timeout_s: Waiting timeout in seconds
        :type timeout_s: float
        :return: A response share
        :rtype: bytes
        """
        device = self.get_device(device_id)
        if device is None:
            return bytes(0)
        # Request share from device
        request_message_bytes = self._request_message(message_type, shareId).SerializeToString()
        response = transaction_pb2.TransactionMessage()
        try:
            response.ParseFromString(bytes(device.send_then_receive_message(request_message_bytes, timeout_s)[0:TRANSACTION_MESSAGE_SIZE]))
        except BaseException:
            return bytes(0)
        return response.data[0:response.dataLength]

    def publish_message(self, device_id: str, message_type: MessageType, shareId: int, data: bytes) -> None:
        """Publish a Share to the Comms device

        :param device_id: A Comms device id
        :type device_id: str
        :param shareId: A share id
        :type shareId: int
        :param data: The share to publish to the device
        :type data: bytes
        """
        # Check & Fetch device
        device = self.get_device(device_id)
        if device is None:
            return
        # Generate publish message
        publish_message = self._publish_message(message_type, shareId, data)
        # Generate transaction record
        record = RequestRecord()
        record.id = publish_message.token
        record.device_id = device_id
        record.sent_at = datetime.now()
        self.transactions.append(record)
        logger.info(record)
        # Convert message to bytes
        publish_message_bytes = publish_message.SerializeToString()
        # Send data
        device.send_message(publish_message_bytes)

    # Private Request Message
    def _request_message(self, message_type: MessageType, shareId: int) -> transaction_pb2.TransactionMessage:
        """A Request Message

        :param shareId: A share id
        :type shareId: int
        :return: A transaction message
        :rtype: transaction_pb2.TransactionMessage
        """
        requestMessage = transaction_pb2.TransactionMessage()
        requestMessage.token = uuid4().int >> 96
        if message_type == MessageType.COMMON:
            requestMessage.action = transaction_pb2.TransactionMessage.COMMON_REQUEST
        else:
            requestMessage.action = transaction_pb2.TransactionMessage.SHARE_REQUEST
        requestMessage.shareId = shareId
        requestMessage.dataLength = 1
        requestMessage.data = bytes(DATA_MAX_SIZE)
        return requestMessage

    def _publish_message(self, message_type: MessageType, shareId: int, data: bytes) -> transaction_pb2.TransactionMessage:
        """A Publish Message

        :param shareId: A share id
        :type shareId: int
        :return: A transaction message
        :rtype: transaction_pb2.TransactionMessage
        """
        publishMessage = transaction_pb2.TransactionMessage()
        publishMessage.token = uuid4().int >> 96
        if message_type == MessageType.COMMON:
            publishMessage.action = transaction_pb2.TransactionMessage.COMMON_PUBLISH
        else:
            publishMessage.action = transaction_pb2.TransactionMessage.SHARE_PUBLISH
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

    def get_shares(self, device_id: str, to_time: datetime, from_time: datetime, shareId: int) -> List[bytes]:
        """Get a range of shares from the database.

        :param device_id: A Comm's device id
        :type device_id: str
        :param to_time: To datetime range
        :type to_time: datetime
        :param from_time: From datetime range
        :type datetime: datetime
        :param shareId: A share id
        :type shareId: int
        """
        item = Query()
        items = self.db.search(item.device == device_id and item.shareId == shareId and item.receivedAt >= to_time and item.receivedAt <= from_time)
        messages = list()
        for i in items:
            messages.append(i.data)
        return messages

    def _on_receive(self, device_id: str, data: bytes) -> None:
        """A Request Message as bytes

        :param device_id: A Comm's device id
        :type device_id: str
        :param data: Return data from the device
        :type data: bytes
        """
        response = transaction_pb2.TransactionMessage()
        try:
            response.ParseFromString(bytes(data[0:TRANSACTION_MESSAGE_SIZE]))
        except BaseException:
            return
        # Confirm the received data is in response to a transaction
        filtered_transactions = filter(lambda record: record.id == response.token and record.device_id == device_id, self.transactions)
        filtered_transactions = list(filtered_transactions)
        if len(filtered_transactions) == 0:
            logger.debug("Could not match received data to a transaction record")
            return
        # Update transaction, then remove
        metadata: RequestRecord = filtered_transactions[0]
        metadata.received_at = datetime.now()
        logger.info(metadata)
        self.transactions.remove(metadata)
        # Save data to database
        # self.db.insert({"id": metadata.id, "device": device_id, "action": response.action, "shareId": response.shareId ,
        # "data": str(base64.b64encode(response.data)), "requestedAt": str(metadata.sent_at), "receivedAt": str(metadata.received_at)})
        # Pass data to callback functions
        responseData: bytes = response.data[0:response.dataLength]
        responseJson: ResponseType = dict()
        responseJson["deviceId"] = device_id
        responseJson["actionType"] = response.action
        responseJson["shareId"] = int(response.shareId)
        responseJson["data"] = str(base64.b64encode(responseData).decode("utf-8"))
        self._callback(responseJson)

    def register_callback(self, fn: Callable[[ResponseType], None]) -> None:
        """Register a receive callback function.

        :param fn: Callback function
        :type fn: Callable function
        """
        self.fns.append(fn)

    def clear_callback(self):
        """Clear all the callback functions
        """
        self.fns.clear()

    def _callback(self, response: ResponseType) -> None:
        """Calls all registered callback functions.

        :param response: Return json dict including the deviceId, shareId, and data (base64 encoded)
        :type response: Dict[str, int, str]
        """
        for fn in self.fns:
            try:
                # Pass data to callback function
                fn(response)
            except Exception as e:
                logger.debug("Callback function failed to execute")
                logger.debug(e)
