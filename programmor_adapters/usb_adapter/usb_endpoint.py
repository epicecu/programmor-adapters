from time import sleep
from typing import Optional
from collections import deque
import threading
import usb.core

import logging
logger = logging.getLogger(__name__)


class USBEndpoint(threading.Thread):
    """
    USBEndpoint.
    A generic USB endpoint. Extend this class to implement the reader/writer.
    """
    def __init__(self, endpoint: Optional[usb.core.Endpoint], interval: int) -> None:
        """Constructor method
        """
        threading.Thread.__init__(self)
        self.stop_flag: bool = False
        self.endpoint = endpoint
        self.interval = interval
        self.queue: deque[bytes] = deque()

    def start(self) -> None:
        """Starts the Endpoint
        """
        threading.Thread.start(self)
        self.stop_flag = False
        logger.debug("Starting USBEndpoint Thread")

    def stop(self) -> None:
        """Stops the thread
        """
        logger.debug("Stopping USBEndpoint Thread")
        self.stop_flag = True

    def run(self) -> None:
        """Run method used by python threading
        """
        while True:
            # Stop thread
            if self.stop_flag:
                logger.debug("Stopped USBEndpoint Thread")
                break

            # Process incoming messages
            self.action()

            # Sleep the thread as per the interval.
            sleep(self.interval/1000)

    def action(self):
        raise NotImplementedError("Action method not implemented")
