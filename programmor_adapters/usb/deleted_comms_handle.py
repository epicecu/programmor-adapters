import logging
from typing import Any
from programmor.comms.usb import USB
# from PyQt6.QtSerialPort import QSerialPort
from PyQt6.QtCore import QObject, pyqtSignal, QThread  # QIODeviceBase
from uuid import uuid4
from time import perf_counter
from programmor.helper import ImportPythonFile

import programmor.proto.transaction_pb2 as transaction_pb2

logger = logging.getLogger(__name__)

DATA_MAX_SIZE = 80
TRANSACTION_MESSAGE_SIZE = 99


class CommsHandle(QObject):
    finished = pyqtSignal()
    requestShareSignal = pyqtSignal(int)
    publishShareSignal = pyqtSignal(int)

    def __init__(self, protoModuleLocation: str, store):
        super().__init__()
        # Import proto file
        global shares_pb2
        shares_pb2 = ImportPythonFile(protoModuleLocation)
        # Defaults
        self.comms = USB()
        self.comms.start()
        self.store = store
        self.connected = False
        self.inBuffer = bytes()
        self.inSize = 0
        # Thread params
        self.runnning = True
        self.startCommunicating = False
        self.requestPreviousTime = perf_counter()
        self.publishPreviousTime = perf_counter()
        # Signals/Slots
        self.requestShareSignal.connect(self.requestShare)
        self.publishShareSignal.connect(self.publishShare)

    def connectDevice(self, port: str) -> bool:
        # Disconnect the signal and disconnect device
        if self.comms.device:
            self.comms.close()
        # Connect to device
        self.comms.received_message_callback(lambda received: self.handleResponse(received))
        # Open the port
        if self.comms.connect(port):
            self.connected = True
            return True
        else:
            self.comms.stop()
            return False

    def disconnectDevice(self) -> bool:
        if self.comms.device:
            self.comms.close()
            self.connected = False
            return True
        return False

    def handleResponse(self, data: bytes) -> None:
        # Handle response
        data = bytes(data[0:TRANSACTION_MESSAGE_SIZE])

        responseMessage = transaction_pb2.TransactionMessage()
        try:
            responseMessage.ParseFromString(data)
        except BaseException:
            return
        try:
            messageLength = responseMessage.ByteSize()
            # Failed to parse data
            if messageLength == 0:
                return
            # Proto managed to parse but not fully correct... wait for more data
            if responseMessage.dataLength == 0:
                return
            # Parse message
            # TODO: Clean up the method used to import the share class
            class_ = getattr(shares_pb2, "Share" + str(responseMessage.shareId))
            share = class_()
            shareData = responseMessage.data[0:responseMessage.dataLength]
            share.ParseFromString(bytes(shareData))
            # logger.debug(f"Publishing model {responseMessage.shareId}")
            self.store.publishModel(responseMessage.shareId, share)
            # debug_ids = [11, 12, 13, 14]
            # if responseMessage.shareId in debug_ids:
            #     logger.debug(f"Recieved {responseMessage.shareId}")
            # Clear out the response buffer
            self.inBuffer = bytes()
            self.inSize = 0
        except BaseException:
            return
        except AttributeError:
            return

    def requestShare(self, shareId) -> None:
        if self.connected:
            outBuffer = self.requestMessageAsBytes(shareId)
            self.comms.send_message(outBuffer)

    def publishShare(self, shareId) -> None:
        if self.connected:
            outBuffer = self.publishMessageAsBytes(shareId)
            # print(outBuffer.hex('/'))
            self.comms.send_message(outBuffer)
            logger.debug(f"Published model {shareId} message length {len(outBuffer)}")

    def requestMessage(self, shareId) -> Any:
        requestMessage = transaction_pb2.TransactionMessage()
        requestMessage.token = uuid4().int >> 96
        requestMessage.action = transaction_pb2.TransactionMessage.REQUEST
        requestMessage.shareId = shareId
        requestMessage.dataLength = 1
        requestMessage.data = bytes(DATA_MAX_SIZE)
        return requestMessage

    def requestMessageAsBytes(self, shareId) -> bytes:
        return self.requestMessage(shareId).SerializeToString()

    def publishMessage(self, shareId) -> Any:
        publishMessage = transaction_pb2.TransactionMessage()
        publishMessage.token = uuid4().int >> 96
        publishMessage.action = transaction_pb2.TransactionMessage.PUBLISH
        publishMessage.shareId = shareId
        model = self.store.getModel(shareId)
        data = model.getData()
        if model is None or data is None:
            return bytes(0)
        data = data.SerializeToString()
        # Check that the data is DATA_MAX_SIZE bytes or less
        if len(data) > DATA_MAX_SIZE:
            return bytes(0)
        publishMessage.dataLength = len(data)
        publishMessage.data = data + bytes(DATA_MAX_SIZE - len(data))
        model.reset()  # Clear ready to set flag
        # print(publishMessage)
        # print(publishMessage.data.hex(" "))
        return publishMessage

    def publishMessageAsBytes(self, shareId) -> bytes:
        return self.publishMessage(shareId).SerializeToString()

    def requestAllSingleRequestModels(self) -> None:
        # Request single mode models
        for key in self.store.getModelIdsWithSingleRequest():
            self.requestShareSignal.emit(key)

    # Threading

    def start(self):
        logger.debug("Start thread")
        self.startCommunicating = True

    def run(self):
        logger.debug("Running")
        do_once = True
        # Request auto mode models
        while self.runnning:
            if self.startCommunicating:
                # Do once
                if do_once:
                    do_once = False
                    # Request single mode models
                    for key in self.store.getModelIdsWithSingleRequest():
                        # logger.debug(f"Attempting to request share {key}")
                        self.requestShareSignal.emit(key)
                        QThread().msleep(1)

                # Request Every x ms request from device (Updated in settings)
                now_1 = perf_counter()
                if (now_1 - self.requestPreviousTime) >= 1 / 3:
                    # logger.debug("Requesting all models from device")
                    for key in self.store.getModelIdsWithAutoRequest():
                        # Request Share to Model
                        # logger.debug(f"Requesting model {key}")
                        self.requestShareSignal.emit(key)
                    # end of request
                    self.requestPreviousTime = now_1

                # Publish Every 1hz
                now_2 = perf_counter()
                if (now_2 - self.publishPreviousTime) >= 1 / 1:
                    for key in self.store.getModelIdsReadyToSend():
                        # Publish Model to Share
                        self.publishShareSignal.emit(key)
                    # end of request
                    self.publishPreviousTime = now_2

            # Sleep thread to not lock cpu
            QThread().msleep(1)
        print("end")

    def stop(self):
        logger.debug("Stop thread")
        self.comms.stop()
        self.running = False
        self.startCommunicating = False
        self.disconnectDevice()
        self.finished.emit()
