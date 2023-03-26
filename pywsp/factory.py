from dataclasses import dataclass
from typing import Any, Dict

from .exceptions import WebSocketUnsupportedMessageType

class MessageFactory:
    def __init__(self) -> None:
        self._registry: Dict[str, Any] = { }

    def register_message_types(self, *message_types: Any) -> None:
        for cls in message_types:
            type = getattr(cls, "_pywsp_message_type", None)
            if type is None:
                raise TypeError(f"class {cls} is not compliant with pyWSP -- "
                    "is it missing the @message decorator?")
            self._registry[type] = cls

    def create(self, message_type: str, **kwargs: Any) -> Any:
        if message_type not in self._registry:
            raise WebSocketUnsupportedMessageType(message_type)

        message_class = self._registry[message_type]
        return message_class(**kwargs)
