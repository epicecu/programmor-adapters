import sys
import logging
import argparse
import os
import asyncio
from flask import Flask

from shared.api import API
from shared.socket_endpoint import SocketEndpoint
from shared.rest_endpoint import RestEndpoint

from usb.usb import USB


def main():

    # Setup argument parsing

    parser = argparse.ArgumentParser(description='An open source automotive tuning software usb adapter')

    parser.add_argument(
        "-f",
        "--log-file",
        help="The file to append all logs to.",
        required=False,
        default="~/.programmor/log.txt"
    )

    parser.add_argument(
        "-l",
        "--log-level",
        help="Select the log level to display to the stdout, all logs will be appended to file.",
        required=False,
        default="DEBUG"
    )

    args = parser.parse_args()

    # Setup logging
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    format = logging.Formatter("%(asctime)s [%(name)s] [%(threadName)s] [%(levelname)-5.5s] %(message)s")
    
    # File stream
    path = os.path.expanduser(os.path.dirname(args.log_file))
    os.makedirs(path, mode=0o775, exist_ok=True)
    file = os.path.join(path, os.path.basename(args.log_file))
    fileHandler = logging.FileHandler(filename=file, encoding='utf-8', mode='a')
    fileHandler.setLevel(level=logging.DEBUG)
    fileHandler.setFormatter(format)
    logger.addHandler(fileHandler)

    # Stdout stream
    stdHandler = logging.StreamHandler(stream=sys.stdout)
    stdHandler.setFormatter(format)
    n_level = getattr(logging, args.log_level.upper(), None)
    if not isinstance(n_level, int):
        n_level = logging.INFO
    stdHandler.setLevel(level=n_level)
    logger.addHandler(stdHandler)

    # Start Application

    logger.info("Programmor USB Adaptation")
 
    # Application to go here
    # sys.exit(app.exec())

    # Programmor Adapter API function 
    api = API(USB)

    # Flask application
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret!ya'

    # Programmor Adapter Endpoints to the GUI
    rest = RestEndpoint(app, api)
    socket = SocketEndpoint(app, api)

    # TEst
    # logger.debug(api.get_devices())
    # try:
    #     teensy = api.get_devices()[0]
    #     result = api.connect_device(teensy)
    #     api.disconnect_device(teensy)
    # except:
    #     print("TEst failed")

    # Starts the Socket-Flask, and Flask app 
    socket.start()

    # Stopping Adapter
    logger.info("Stopping Application")
    try:
        socket.stop()
        rest.stop()
    except:
        logger.debug("Failed to stop Socket or Rest apps")
    api.stop()

if __name__ == "__main__":
    main()
