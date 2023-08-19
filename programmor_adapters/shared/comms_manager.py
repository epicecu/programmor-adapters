from typing import List, Dict, Callable, Optional
from shared.comm import Comm

# Logging
import logging
logger = logging.getLogger(__name__)


class CommsManager:

    def __init__(self) -> None:
        """CommsManager
        Manages all the device communications
        """
        self.connections: Dict[str, Comm] = dict()

    def get_devices(self) -> List[str]:
        raise NotImplementedError("get_devices method not implemented")

    def get_device(self, device_id: str) -> Optional[Comm]:
        return self.connections.get(device_id, None)

    def check_device(self, device_id: str) -> bool:
        return self.get_device(device_id) is not None

    def connect_device(self, device_id: str, callback: Callable[[str, bytes], None]) -> bool:
        raise NotImplementedError("connect_device method not implemented")

    def disconnect_device(self, device_id: str) -> bool:
        if not self.check_device(device_id):
            return False
        # Close connection and delete
        try:
            # Close
            if self.check_device(device_id):
                self.connections[device_id].close()
                self.connections[device_id].stop()
                del self.connections[device_id]
            return True
        except Exception as e:
            logger.error(e)
            return False

    def disconnect_all_devices(self):
        device_ids = list()
        for device_id, _ in self.connections.items():
            device_ids.append(device_id)
        for device_id in device_ids:
            self.disconnect_device(device_id)
