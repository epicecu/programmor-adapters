import threading
import random
from math import ceil
from typing import Callable, Dict, List
from queue import Queue
from time import sleep, perf_counter

import logging

from shared.frame import ProcessState
from test_adapter.test_device import TestDevice
logger = logging.getLogger(__name__)


# Test class.
class TestComm(threading.Thread):
    """Communication Interface
    To be extended to support Programmor communication methods, self contained class using
    python threading. Supports packeting data into Frames to receive & send to the device.
    """

    def __init__(self, device: TestDevice) -> None:
        """Constructor method
        """
        threading.Thread.__init__(self)
        self.stop_flag: bool = False
        self.blocking: bool = False
        # Message as bytes
        self.messages_outgoing: Queue[bytes] = Queue()
        # Received message callback
        self.fn: Callable[[bytes], None] = None
        self.lastMessage: bytes = bytes()
        # Test device
        self.device = device
        self.connected = False

    def start(self) -> None:
        """Starts the thread
        """
        threading.Thread.start(self)
        logger.debug("Starting Comms Thread")

    def stop(self) -> None:
        """Stops the thread
        """
        logger.debug("Stopping Comms Thread")
        self.stop_flag = True
        self.blocking = True
        # self.close()

    def run(self) -> None:
        """Run method used by python threading
        """
        while True:
            # Stop thread
            if self.stop_flag:
                logger.debug("Stopped Comms Thread")
                break

            # Skip if blocking
            if self.blocking:
                continue

            # Tick
            self.device.tick()

            # Process incoming messages
            self.process_incoming_data()

            # Process outgoing messages
            self.process_outgoing_data()

            # Sleep the thread
            # sleep(0.0001)  # 0.1ms

    def process_incoming_data(self) -> ProcessState.ERROR:
        # Read data
        data = self.read()
        if len(data) == 0:
            return ProcessState.ERROR
        self.lastMessage = data
        if self.fn is not None:
            self.callback(data)
        return ProcessState.OK


    def process_outgoing_data(self) -> ProcessState.ERROR:
        # Check if we have data to send
        if self.messages_outgoing.empty():
            return ProcessState.ERROR
        # The message to send
        data = self.messages_outgoing.get()
        self.write(data)
        return ProcessState.OK

    def send_then_receive_message(self, message_bytes: bytes, wait_s: float = 0.5) -> bytes:
        """Send a message then wait for a response.

        :param message_bytes: Data to send to the device
        :type message_bytes: bytes
        :param wait_s: Waiting timeout in seconds
        :type wait_s: float
        :return: Response from the device
        :rtype: bytes
        """
        oldMessage = self.lastMessage
        self.messages_outgoing.put(message_bytes)
        startTime = perf_counter()
        currentTime = perf_counter()
        while ((currentTime - startTime) < wait_s):
            # asyncio.sleep(0.001)
            currentTime = perf_counter()
            sleep(0.001)
            if self.lastMessage != oldMessage:
                logger.debug(f"Sent and received message in {currentTime-startTime}ms")
                return self.lastMessage
        return bytes(0)

    def send_message(self, message_bytes: bytes) -> None:
        """Send a message to the device.

        :param message_bytes: Message to send as bytes
        :type message_bytes: bytes
        """
        self.messages_outgoing.put(message_bytes)
        # instead of a list, simply create the frames and write

    def set_received_message_callback(self, fn: Callable[[bytes], None]) -> None:
        """Set the callback function to be called when a new message
        has been received.

        :param message_bytes: Callback function
        :type message_bytes: Callable()
        """
        self.fn = fn

    def callback(self, message_bytes: bytes) -> None:
        """To be called on successful response from device.

        :param message_bytes: Message to send as bytes
        :type message_bytes: bytes
        """
        self.fn(message_bytes)

    def is_callback(self) -> bool:
        """Checks if a callback function is set.

        :return: True or False
        :rtype: bool
        """
        return self.fn is not None

    def read(self) -> bytes:
        """Reads data from the device.

        :return: 64 bytes from the device
        :rtype: bytes
        """
        return self.device.get_data()

    def write(self, buffer: bytes) -> None:
        """Writes data to the device.

        :return: 64 bytes to the device
        :rtype: bytes
        """
        self.device.process_data(buffer)

    def connect(self) -> bool:
        logger.debug(f"Connected {self.__str__()}")
        self.connected = True
        return True

    def close(self) -> None:
        """Closes connection to the device.
        """
        self.connected = False