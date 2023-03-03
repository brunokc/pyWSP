import aiohttp
from dataclasses import asdict
import logging
from typing import Tuple

from .callback import WebSocketCallback
from .factory import MessageFactory
from .message import WebSocketMessage
from .socket import WebSocket

_LOGGER = logging.getLogger(__name__)

class WebSocketClient:
    def __init__(self, factory: MessageFactory):
        self._message_factory = factory
        self._ws: WebSocket
        self._callback: WebSocketCallback

    def register_callback(self, callback: WebSocketCallback) -> None:
        self._callback = callback

    async def send_message(self, message: WebSocketMessage) -> None:
        await self._ws.send_message(message)

    async def close(self) -> None:
        await self._ws.close()

    def _get_peer_info(self, response: aiohttp.ClientWebSocketResponse) -> Tuple[str, int]:
        client_ip = ""
        client_port = 0
        peername = response.get_extra_info("peername")
        if peername is not None:
            client_ip, client_port = peername
        return client_ip, client_port

    async def run(self, url: str) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(url) as ws:
                _LOGGER.info("Connected to %s", url)
                server_info = self._get_peer_info(ws)
                self._ws = WebSocket(ws, server_info, self._callback, self._message_factory)
                await self._ws.handle_messages()
