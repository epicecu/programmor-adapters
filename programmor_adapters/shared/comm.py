import threading
import random
from math import ceil
from typing import Callable, Dict, List
from queue import Queue
from time import sleep, perf_counter

from shared.frame import Frame, ProcessState, FRAME_PAYLOAD_SIZE

import logging
logger = logging.getLogger(__name__)


# Comm base class.
class Comm(threading.Thread):
    """Communication Interface
    To be extended to support Programmor communication methods, self contained class using
    python threading. Supports packeting data into Frames to receive & send to the device.
    """

    def __init__(self) -> None:
        """Constructor method
        """
        threading.Thread.__init__(self)
        self.stop_flag: bool = False
        self.blocking: bool = False
        # Message as bytes
        self.messages_outgoing: Queue[bytes] = Queue()
        # Map of FrameIds by Queue of Frames
        self.inFrames: Dict[int, List[Frame]] = {}
        self.outFrames: Dict[int, List[Frame]] = {}
        # Received message callback
        self.fn: Callable[[bytes], None] = None
        self.lastMessage: bytes = bytes()

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
        self.close()

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

            # Process incoming messages
            self.process_incoming_frames()

            # Process outgoing messages
            self.process_outgoing_frames()

            # Sleep the thread
            sleep(0.0001)  # 0.1ms

    def process_incoming_frames(self) -> ProcessState:
        """Processes the incoming frames.

        :return: State of the process
        :rtype: ProcessState
        """
        # Read data
        data = self.read()

        if len(data) != 64:
            return ProcessState.ERROR

        # Ok frame
        frame = Frame()
        frame.from_bytes(data)
        # print(f"Received {frame}")

        # Check if crc is correct
        if not frame.is_valid():
            return ProcessState.ERROR

        # Is this frame a data frame
        if frame.preamble != 0x01:
            return ProcessState.ERROR

        # Is this frame for PC.. 0x01?
        if frame.destinationAddress != 0x01:
            return ProcessState.ERROR

        # Get Queue of frames for the FrameId
        frames: List[Frame] = self.inFrames.get(frame.frameId)
        if frames is None:
            self.inFrames[frame.frameId] = list()
            self.inFrames[frame.frameId].append(frame)
        else:
            # Push on new frame
            frames.append(frame)

        remove_frames: list[int] = list()

        # Process a valid set of frames
        for _, frames in self.inFrames.items():
            # Check if we have a complete set
            for frame in frames:
                if frame.frameOrder != 1:
                    continue
                # Single frame
                if frame.frameTotal == 1:
                    # Callback
                    remove_frames.append(frame.frameId)
                    self.lastMessage = frame.payload
                    if self.fn is not None:
                        self.fn(frame.payload)
                # Multiple frames
                else:
                    # Check if we have the remaining data..
                    if len(frames) == frame.frameTotal:
                        message_bytes: bytearray = bytearray()
                        for order in range(frame.frameTotal):
                            # frame = next(frame for frame in frames if frame.frameOrder == order)
                            frames_filtered = filter(lambda x: x.frameOrder == order+1, frames)
                            count = 0
                            # Add payload to bytearray
                            for f in frames_filtered:
                                message_bytes.extend(f.payload)
                                count = count+1
                            # Could not find frame with order
                            if count == 0:
                                message_bytes.clear()
                                break
                        if len(message_bytes) > 0:
                            # Callback
                            remove_frames.append(frame.frameId)
                            self.lastMessage = message_bytes
                            if self.fn is not None:
                                self.callback(message_bytes)

        # Remove used frame sets
        for setId in remove_frames:
            _ = self.inFrames.pop(setId, None)

        return ProcessState.OK

    def process_outgoing_frames(self) -> ProcessState:
        """Processes the outgoing frames.

        :return: State of the process
        :rtype: ProcessState
        """
        # Check if we have data to send
        if self.messages_outgoing.empty():
            return ProcessState.ERROR

        # The message to send
        data = self.messages_outgoing.get()

        # The amount of frames required to send the message
        required_frames = ceil(len(data)/FRAME_PAYLOAD_SIZE)

        # frame id
        frameId = random.getrandbits(32)

        for i in range(0, required_frames):
            # Frame i
            frame = Frame()
            frame.frameId = frameId
            frame.frameTotal = required_frames
            frame.frameOrder = i+1
            payload = bytearray(data[i*FRAME_PAYLOAD_SIZE:(i+1)*FRAME_PAYLOAD_SIZE])
            payload.extend(bytes(FRAME_PAYLOAD_SIZE-len(payload)))
            frame.payload = payload
            frame.checksum()
            # print(f"Sending {frame}")
            # Write data
            frame_data = frame.to_bytes()
            self.write(frame_data)

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
        raise NotImplementedError("Read method not implemented")

    def write(self, buffer: bytes) -> None:
        """Writes data to the device.

        :return: 64 bytes to the device
        :rtype: bytes
        """
        raise NotImplementedError("Write method not implemented")

    def close(self) -> None:
        """Closes connection to the device.
        """
        raise NotImplementedError("Close method not implemented")
