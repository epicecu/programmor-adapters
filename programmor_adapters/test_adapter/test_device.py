import time
from typing import List, Optional
import shared.proto.transaction_pb2 as transaction_pb2
from shared.types import MessageType
import test_adapter.proto.test_pb2 as test_pb2
from shared.api import TRANSACTION_MESSAGE_SIZE, DATA_MAX_SIZE

# Logging
import logging
logger = logging.getLogger(__name__)


class TestDevice:

    def __init__(
            self,
            name: str,
            device_id: str,
            id: int = 2,
            registry_id: int = 0x3E9,  # 1001
            serial_number: int = 123456789,
            shares_version: int = 1,
            firmware_version: int = 202308) -> None:
        self.name = name
        self.device_id = device_id
        # Common 1
        self.id = id
        self.registry_id = registry_id
        self.serial_number = serial_number
        self.shares_version = shares_version
        self.firmware_version = firmware_version
        # Share 1: Counter
        self.counter_start: int = 0
        self.counter_end: int = 20
        self.counter: int = self.counter_start
        # Device
        self.elapsed_time: float = 0
        self.outbound_data: List[bytes] = list()

    def tick(self) -> None:
        current_time = time.perf_counter()
        if current_time - self.elapsed_time > 1:
            # Increment counter
            self.counter = self.counter + 1
            # Wrap counter when we reach the end
            if self.counter > self.counter_end:
                self.counter = self.counter_start
            # Update time
            self.elapsed_time = current_time

    # Process Data
    # Adapter -> Test Device
    def process_data(self, data: bytes) -> None:
        inMessage = transaction_pb2.TransactionMessage()  # type: ignore
        try:
            inMessage.ParseFromString(bytes(data[0:TRANSACTION_MESSAGE_SIZE]))
        except BaseException:
            return

        # Request action
        if inMessage.action == transaction_pb2.TransactionMessage.COMMON_REQUEST:  # type: ignore
            # Common request
            commonMessage: transaction_pb2.Common1 = transaction_pb2.Common1()  # type: ignore
            commonMessage.id = self.id
            commonMessage.registryId = self.registry_id
            commonMessage.serialNumber = self.serial_number
            commonMessage.sharesVersion = self.shares_version
            commonMessage.firmwareVersion = self.firmware_version
            commonMessage.deviceName = self.name
            self.outbound_data.append(bytes(self.response_message(MessageType.COMMON, 1, inMessage.token,
                                      commonMessage.SerializeToString()).SerializeToString()))

        elif inMessage.action == transaction_pb2.TransactionMessage.SHARE_REQUEST:  # type: ignore

            if inMessage.shareId == 1:
                # Share1 request
                testMessage: test_pb2.TestMessage = test_pb2.Share1()  # type: ignore
                testMessage.startingNumber = self.counter_start
                testMessage.endingNumber = self.counter_end
                testMessage.counter = self.counter
                self.outbound_data.append(bytes(self.response_message(MessageType.SHARE, 1, inMessage.token,
                                          testMessage.SerializeToString()).SerializeToString()))

            elif inMessage.shareId == 2:
                # Share2 request
                testMessage: test_pb2.TestMessage = test_pb2.Share2()  # type: ignore
                testMessage.frequencyInputPinId = 101
                testMessage.digitalOutputPinId = 102
                testMessage.analogInputAPinId = 103
                testMessage.analogInputBPinId = 104
                self.outbound_data.append(bytes(self.response_message(MessageType.SHARE, 2, inMessage.token,
                                          testMessage.SerializeToString()).SerializeToString()))

            elif inMessage.shareId == 3:
                # Share2 request
                testMessage: test_pb2.TestMessage = test_pb2.Share3()  # type: ignore
                testMessage.loopsPerSecond = int(time.perf_counter())
                self.outbound_data.append(bytes(self.response_message(MessageType.SHARE, 3, inMessage.token,
                                          testMessage.SerializeToString()).SerializeToString()))

        elif inMessage.action == transaction_pb2.TransactionMessage.SHARE_PUBLISH:  # type: ignore
            # Share publish
            inData: bytes = inMessage.data[0:inMessage.dataLength]
            testMessage: test_pb2.TestMessage = test_pb2.Share1()  # type: ignore
            try:
                testMessage.ParseFromString(bytes(inData[0:DATA_MAX_SIZE]))
            except BaseException as e:
                logger.error("Failed to parse message", e)
                return
            # Process message
            self.counter_start = testMessage.startingNumber
            self.counter_end = testMessage.endingNumber

    # Get Data
    # Test Device -> Adapter

    def get_data(self) -> bytes:
        if len(self.outbound_data) > 0:
            return self.outbound_data.pop()
        else:
            return bytes(0)

    @staticmethod
    def response_message(message_type: MessageType, shareId: int, token: int, data: Optional[bytes]) -> transaction_pb2.TransactionMessage:  # type: ignore
        responseMessage = transaction_pb2.TransactionMessage()  # type: ignore
        responseMessage.token = token
        if message_type == MessageType.COMMON:
            responseMessage.action = transaction_pb2.TransactionMessage.COMMON_RESPONSE  # type: ignore
        else:
            responseMessage.action = transaction_pb2.TransactionMessage.SHARE_RESPONSE  # type: ignore
        responseMessage.shareId = shareId
        if data is None:
            data = bytes(0)
        # Check that the data is DATA_MAX_SIZE bytes or less
        if len(data) > DATA_MAX_SIZE:
            data = bytes(0)
        responseMessage.dataLength = len(data)
        responseMessage.data = data + bytes(DATA_MAX_SIZE - len(data))
        # print(responseMessage)
        # print(responseMessage.data.hex(" "))
        return responseMessage
