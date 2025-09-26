from usb_adapter.usb_endpoint import USBEndpoint
from typing import Optional
import usb.core

import logging
logger = logging.getLogger(__name__)


class USBWrite(USBEndpoint):
    def __init__(self, endpoint: Optional[usb.core.Endpoint], interval: int) -> None:
        super().__init__(endpoint, interval)

    def action(self) -> None:
        data = None

        try:
            data = self.queue.popleft()
        except Exception:
            return

        try:
            if self.endpoint is not None:
                self.endpoint.write(bytes(data), 5)
                # print("Write")
        except Exception:
            if data:
                # print("Write Error")
                self.queue.appendleft(data)

    def write(self, buffer: bytes) -> None:
        try:
            if len(buffer) > 0:
                return self.queue.append(buffer)
        except Exception:
            pass
