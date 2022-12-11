import logging
import threading
import struct
import zlib
import random
from math import ceil
from enum import Enum
from typing import Callable, Dict, List, Protocol
from queue import Queue
from time import sleep, perf_counter

logger = logging.getLogger(__name__)

FRAME_PAYLOAD_SIZE = 50


class ProcessState(Enum):
    OK = 0
    ERROR = 1

# Automotive Frame Protocol (AFP)


class Frame:
    # Null = 0x00
    # Data packet = 0x01
    # Programmor Compatible Request = 0x02
    # Programmor Compatible Response = 0x03
    # ARP Request packet = 0x04
    # ARP Response packet = 0x05
    preamble: int = 0x01  # Data frame
    # 0x00 = A catch all address, first receiving device to respond
    # 0x01 = PC software Programmor.com
    # 0x02 - 0x7F = A specific device on the local network
    destinationAddress: int = 0x00  # Next device
    # 0x00 = Reserved
    # 0x01 = PC software Programmor.com
    # 0x02 - 0x7F = A specific device on the local network
    sourceAddress: int = 0x01  # From PC
    frameId: int = 1
    frameOrder: int = 1  # this frame's order
    frameTotal: int = 1  # total amount of frames for the message
    payload: bytes = bytes()  # size of 47 bytes
    crc: int = 0  # check sum of the all the above variables

    def __init__(self, frame_bytes: bytes = None) -> None:
        if frame_bytes is not None:
            self.from_bytes(frame_bytes)

    def __bytes__(self) -> bytearray:
        return self.to_bytes()

    def calculate_crc(self) -> int:
        # Check sum the frame up to the crc
        return zlib.crc32(self.to_bytes()[0:60]) & 0xffffffff

    def checksum(self) -> None:
        self.crc = self.calculate_crc()

    # Usually called after receiving data
    def is_valid(self) -> bool:
        return self.crc == self.calculate_crc()

    def __str__(self) -> str:
        return f"""Frame(preamble: {self.preamble} destinationAddress: {self.destinationAddress} sourceAddress: {self.sourceAddress}
        id: {self.frameId} order: {self.frameOrder} total: {self.frameTotal} payload: {self.payload.hex('/')} crc: {self.crc})"""

    def from_bytes(self, frame_bytes: bytes):
        if len(frame_bytes) != 64:
            raise Exception("Bytes length does not equal 64")
        # Unpack
        self.preamble = struct.unpack("<H", frame_bytes[0:2])[0]
        self.destinationAddress = struct.unpack("<B", frame_bytes[2:3])[0]
        self.sourceAddress = struct.unpack("<B", frame_bytes[3:4])[0]
        self.frameId = struct.unpack("<I", frame_bytes[4:8])[0]
        self.frameOrder = struct.unpack("<B", frame_bytes[8:9])[0]
        self.frameTotal = struct.unpack("<B", frame_bytes[9:10])[0]
        self.payload = frame_bytes[10:60]
        self.crc = struct.unpack("<I", frame_bytes[60:64])[0]

    def to_bytes(self) -> bytearray:
        # Pack
        frame_bytes: bytearray = bytearray()
        frame_bytes.extend(struct.pack("<H", self.preamble))
        frame_bytes.extend(struct.pack("<B", self.destinationAddress))
        frame_bytes.extend(struct.pack("<B", self.sourceAddress))
        frame_bytes.extend(struct.pack("<I", self.frameId))
        frame_bytes.extend(struct.pack("<B", self.frameOrder))
        frame_bytes.extend(struct.pack("<B", self.frameTotal))
        # Check if the payload is the correct size
        if len(self.payload) > FRAME_PAYLOAD_SIZE:
            raise Exception("Payload size is greater then FRAME_PAYLOAD_SIZE")
        elif len(self.payload) < FRAME_PAYLOAD_SIZE:
            # Padd out the payload to equal FRAME_PAYLOAD_SIZE
            frame_bytes.extend(self.payload)
            frame_bytes.extend(bytes(FRAME_PAYLOAD_SIZE-len(self.payload)))
        else:
            frame_bytes.extend(self.payload)
        # Calculate checksum
        self.crc = zlib.crc32(frame_bytes[0:60]) & 0xffffffff
        frame_bytes.extend(struct.pack("<I", self.crc))
        # Check if the
        return frame_bytes


# Comm base class.
class Comm(threading.Thread):

    def __init__(self) -> None:
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

    # Starts the thread

    def start(self) -> None:
        threading.Thread.start(self)
        logger.info("Starting Comms Thread")

    # Stops the thread
    def stop(self) -> None:
        logger.info("Stopping Comms Thread")
        self.stop_flag = True
        self.blocking = True
        self.close()

    # Threading main function
    def run(self) -> None:
        while True:
            # Stop thread
            if self.stop_flag:
                logger.info("Stopped Comms Thread")
                break

            # Skip if blocking
            if self.blocking:
                continue

            # Process incoming messages
            self.process_incoming_frames()

            # Process outgoing messages
            self.process_outgoing_frames()

            # Sleep the thread
            sleep(0.001)  # 1ms

    def process_incoming_frames(self) -> ProcessState:
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
                                self.fn(message_bytes)

        # Remove used frame sets
        for setId in remove_frames:
            _ = self.inFrames.pop(setId, None)

        return ProcessState.OK

    def process_outgoing_frames(self) -> ProcessState:
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

    # Send and Receive without threading
    def send_then_receive_message(self, message_bytes: bytes, wait_s: float = 0.5) -> bytes:
        oldMessage = self.lastMessage
        self.messages_outgoing.put(message_bytes)
        startTime = perf_counter()
        while ((perf_counter() - startTime) < wait_s):
            sleep(0.001)
            if self.lastMessage != oldMessage:
                return self.lastMessage
        return bytes(0)

    # Send message to device
    def send_message(self, message_bytes: bytes) -> None:
        self.messages_outgoing.put(message_bytes)
        # instead of a list, simply create the frames and write

    # Function called when a new message has been received
    def set_received_message_callback(self, fn: Callable[[bytes], None]):
        self.fn = fn

    # Read bytes from device
    def read(self) -> bytes:
        raise NotImplementedError("Read method not implemented")

    # Write bytes to device
    def write(self, buffer: bytes) -> None:
        raise NotImplementedError("Write method not implemented")

    # Close device connection
    def close(self) -> None:
        raise NotImplementedError("Close method not implemented")
