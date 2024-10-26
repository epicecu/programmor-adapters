import hashlib
from typing import List, Dict, Callable, Tuple
from shared.comms_manager import CommsManager
from shared.frame import Frame, BytesLengthError
from usb_adapter.helper import get_device_endpoints
from usb_adapter.usb import USB

import usb.core
import usb.util
import libusb_package

# Logging
import logging
logger = logging.getLogger(__name__)

ENCODE = "utf-8"


class USBManager(CommsManager):

    def __init__(self) -> None:
        super().__init__()

        # Device Id to path lookup
        self.device_vender_product_lookup: Dict[str, Tuple[int, int]] = dict()

    def get_device_id_from_vender_product(self, vender_id: int, product_id: int) -> str | None:
        for device_id, (device_vender_id, device_product_id) in self.device_vender_product_lookup.items():
            if device_vender_id == vender_id and device_product_id == product_id:
                return device_id
        return None

    def get_devices(self) -> List[str]:
        """Get Device Ids
        """
        logger.debug("Getting device ids")
        compatible_devices: List[str] = list()

        dev: usb.core.Device  # hinting for-loop variable
        for dev in libusb_package.find(find_all=True):
            # Check if device is available
            if dev is None:
                continue
            # Check if meta data is available
            try:
                assert dev.manufacturer is not None
                assert dev.product is not None
            except Exception:
                continue
            # print(f"{dev.manufacturer} {dev.product}")
            # Check if the device is already in use
            device_id = self.get_device_id_from_vender_product(dev.idVendor, dev.idProduct)
            if device_id:
                if self.check_device(device_id):
                    # Found!, don't disrupt the connected device
                    compatible_devices.append(device_id)
                    continue
            # Get device configuration
            endpoint_in, endpoint_out = get_device_endpoints(dev)
            if endpoint_in is None or endpoint_out is None:
                continue
            # Construct Programmor Check Request Frame
            request_frame = Frame()
            request_frame.preamble = 0x02
            request_frame.checksum()
            request_frame_as_bytes = bytes(request_frame.to_bytes())
            # Send bytes
            try:
                endpoint_out.write(request_frame_as_bytes, 1)
            except usb.core.USBTimeoutError:
                continue
            except usb.core.USBError:
                continue
            # Read bytes
            try:
                received = endpoint_in.read(64, 1)
            except usb.core.USBTimeoutError:
                continue
            except usb.core.USBError:
                continue
            # Convert bytes to Frame
            received_as_bytes = bytes(received)
            try:
                received_frame = Frame(received_as_bytes)
            except BytesLengthError as e:
                logger.debug(e)
                continue
            # Check
            if not received_frame.is_valid():
                logger.debug("Frame CRC not valid")
                continue
            if received_frame.preamble != 0x03:
                logger.debug("Frame type incorrect")
                continue
            # Found a compatible device :)
            logger.debug(f"Found device vender {dev.idVendor} product {dev.idProduct}")
            device_id = hashlib.md5(f"{dev.idVendor}{dev.idProduct}".encode(ENCODE)).hexdigest()
            self.device_vender_product_lookup[device_id] = (dev.idVendor, dev.idProduct)
            compatible_devices.append(device_id)
            # dev.reset()
            usb.util.dispose_resources(dev)

        return compatible_devices

    def connect_device(self, device_id: str, callback: Callable[[str, bytes], None]) -> bool:
        if self.check_device(device_id):
            logger.debug(f"Device already connected {device_id}")
            return False
        # Get the product and vender ids
        lookup = self.device_vender_product_lookup.get(device_id)
        if lookup is None:
            return False
        vender, product = lookup
        # Create USB Connection and connect
        logger.debug("Creating a new comms device")
        self.connections[device_id] = USB(vender, product)
        self.connections[device_id].set_received_message_callback(lambda data: callback(device_id, data))
        self.connections[device_id].start()
        if not self.connections[device_id].connect():
            logger.debug(f"Failed to connect to device {device_id}")
            self.connections[device_id].stop()
            del self.connections[device_id]
            return False
        logger.debug(f"Connected to device {device_id}")
        return True
