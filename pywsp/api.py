import asyncio
import inspect
import logging

from dataclasses import asdict
from functools import partial
from typing import Any, Dict

from .callback import WebSocketConnectionCallback, WebSocketMessageCallback
# from .exceptions import WebSocketUnsupportedMessageType
from .factory import MessageFactory
from .message import deserialize_message, WebSocketErrorMessage
from .server import WebSocketServer
from .socket import WebSocket

_LOGGER = logging.getLogger(__name__)

INPUT_MESSAGE_TYPE = "input_message_type"
OUTPUT_MESSAGE_TYPE = "output_message_type"

def get_class_from_method(func) -> bool:
    cls = func.__qualname__[:-1]
    if inspect.isclass(cls):
        return cls

def api(*, input, output):
    def wrap(func):
        setattr(func, INPUT_MESSAGE_TYPE, input)
        setattr(func, OUTPUT_MESSAGE_TYPE, output)
        return func
    return wrap

# class ApiCall:
#     def __init__(self, request_message_type, response_message_type):
#         self._request_message_type = request_message_type
#         self._response_message_type = response_message_type

#     async def __call__(self, socket, *args, **kwargs):
#         request = self._request_message_type(*args, *kwargs)
#         await socket.send_message(request)
#         response = await self._socket.receive_message()
#         if isinstance(response, WebSocketErrorMessage):
#             # TODO:
#             pass

#         return response


class WebSocketError(RuntimeError):
    pass


class WebSocketApiServer(WebSocketConnectionCallback, WebSocketMessageCallback):
    def __init__(
            self,
            address: str,
            port: int,
            url: str,
            *,
            # method_map: Dict[Any, Any],
            message_factory: MessageFactory = None) -> None:

        self._address = address
        self._port = port
        self._url = url

        self._message_factory = message_factory or MessageFactory()
        self._method_map = { }

        self._wss = WebSocketServer((self._message_factory))
        self._wss.register_callback(self)

        self._build_message_factory()

    def _build_message_factory(self):
        def filter_method(f):
            return (
                inspect.isfunction(f)
                and not f.__name__.startswith("__")
                and f.__qualname__.split(".")[-2] == self.__class__.__name__
            )

        methods = inspect.getmembers(self.__class__, filter_method)
        for method in [m[1] for m in methods]:
            _LOGGER.debug("examining method %s", method.__qualname__)
            input = getattr(method, INPUT_MESSAGE_TYPE, None)
            output = getattr(method, OUTPUT_MESSAGE_TYPE, None)
            if input is not None and output is not None:
                _LOGGER.debug(
                    "registering input=%s and output=%s for method %s",
                    input, output, method)
                self._message_factory.register_message_types(input, output)
                call = getattr(self, method.__name__, None)
                assert call is not None
                self._method_map[input] = call #partial(method, self)

    async def start(self) -> None:
        await self._wss.start_listening(self._address, self._port, self._url)

    async def close(self) -> None:
        await self._wss.close()

    def on_new_connection(self, ws: WebSocket) -> None:
        _LOGGER.debug("new connection with socket %s", ws)
        ws.register_callback(self)

    async def on_closing(self, ws: WebSocket) -> None:
        _LOGGER.debug("closing socket %s", ws)

    async def on_new_message(self, ws: WebSocket, message: Any) -> None:
        message_type = type(message)
        method = self._method_map.get(message_type, None)
        _LOGGER.debug("new message: %s; method: %s", message, method)

        if method is None:
            _LOGGER.error("unsupported message type '%s'", message_type.__name__)
            error = WebSocketErrorMessage(error_message=f"unsupported message type {message_type}")
            asyncio.get_running_loop().call_soon(ws.send_message(error))
            return

        args = asdict(message)
        result = await method(**args)
        _LOGGER.debug("result: %s", result)

        # Build response message
        outputClass = getattr(method, OUTPUT_MESSAGE_TYPE, None)
        assert outputClass is not None
        response = outputClass(result)
        # asyncio.get_running_loop().call_soon(ws.send_message, response)
        await ws.send_message(response)



class WebSocketApiClient(WebSocketMessageCallback):
    def __init__(self, url, *, message_factory=None):
        self._message_factory = message_factory or MessageFactory()
        self._url = url
        self._ws = WebSocket(self._message_factory)
        self._ws.register_callback(self)
        self._future = asyncio.Future()

    async def _ensure_connected(self):
        if not self._ws.connected():
            await self._ws.connect(self._url)

    async def on_new_message(self, ws: "WebSocket", message: Any) -> None:
        self._future.set_result(message)

    async def close(self):
        await self._ws.close()

    async def api_call(self, request_message_type, response_message_type, *args, **kwargs):
        await self._ensure_connected()

        self._message_factory.register_message_types(response_message_type)
        request = request_message_type(*args, *kwargs)

        await self._ws.send_message(request)
        # response_message = await self._ws.receive_message()
        response = await self._future
        # response = deserialize_message(response_message.json(), self._message_factory)

        if isinstance(response, WebSocketErrorMessage):
            raise WebSocketError(response)
        elif not isinstance(response, response_message_type):
            raise TypeError(f"unexpected response message type '{type(response)}'")

        # return asdict(response)
        return response
