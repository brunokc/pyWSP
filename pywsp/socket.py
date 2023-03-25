from aiohttp import web, ClientSession, ClientWebSocketResponse, WSMsgType
import asyncio
from dataclasses import asdict
import logging
from typing import Any, Dict, NamedTuple, Optional, Tuple, Union

from .callback import WebSocketMessageCallback
from .const import *
from .exceptions import WebSocketInvalidMessage
from .factory import MessageFactory
from .message import WebSocketMessage

_LOGGER = logging.getLogger(__name__)

class PeerInfo(NamedTuple):
    ip: str
    port: int

class WebSocket:
    def __init__(
        self,
        factory: MessageFactory,
        *,
        wsr: Union[ClientWebSocketResponse, web.WebSocketResponse] = None,
        peer_info: Tuple[str, int] = None,
        session: ClientSession = None) -> None:

        self._callback: Optional[WebSocketMessageCallback] = None
        self._handle_message_task: asyncio.Task = None

        self._factory = factory
        self._wsr = wsr
        self._peer_info = peer_info
        self._session = session

    @property
    def peer_info(self) -> PeerInfo:
        return self._peer_info

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self.close()

    async def __anext__(self):
        async for msg in self._wsr:
            yield msg

    def register_callback(self, callback: WebSocketMessageCallback) -> None:
        self._callback = callback
        self.try_start_handle_message_task()

    async def close(self) -> None:
        if self._handle_message_task:
            self._handle_message_task.cancel()
        await self._wsr.close()
        if self._session:
            await self._session.close()

    async def send_message(self, message: WebSocketMessage) -> None:
        await self._wsr.send_json(asdict(message))

    def try_start_handle_message_task(self):
        # Only invoke in client scenarios, where we have a session defined.
        # For server created sockets, the server handles the message loop.
        assert self._handle_message_task is None
        if self._session is None or self._wsr is None or self._callback is None:
            return

        async def handle_websocket_messages():
            try:
                await self._handle_messages()
            except Exception as e:
                _LOGGER.error("closing websocket due to error handling message: %s (ws: %s)", e, self)
                await self.close()
            finally:
                pass

            _LOGGER.info("connection closed")

        self._handle_message_task = asyncio.create_task(
            handle_websocket_messages(),
            name="WebSocket_message_loop")

    async def _handle_messages(self) -> None:
        async for msg in self._wsr:
            _LOGGER.debug("new message %s", msg.__repr__())

            if msg.type == WSMsgType.TEXT:
                await self._dispatch_callback(msg.json())
            elif msg.type == WSMsgType.BINARY:
                await self._dispatch_callback(msg.data)
            elif msg.type == WSMsgType.ERROR:
                _LOGGER.error("error %s", self._wsr.exception())

    async def _dispatch_callback(self, data: Dict[str, Any]) -> None:
        if MESSAGE_ID not in data:
            _LOGGER.error("invalid message received (missing 'id'). Discarding...")
            raise WebSocketInvalidMessage("missing required field 'id'")
        if MESSAGE_TYPE not in data:
            _LOGGER.error("invalid message received (missing 'type'). Discarding...")
            raise WebSocketInvalidMessage("missing required field 'type'")

        if self._callback:
            message_type: str = data[MESSAGE_TYPE]
            message = self._factory.create(message_type, **data)
            await self._callback.on_new_message(self, message)

    @staticmethod
    def _get_peer_info(wsr: ClientWebSocketResponse) -> Tuple[str, int]:
        client_ip = ""
        client_port = 0
        peername = wsr.get_extra_info("peername")
        if peername is not None:
            client_ip, client_port = peername
        return client_ip, client_port

    async def connect(self, url: str) -> None:
        if self._session is None:
            self._session = ClientSession()

        ws = None
        try:
            wsr = await self._session.ws_connect(url)
            _LOGGER.info("connected to %s", url)
            self._wsr = wsr
            self._peer_info = PeerInfo(*self._get_peer_info(wsr))
            self.try_start_handle_message_task()
        except:
            if ws is not None:
                await ws.close()
