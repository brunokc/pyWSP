from aiohttp import web
from aiohttp.web import Request, StreamResponse
import logging
from typing import Any, Dict, List, Tuple

from .callback import WebSocketConnectionCallback
from .factory import MessageFactory
from .socket import WebSocket

_LOGGER = logging.getLogger(__name__)

class WebSocketServer:
    def __init__(self, factory: MessageFactory):
        self._callback: WebSocketConnectionCallback
        self._site: web.BaseSite

        self._factory = factory
        self.clients: List[WebSocket] = []

    def register_callback(self, callback: WebSocketConnectionCallback) -> None:
        self._callback = callback

    async def close(self) -> None:
        await self._site.stop()

    async def handle_binary(self, data: bytes) -> None:
        _LOGGER.debug("received binary payload")
        _LOGGER.debug(data)

    def get_peer_info(self, request: Request) -> Tuple[str, int]:
        client_ip = ""
        client_port = 0
        peername = None
        if request.transport:
            peername = request.transport.get_extra_info("peername")
        if peername is not None:
            client_ip, client_port = peername
        return client_ip, client_port

    async def websocket_handler(self, request: Request) -> StreamResponse:
        assert self._callback is not None

        client_info = self.get_peer_info(request)
        _LOGGER.info(f"connection from %s:%d", client_info[0], client_info[1])

        wsr = web.WebSocketResponse()
        await wsr.prepare(request)
        ws = WebSocket(self._factory, wsr=wsr, peer_info=client_info)

        self.clients.append(ws)
        self._callback.on_new_connection(ws)

        try:
            await ws._handle_messages()
        except Exception as e:
            _LOGGER.error("closing websocket due to error handling message: %s", e)
            await ws.close()
        finally:
            await self._callback.on_closing(ws)
            self.clients.remove(ws)

        _LOGGER.info("connection closed")

        return wsr

    async def start_listening(self, address: str, port: int, url: str) -> None:
        if self._callback is None:
            _LOGGER.error("No callback defined, canceling websocket")
            raise RuntimeError("Starting websocket without setting a callback")

        app = web.Application()
        app.router.add_get(url, self.websocket_handler)

        runner = web.AppRunner(app)
        await runner.setup()
        self._site = web.TCPSite(runner, address, port)
        await self._site.start()
        _LOGGER.info("serving on %s:%d", address, port)
