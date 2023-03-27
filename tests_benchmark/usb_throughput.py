from shared.api import API, MessageType
from usb_adapter.usb_manager import USBManager
from time import sleep
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

data_list = list()

def handle_data(data):
    data_list.append(data)

def main():
    api = API(USBManager)
    api.start()
    api.register_callback(lambda data: handle_data(data))
    
    devices = api.get_devices_detailed()

    if len(devices) == 0:
        exit("No found devices")

    teensy_id = devices[0]["deviceId"]

    print(api.get_devices_detailed())
    api.connect_device(teensy_id)
    
    sleep(0)
    print(api.get_devices_detailed())

    # Set Request
    api.set_scheduled_message(teensy_id, MessageType.SHARE, 1, 23)
    print("Set schedule")

if __name__ == "__main__":
    main()