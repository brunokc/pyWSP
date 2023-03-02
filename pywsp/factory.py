from dataclasses import dataclass
from typing import Any, Dict, Iterable, Tuple, Type

from .message import WebSocketMessage

class MessageFactory:
    def __init__(self) -> None:
        self._registry: Dict[str, Type[WebSocketMessage]] = { }


    # def register_message_type(
    #     self, message_type: str, message_class: Type[WebSocketMessage]) -> None:

    #     self.register_message_types([(message_type, message_class)])


    def register_message_type(self, message_class: Type[WebSocketMessage]) -> None:
        self.register_message_types(message_class)


    def register_message_types(
        # self, message_types: Iterable[Type[WebSocketMessage]]) -> None:
        self, *message_types: Type[WebSocketMessage]) -> None:

        for cls in message_types:
            type = getattr(cls, "_pywsp_message_type")
            self._registry[type] = cls


    def create(self, message_type: str, **kwargs: Any) -> WebSocketMessage:
        if message_type not in self._registry:
            raise LookupError("unknown message type")

        factory = self._registry[message_type]
        return factory(**kwargs)
