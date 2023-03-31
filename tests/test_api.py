import asyncio
import logging
import pytest

from pywsp import *
from pywsp import debug
from typing import Any, List

WS_HOST = "127.0.0.1"
WS_PORT = 11112
WS_URL = "/api/websocket"

logging.basicConfig(level=logging.DEBUG, format="%(name)s: %(message)s")

_LOGGER = logging.getLogger(__name__)

@message(type="ping")
class PingMessage:
    request: str

@message(type="pong")
class PongMessage:
    response: str


class Server(WebSocketConnectionCallback, WebSocketMessageCallback):
    def __init__(self) -> None:
        self.messages: List[Any] = []
        self.new_message_event = asyncio.Event()
        self.new_connection_event = asyncio.Event()
        self.ws: WebSocket

    def on_new_connection(self, ws: WebSocket) -> None:
        _LOGGER.info("server: new connection: %s", ws)
        ws.register_callback(self)
        self.ws = ws
        self.new_connection_event.set()

    async def on_new_message(self, ws: WebSocket, message: Any) -> None:
        _LOGGER.info("server: new message: %s", message)
        assert isinstance(message, PingMessage)
        asyncio.create_task(ws.send_message(PongMessage("received: " + message.request)))
        # self.messages.append(message)
        # self.new_message_event.set()


class SimpleApiClient(WebSocketApiClient):
    def __init__(self, url):
        super().__init__(url)

    async def ping(self, request):
        return await self.api_call(PingMessage, PongMessage, request)


class SimpleApiServer(WebSocketApiServer):
    def __init__(self):
        # method_map = {
        #     PingMessage: self.ping
        # }
        super().__init__(WS_HOST, WS_PORT, WS_URL) #, method_map=method_map)

    @api(input=PingMessage, output=PongMessage)
    async def ping(self, request):
        return "received: " + request


class TestApis:
    @pytest.mark.asyncio
    async def test_simple_api(self):
        loop = asyncio.get_running_loop()
        # loop.set_debug(True)

        factory = MessageFactory()
        factory.register_message_types(PingMessage, PongMessage)

        _LOGGER.debug("registering procotol")
        server = WebSocketServer(factory)
        server_callback = Server()
        server.register_callback(server_callback)
        await server.start_listening(WS_HOST, WS_PORT, WS_URL)

        # loop.call_later(3, debug.dump_tasks, loop)

        api = SimpleApiClient(f"http://{WS_HOST}:{WS_PORT}{WS_URL}")
        request = "this is a test"
        pong = await api.ping(request)
        _LOGGER.debug("response: %s", pong)
        assert pong.response == "received: " + request
        await api.close()
        await server.close()
        await asyncio.sleep(0.25)

    @pytest.mark.asyncio
    async def test_simple_server_api(self):
        loop = asyncio.get_running_loop()

        server = SimpleApiServer()
        await server.start()

        api = SimpleApiClient(f"http://{WS_HOST}:{WS_PORT}{WS_URL}")
        request = "this is a test"
        pong = await api.ping(request)
        _LOGGER.debug("response: %s", pong)
        assert pong.response == "received: " + request
        await api.close()
        await server.close()
        await asyncio.sleep(0.25)
