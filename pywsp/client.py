import aiohttp
from dataclasses import asdict
import logging

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

    # async def _dispatch(self, ws, data) -> None:
    #     id = data["id"]
    #     action = data["action"]
    #     args = data["args"] if "args" in data else None
    #     response = data["response"] if "response" in data else None

        # print(f"Server (raw): {msg}")
        # print(f"WebSocketMessage: id={id}; action={action}")
        # if args is not None:
        #     print(f"  args: {jsonutils.dumps(args, indent=2)}")
        # if response is not None:
        #     print(f"  response: {jsonutils.dumps(response, indent=2)}")

        # if (action == "raiseEvent" and args is not None and args["event"] == "thermostatUpdated"
        #     and "payload" in args):

        #     thermostats = args["payload"]["thermostats"]
        #     await get_status(ws, thermostats)

    # async def _handle_connection(self, ws) -> None:
    #     _LOGGER.debug("waiting for messages...")
    #     async for msg in ws:
    #         if msg.type == aiohttp.WSMsgType.TEXT:
    #             await self._dispatch(ws, msg.data)
    #         elif msg.type == aiohttp.WSMsgType.BINARY:
    #             #self.handle_request(msg.data)
    #             pass
    #         elif msg.type == aiohttp.WSMsgType.ERROR:
    #             break

    async def run(self, url: str) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(url) as ws:
                _LOGGER.info("Connected to %s", url)
                self._ws = WebSocket(ws, self._callback, self._message_factory)
                await self._ws.handle_messages()
