from aiohttp import web
from aiohttp.web import Request, StreamResponse
import logging
from typing import Any, Dict, List, Tuple

from .callback import WebSocketCallback
from .factory import MessageFactory
from .socket import WebSocket

_LOGGER = logging.getLogger(__name__)

class WebSocketServer:
    def __init__(self, factory: MessageFactory):
        self._callback: WebSocketCallback
        self._factory = factory
        self.clients: List[WebSocket] = []
        self._site: web.BaseSite

    def register_callback(self, callback: WebSocketCallback) -> None:
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

        client_ip, client_port = self.get_peer_info(request)
        _LOGGER.debug(f"connection from %s:%d", client_ip, client_port)

        wsr = web.WebSocketResponse()
        await wsr.prepare(request)
        ws = WebSocket(wsr, self._callback, self._factory)
        # ws = WebSocket(client_ip, client_port, self._callback, self._factory)

        self.clients.append(ws)
        try:
            await ws.handle_messages()
        finally:
            self.clients.remove(ws)

        _LOGGER.debug("connection closed")
        return wsr

    # async def raise_event(self, event: str, args: Dict[str, Any]) -> None:
    #     for client in self.clients:
    #         await client.raise_event(event, args)

    async def run(self, address: str, port: int, url: str) -> None:
        if self._callback is None:
            _LOGGER.debug("No callback defined, canceling websocket")
            raise RuntimeError("Starting websocket without setting a callback")

        app = web.Application()
        app.router.add_get(url, self.websocket_handler)

        runner = web.AppRunner(app)
        await runner.setup()
        self._site = web.TCPSite(runner, address, port)
        await self._site.start()
        _LOGGER.debug("serving on %s:%d", address, port)
