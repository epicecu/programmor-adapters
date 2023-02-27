from typing_extensions import TypedDict

ResponseType = TypedDict('ResponseType',{'deviceId': str,'actionType': int,'shareId': int,'data': str})
