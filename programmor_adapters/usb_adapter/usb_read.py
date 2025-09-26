from usb_adapter.usb_endpoint import USBEndpoint
from typing import Optional
import usb.core

import logging
logger = logging.getLogger(__name__)


class USBRead(USBEndpoint):
    def __init__(self, endpoint: Optional[usb.core.Endpoint], interval: int) -> None:
        super().__init__(endpoint, interval)

    def action(self) -> None:
        try:
            if self.endpoint is not None:
                self.queue.append(bytes(self.endpoint.read(64, 1)))
                # print("Read")
        except Exception:
            # print("Read Error")
            # print(e)
            pass

    def read(self) -> bytes:
        try:
            return self.queue.popleft()
        except Exception:
            return bytes(0)
