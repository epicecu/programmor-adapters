from typing import Optional
import usb.core
import usb.util
import libusb_package

from shared.comm import Comm
from usb_adapter.helper import get_device_endpoints

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

    def __str__(self) -> str:
        return f"USB(id: vender_id: {self.device_id_vender} product_id: {self.device_id_product})"

    def read(self) -> bytes:
        # Return no bytes if device is not ready
        if self.device is None:
            return bytes(0)
        try:
            if self.device_endpoint_in is not None:
                return bytes(self.device_endpoint_in.read(64, 1))
            else:
                return bytes(0)
        except Exception:
            return bytes(0)

    def write(self, buffer: bytes) -> None:
        if len(buffer) > 0 and self.device is None:
            return  # Not connected to device
        if self.device_endpoint_out is not None:
            self.device_endpoint_out.write(bytes(buffer), 1)

    def connect(self) -> bool:
        self.device: Optional[usb.core.Device] = libusb_package.find(idVendor=self.device_id_vender, idProduct=self.device_id_product)  # type: ignore
        if self.device is None:
            return False
        self.device_endpoint_in, self.device_endpoint_out = get_device_endpoints(self.device)
        if self.device_endpoint_in is None or self.device_endpoint_out is None:
            return False
        logger.debug(f"Connected {self.__str__()}")
        return True

    def close(self) -> None:
        if self.device is not None:
            logger.debug("Closing device")
            # self.device.reset()
            usb.util.dispose_resources(self.device)
            self.device = None
            self.device_endpoint_in = None
            self.device_endpoint_out = None
            logger.debug(f"Closed {self.__str__()}")
