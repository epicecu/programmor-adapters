import asyncio
from socketio import AsyncServer
from aiohttp import web
from shared.api import API

#NOTE https://stackoverflow.com/questions/56970102/how-to-decorate-class-functions-with-flask-socketio-if-the-socketio-instance-is


class Endpoint():
    """Endpoint Interface
    """
    def __init__(self, loop: asyncio.AbstractEventLoop, api:API) -> None:
        self.loop = loop
        self.api = api

        
        sio: AsyncServer = AsyncServer(async_mode='aiohttp')
        app = web.Application()
        sio.attach(app)
        # set up aiohttp - like run_app, but non-blocking
        runner = web.AppRunner(app)
        loop.run_until_complete(runner.setup())
        site = web.TCPSite(runner)    
        loop.run_until_complete(site.start())


    def start(self) -> None:
        web

    def stop(self) -> None:
        """Stops the Endpoint application
        """
        raise NotImplementedError("Stop method not implemented")
