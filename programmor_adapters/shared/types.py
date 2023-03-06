from typing_extensions import TypedDict
from enum import Enum

ResponseType = TypedDict('ResponseType', {'deviceId': str, 'actionType': int, 'shareId': int, 'data': str})


class MessageType(Enum):
    COMMON = 1
    SHARE = 2
