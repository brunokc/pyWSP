from dataclasses import dataclass
from typing import Any, Dict, Iterable, Tuple, Type

from .exceptions import WebSocketUnsupportedMessageType
from .message import WebSocketMessage

class MessageFactory:
    def __init__(self) -> None:
        self._registry: Dict[str, Type[WebSocketMessage]] = { }

    def register_message_types(self, *message_types: Type[WebSocketMessage]) -> None:
        for cls in message_types:
            type = getattr(cls, "_pywsp_message_type", None)
            if type is None:
                raise TypeError(f"class {cls} is not compliant -- is it missing the @message decorator?")
            self._registry[type] = cls

    def create(self, message_type: str, **kwargs: Any) -> WebSocketMessage:
        if message_type not in self._registry:
            raise WebSocketUnsupportedMessageType(message_type)

        message_class = self._registry[message_type]
        return message_class(**kwargs)
