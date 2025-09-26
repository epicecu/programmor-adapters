import usb.core
import usb.util
import libusb_package
from typing import Optional

from shared.comm import Comm
from usb_adapter.helper import get_device_endpoints
from usb_adapter.usb_read import USBRead
from usb_adapter.usb_write import USBWrite

import logging
logger = logging.getLogger(__name__)


class USB(Comm):

    def __init__(self, device_id_vender: int, device_id_product: int) -> None:
        super().__init__()
        # Connected device
        self.device: Optional[usb.core.Device] = None
        self.device_endpoint_in: Optional[usb.core.Endpoint] = None
        self.device_endpoint_out: Optional[usb.core.Endpoint] = None
        # Device id
        self.device_id_vender: int = device_id_vender
        self.device_id_product: int = device_id_product
        # meta data
        # self.device_manufacturer: str = None
        # self.device_product: str = None
        # Endpoints.
        self.read_endpoint: Optional[USBRead] = None
        self.write_endpoint: Optional[USBWrite] = None

    def __str__(self) -> str:
        return f"USB(id: vender_id: {self.device_id_vender} product_id: {self.device_id_product})"

    def read(self) -> bytes:
        # Return no bytes if device is not ready
        if self.device is None or self.read_endpoint is None:
            return bytes(0)
        return self.read_endpoint.read()

    def write(self, buffer: bytes) -> None:
        if len(buffer) > 0 and self.device is None:
            return  # Not connected to device
        if self.write_endpoint:
            self.write_endpoint.write(buffer)

    def connect(self) -> bool:
        self.device: Optional[usb.core.Device] = libusb_package.find(idVendor=self.device_id_vender, idProduct=self.device_id_product)  # type: ignore
        if self.device is None:
            return False
        self.device_endpoint_in, self.device_endpoint_out = get_device_endpoints(self.device)
        if self.device_endpoint_in is None or self.device_endpoint_out is None:
            return False
        self.read_endpoint = USBRead(self.device_endpoint_in, 1)
        self.write_endpoint = USBWrite(self.device_endpoint_out, 1)
        self.read_endpoint.start()
        self.write_endpoint.start()
        logger.debug(f"Connected {self.__str__()}")
        return True

    def close(self) -> None:
        if self.device is not None:
            logger.debug("Closing device")
            # self.device.reset()
            usb.util.dispose_resources(self.device)
            self.device = None
            if self.read_endpoint:
                self.read_endpoint.stop()
            if self.write_endpoint:
                self.write_endpoint.stop()
            self.read_endpoint = None
            self.write_endpoint = None
            self.device_endpoint_in = None
            self.device_endpoint_out = None
            logger.debug(f"Closed {self.__str__()}")
