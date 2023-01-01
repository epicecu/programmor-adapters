import asyncio
from aiohttp import web
from shared.api import API

#NOTE https://docs.aiohttp.org/en/stable/web_quickstart.html#organizing-handlers-in-classes


class RestNamespace():
    """REST Namespace
    """
    def __init__(self) -> None:
        pass

    def handle_get_data(self, request):
        pass