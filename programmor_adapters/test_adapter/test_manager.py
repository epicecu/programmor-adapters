from typing import List, Callable
from shared.comms_manager import CommsManager
from test_adapter.test_comm import TestComm
from test_adapter.test_device import TestDevice


# Logging
import logging
logger = logging.getLogger(__name__)

ENCODE = "utf-8"


class TestManager(CommsManager):

    def __init__(self) -> None:
        super().__init__()
        self.devices: List[TestDevice] = list()
        self.devices.append(TestDevice(name="January", device_id="fakeusb-janmoo1", id=2, serial_number=123))
        self.devices.append(TestDevice(name="February", device_id="fakeusb-febroff2", id=3, serial_number=456))

    def get_devices(self) -> List[str]:
        """Get Device Ids
        """
        logger.debug("Getting device ids")
        compatible_devices: List[str] = list()
        for device in self.devices:
            compatible_devices.append(device.device_id)
        return compatible_devices

    def connect_device(self, device_id: str, callback: Callable) -> bool:
        if self.check_device(device_id):
            logger.debug(f"Device already connected {device_id}")
            return False
        # Create Test Connection and connect
        logger.debug("Creating a new comms device")
        test_device = self.get_test_device(device_id)
        if test_device is None:
            return False
        self.connections[device_id] = TestComm(test_device)
        self.connections[device_id].set_received_message_callback(lambda data: callback(device_id, data))
        self.connections[device_id].start()
        if not self.connections[device_id].connect():
            logger.debug(f"Failed to connect to device {device_id}")
            self.connections[device_id].stop()
            del self.connections[device_id]
            return False
        logger.info(f"Connected to device {device_id}")
        return True

    def get_test_device(self, device_id: str) -> TestDevice | None:
        for device in self.devices:
            if device.device_id == device_id:
                return device
        return None
