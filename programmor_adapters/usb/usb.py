import logging
from time import sleep
from typing import List, Any

from shared.interface import Comm, Frame

try:  # noqa: E722
    import hid # Linux
except Exception as e:
    print("Failled to import HID library, install required binaries for your system")
    print(e)

try:  # noqa: E722
    import pywinusb.hid as hid # Windows
    def enumerate() -> any:
        device_strings: List[str] = list()
        devices = hid.HidDeviceFilter().get_devices()
        for device in devices:
            device_strings.append(device.path)
        return device_strings
    hid.enumerate = enumerate
except Exception:
    print("Failled to import HID library, install required binaries for your system")


logger = logging.getLogger(__name__)


class USB(Comm):

    def __init__(self) -> None:
        super().__init__()
        self.device: hid.Device = None
        self.devices: List[Any] = hid.enumerate()

    # Get list of devices
    def get_device_paths(self) -> List[str]:
        all_devices: List = hid.enumerate()
        compatible_devices: List[str] = list()
        for device in all_devices:
            if self.check_device_compatibility(device['path']):
                compatible_devices.append(device['path'])
        return compatible_devices

    # Checks if this device is a
    def check_device_compatibility(self, path: str) -> bool:
        result = False
        self.blocking = True
        sleep(0.01)
        # Connect to device
        try:
            device = hid.Device(path=path)
        except Exception:
            # logger.debug(f"Failed to open device {path}")
            self.blocking = False
            return result
        # Send frame
        frame = Frame()
        frame.preamble = 0x02
        frame.checksum()
        as_bytes: bytes = bytes(frame.to_bytes())
        device.write(as_bytes)
        # Read response
        response_bytes = device.read(64, 5)
        try:
            response = Frame(response_bytes)
            logger.debug(f"Response {response}")
        except Exception:
            logger.debug(f"Not enough returned data {len(response_bytes)}")
            self.blocking = False
            return result
        # Check
        if response.is_valid():
            if response.preamble == 0x03:
                result = True
        self.blocking = False
        return result

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

    def connect(self, path: str) -> bool:
        try:
            self.device = hid.Device(path=path)
            return True
        except Exception:
            return False

    def close(self) -> None:
        if self.device is not None:
            self.device.close()
            self.device = None
