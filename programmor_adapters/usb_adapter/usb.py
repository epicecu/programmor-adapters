import logging
import hashlib
import os
from time import sleep
from typing import List, Dict

from shared.comm import Comm, Frame

try:  # noqa: E722
    full_path = os.path.realpath(__file__)
    dir_path = os.path.dirname(full_path)
    os.add_dll_directory(os.path.join(dir_path, "../../lib"))
    import hid  # Linux & Windows
except Exception as e:
    print("Failed to import HID library, install required binaries for your system")
    print(e)


logger = logging.getLogger(__name__)

ENCODE = "utf-8"


class USB(Comm):

    def __init__(self) -> None:
        super().__init__()
        # Connected device
        self.device: hid.Device = None
        self.device_path: str = None
        self.device_id: str = None
        # Device Id to path lookup
        self.device_path_lookup: Dict[str, str] = dict()
        # self.get_device_ids()

    def __str__(self) -> str:
        return f"USB(id: {self.device_id} path: {self.device_path})"

    def get_device_ids(self) -> List[str]:
        """Get Device Ids
        """
        all_devices: List = hid.enumerate()
        compatible_devices: List[str] = list()
        for device in all_devices:
            device_path: str = device['path'].decode(ENCODE)
            # logger.debug(f"Checking {device_path}")
            if self.check_device_compatibility(device_path):
                logger.debug("Found device")
                device_id = hashlib.md5(device['path']).hexdigest()
                self.device_path_lookup[device_id] = device_path
                compatible_devices.append(device_id)
        return compatible_devices

    # Checks if this device is a
    def check_device_compatibility(self, path: str) -> bool:
        self.blocking = True
        sleep(0.001)
        # Connect to device
        try:
            device = hid.Device(path=path.encode(ENCODE))
        except Exception:
            # logger.debug(f"Failed to open device {path}")
            self.blocking = False
            return False
        logger.debug(f"Checking device compatibility {path}")
        # Send frame
        frame = Frame()
        frame.preamble = 0x02
        frame.checksum()
        as_bytes: bytes = bytes(frame.to_bytes())
        try:
            # Write seems to be slow here??? need to investigate if its my crappy firmware code lol
            device.write(as_bytes)
            print(frame)
            print(len(as_bytes))
        except hid.HIDException:
            # logger.debug("Failed to write")
            self.blocking = False
            return False
        sleep(0.001)
        # Read response
        response_bytes = device.read(64, 1)
        # Connected, accepted request but not response
        if len(response_bytes) == 0:
            logger.debug("No bytes returned")
            self.blocking = False
            return False
        # Process the response
        try:
            response = Frame(response_bytes)
            # logger.debug(f"Response {response}")
        except Exception as e:
            logger.debug(e)
            logger.debug(f"Not enough returned data {len(response_bytes)}")
            self.blocking = False
            return False
        # Check
        if not response.is_valid():
            logger.debug("Frame CRC not valid")
            return False
        if response.preamble != 0x03:
            logger.debug("Frame type incorrect")
            return False
        self.blocking = False
        return True

    def get_devices(self) -> List[str]:
        return self.get_device_ids()

    def read(self) -> bytes:
        # Return no bytes if device is not ready
        if self.device is None:
            return bytes(0)
        try:
            return self.device.read(64, 1)
        except Exception:
            return bytes(0)

    def write(self, buffer: bytes) -> None:
        buffer: bytes = bytes(buffer)
        if len(buffer) > 0 and self.device is None:
            return  # Not connected to device
        self.device.write(buffer)
        sleep(0.01)

    def connect(self, device_id: str) -> bool:
        if device_id not in self.device_path_lookup:
            logger.debug(f"Device id {device_id} not found in lookup")
            return False
        path = self.device_path_lookup[device_id]
        try:
            self.device = hid.Device(path=path.encode(ENCODE))
            self.device_path = path
            self.device_id = device_id
            logger.debug(f"Connected {self.__str__()}")
            return True
        except Exception:
            return False

    def close(self) -> None:
        if self.device is not None:
            self.device.close()
            logger.debug(f"Closed {self.__str__()}")
            self.device = None
