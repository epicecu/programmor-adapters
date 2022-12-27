import struct
import zlib
from enum import Enum

FRAME_PAYLOAD_SIZE = 50


class ProcessState(Enum):
    """Communication Interface Process State.
    """
    OK = 0
    ERROR = 1


class Frame:
    """Automotive Frame Protocol (AFP) Version 1.
    """
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