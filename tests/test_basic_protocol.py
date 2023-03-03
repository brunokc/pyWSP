import asyncio
import logging
import pytest
from pywsp import *
from typing import List

WS_HOST = "127.0.0.1"
WS_PORT = 11111
WS_URL = "/api/websocket"

logging.basicConfig(level=logging.DEBUG, format="%(name)s: %(message)s")

_LOGGER = logging.getLogger(__name__)

@message(type="request")
class RequestMessage(WebSocketMessage):
    request: str

@message(type="response")
class ResponseMessage(WebSocketMessage):
    response: str


class Server(WebSocketCallback):
    def __init__(self, parent: "TestBasicProtocol") -> None:
        self._parent = parent
        self.messages: List[WebSocketMessage] = []
        self.new_message_event = asyncio.Event()
        self.new_connection_event = asyncio.Event()
        self.ws: WebSocket

    def on_new_connection(self, ws: WebSocket) -> None:
        self.ws = ws
        self.new_connection_event.set()

    async def on_new_message(self, ws: WebSocket, message: WebSocketMessage) -> None:
        self.messages.append(message)
        self.new_message_event.set()


class Client(WebSocketCallback):
    def __init__(self, parent: "TestBasicProtocol") -> None:
        self._parent = parent
        self.messages: List[WebSocketMessage] = []
        self.new_message_event = asyncio.Event()
        self.new_connection_event = asyncio.Event()

    def on_new_connection(self, ws: WebSocket) -> None:
        self.new_connection_event.set()

    async def on_new_message(self, ws: WebSocket, message: WebSocketMessage) -> None:
        self.messages.append(message)
        self.new_message_event.set()


class TestBasicProtocol:
    @pytest.mark.asyncio
    async def test_single_call(self) -> None:
        factory = MessageFactory()
        factory.register_message_types(RequestMessage)

        _LOGGER.debug("registering procotol")
        server = WebSocketServer(factory)
        server_callback = Server(self)
        server.register_callback(server_callback)
        server_task = asyncio.create_task(server.run(WS_HOST, WS_PORT, WS_URL), name="server")

        client = WebSocketClient(factory)
        client_callback = Client(self)
        client.register_callback(client_callback)
        client_task = asyncio.create_task(client.run(f"http://{WS_HOST}:{WS_PORT}{WS_URL}"), name="client")

        await server_callback.new_connection_event.wait()
        await client_callback.new_connection_event.wait()

        await client.send_message(RequestMessage(1, "this is a request"))
        await server_callback.new_message_event.wait()

        assert len(server_callback.messages) == 1

        msg = server_callback.messages[0]
        _LOGGER.debug("server message: %s", msg)
        assert msg.id == 1
        assert msg.request == "this is a request"

        await client.close()
        await client_task
        await server.close()
        await server_task
        await asyncio.sleep(0.25)

    @pytest.mark.asyncio
    async def test_request_response(self) -> None:
        factory = MessageFactory()
        factory.register_message_types(RequestMessage, ResponseMessage)

        _LOGGER.debug("registering procotol")
        server = WebSocketServer(factory)
        server_callback = Server(self)
        server.register_callback(server_callback)
        server_task = asyncio.create_task(server.run(WS_HOST, WS_PORT, WS_URL), name="server")

        client = WebSocketClient(factory)
        client_callback = Client(self)
        client.register_callback(client_callback)
        client_task = asyncio.create_task(client.run(f"http://{WS_HOST}:{WS_PORT}{WS_URL}"), name="client")

        await server_callback.new_connection_event.wait()
        await client_callback.new_connection_event.wait()

        # Request
        await client.send_message(RequestMessage(1, "this is a request"))
        await server_callback.new_message_event.wait()

        assert len(server_callback.messages) == 1

        msg = server_callback.messages[0]
        _LOGGER.debug("server message: %s", msg)
        assert msg.id == 1
        assert msg.request == "this is a request"

        # Response
        await server_callback.ws.send_message(ResponseMessage(2, "this is a response"))
        await client_callback.new_message_event.wait()

        assert len(client_callback.messages) == 1

        msg = client_callback.messages[0]
        _LOGGER.debug("client message: %s", msg)
        assert msg.id == 2
        assert msg.response == "this is a response"

        await client.close()
        await client_task
        await server.close()
        await server_task
        await asyncio.sleep(0.25)
