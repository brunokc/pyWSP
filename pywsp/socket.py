from aiohttp import web, WSMsgType, ClientWebSocketResponse
from dataclasses import asdict
import logging
from typing import Any, Dict, Union

from .callback import WebSocketCallback
from .const import *
from .exceptions import WebSocketInvalidMessage
from .factory import MessageFactory
from .message import WebSocketMessage

_LOGGER = logging.getLogger(__name__)


class WebSocket:
    def __init__(
        self,
        ws: Union[ClientWebSocketResponse, web.WebSocketResponse],
        callback: WebSocketCallback,
        factory: MessageFactory) -> None:

        self._ws = ws
        # self.client_ip = client_ip
        # self.client_port = client_port
        self._callback = callback
        self._factory = factory

    # async def send_response(self, msg: WebSocketMessage, data: dict[str, Any]) -> None:
    #     message = WebSocketMessage(msg.id, msg.type, response=data)
    #     await self._ws.send_str(str(message))

    async def send_message(self, message: WebSocketMessage) -> None:
        await self._ws.send_json(asdict(message))

    async def close(self) -> None:
        await self._ws.close()

    async def handle_messages(self) -> None:
        self._callback.on_new_connection(self)

        async for msg in self._ws:
            _LOGGER.debug("new message %s", msg.__repr__())

            if msg.type == WSMsgType.TEXT:
                await self.dispatch_callback(msg.json())
            elif msg.type == WSMsgType.BINARY:
                await self.dispatch_callback(msg.data)
            elif msg.type == WSMsgType.ERROR:
                _LOGGER.debug("error %s", self._ws.exception())

    async def dispatch_callback(self, data: Dict[str, Any]) -> None:
        if MESSAGE_ID not in data:
            _LOGGER.error("invalid message received (missing 'id'). Discarding...")
            raise WebSocketInvalidMessage("missing required field 'id'")
        if MESSAGE_TYPE not in data:
            _LOGGER.error("invalid message received (missing 'type'). Discarding...")
            raise WebSocketInvalidMessage("missing required field 'type'")

        message_type: str = data[MESSAGE_TYPE]
        message = self._factory.create(message_type, **data)
        await self._callback.on_new_message(self, message)

    # async def raise_event(self, event_name: str, payload: Dict[str, Any]) -> None:
    #     event = {
    #         "name": event_name,
    #         "payload": payload
    #     }
    #     message = EventMessage(event)
    #     await self.send_message(message)
