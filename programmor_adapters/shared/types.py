from typing_extensions import TypedDict

ResponseType = TypedDict('ResponseType', {'deviceId': str, 'shareId': int, 'message': str})
