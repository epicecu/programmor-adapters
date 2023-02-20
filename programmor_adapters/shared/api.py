from shared.comm import Comm
from shared.datetime import diff_ms
from datetime import datetime
from time import sleep
from typing import List, Dict, Any, Protocol, Callable, Tuple
from uuid import uuid4
from tinydb import TinyDB, Query
import threading

# Transaction Protobuf File
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

class ScheduledRequest(Protocol):
    """Scheduled Request Message Object
    """
    device_id: str
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


class RequestRecord(Protocol):
    """API Tranactions with the device
    """
    id: int
    device_id: str
    sent_at: datetime
    received_at: datetime
    created_at: datetime = datetime.now()


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
        self.fns: List[Callable[[bytes], None]] = list()
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
                self.request_share(schedule.device_id, schedule.share_id)
                schedule.tick()

    def set_scheduled_message(self, device_id: str, shareId: int, interval_ms: float = 100) -> None:
        """Set Schedule Message

        :param device_id: A Comms device id
        :type device_id: str
        :param shareId: A share id
        :type device_id: int
        :param interval_ms: The scheduled interval time
        :type device_id: float
        """
        # Check if schedule already exists
        schedule = next(filter(lambda schedule: schedule.share_id == shareId and schedule.device_id == device_id, self.scheduled), None)
        # Create or modify the schedule
        if schedule == None:
            # Create new schedule
            schedule = ScheduledRequest()
            self.scheduled.append(schedule)
        else:
            # Update the schedule
            schedule.update_interval(interval_ms)

    def clear_scheduled_message(self, device_id: str, shareId: int) -> None:
        """Clear Scheduled Message

        :param device_id: A Comms device id
        :type device_id: str
        :param shareId: A share id
        :type device_id: int
        """
        schedule = next(filter(lambda schedule: schedule.share_id == shareId and schedule.device_id == device_id, self.scheduled), None)
        if schedule != None:
            self.scheduled.remove(schedule)

    def get_devices(self) -> List[str]:
        """Returns a list of Programmor compatible device ids.

        :return: A list of device ids
        :rtype: str
        """
        comm = self.comm() # This may be an anti pattern, fix latter
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
                common.ParseFromString(self.request_common_sync(device_id, 1))
            except BaseException as e:
                print(f"Failed to parse common message: {e}")
                continue
            device = {
                "adapterDeviceId": device_id,
                "id": common.id, #NOTE: Not sure why we need this, might go
                "name": common.deviceName,
                "registryId": common.registryId,
                "serialNumber": common.serialNumber,
                "sharesVersion": common.sharesVersion,
                "firmwareVersion": common.firmwareVersion
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
        """Checks if a device is avaliable and connected.

        :param device_id: A Comms device id
        :type device_id: str
        :return: Status
        :rtype: bool
        """
        if self.get_device(device_id) != None:
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
        print("Creating a new comms obj")
        self.connections[device_id] = self.comm()
        self.connections[device_id].set_received_message_callback(lambda data: self._on_receive(device_id, data))
        self.connections[device_id].get_devices()
        self.connections[device_id].start()
        if not self.connections[device_id].connect(device_id):
            logger.debug(f"Failed to connect to device {device_id}")
            self.connections[device_id].stop()
            del self.connections[device_id]
            return False
        logger.debug(f"Connected to device {device_id}")
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
            self.connections[device_id].close()
            self.connections[device_id].stop()
            del self.connections[device_id]
            return True
        except:
            return False

    def request_share(self, device_id: str, shareId: int) -> None:
        """Request a Share from the Comms device

        :param device_id: A Comm's device id
        :type device_id: str
        :param shareId: A share id
        :type shareId: int
        """
        device = self.get_device(device_id)
        if device == None:
            return
        # Request share from device
        request_message = self._request_message(shareId)
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

    def request_share_sync(self, device_id: str, shareId: int, timeout_s: float = 1) -> bytes:
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
        if device == None:
            return bytes(0)
        # Request share from device
        request_message_bytes = self._request_message(shareId).SerializeToString()
        response = transaction_pb2.TransactionMessage()
        try:
            response.ParseFromString(bytes(device.send_then_receive_message(request_message_bytes, timeout_s)[0:TRANSACTION_MESSAGE_SIZE]))
        except BaseException:
            return bytes(0)
        return response.data[0:response.dataLength]

    def request_common_sync(self, device_id: str, shareId: int, timeout_s: float = 1) -> bytes:
        """Request a Common from the Comms device and wait for a response within the timeout.

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
        if device == None:
            return bytes(0)
        # Common share from device
        common_message_bytes = self._common_message(shareId).SerializeToString()
        response = transaction_pb2.TransactionMessage()
        try:
            data = device.send_then_receive_message(common_message_bytes, timeout_s)
            response.ParseFromString(bytes(data[0:TRANSACTION_MESSAGE_SIZE]))
        except BaseException as e:
            logger.debug(f"Failed to parse respose {e}")
            return bytes(0)
        return response.data[0:response.dataLength]

    def publish_share(self, device_id: str, shareId: int, data: bytes) -> None:
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
        if device == None:
            return
        # Generate publish message
        publish_message = self._publish_message(shareId, data)
        # Generate transaction record
        record = RequestRecord()
        record.id = publish_message.token
        record.device_id = device_id
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

    def _common_message(self, shareId: int) -> transaction_pb2.TransactionMessage:
        """A Common Message

        :param shareId: A share id
        :type shareId: int
        :return: A transaction message
        :rtype: transaction_pb2.TransactionMessage
        """
        commonMessage = transaction_pb2.TransactionMessage()
        commonMessage.token = uuid4().int >> 96
        commonMessage.action = transaction_pb2.TransactionMessage.COMMON
        commonMessage.shareId = shareId
        commonMessage.dataLength = 1
        commonMessage.data = bytes(DATA_MAX_SIZE)
        return commonMessage

    def get_shares(self, device_id:str, to_time: datetime, from_time: datetime, shareId: int) -> List[bytes]:
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
        items = self.db.search(item.device == device_id and item.shareId == shareId and item.receivedAt >= to_time and item.receivedAt <= from_time )
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
        self.db.insert({"id": metadata.id, "device": device_id, "action": response.action, "shareId": response.shareId ,"data": response.data, "requestedAt": metadata.sent_at, "receivedAt": metadata.received_at})
        # Pass data to callback functions
        self._callback(response.data[0:response.dataLength])

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

    def _callback(self, data: bytes) -> None:
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
