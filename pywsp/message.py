from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union

from .const import MESSAGE_ID, MESSAGE_TYPE, PYWSP_MESSAGE_ID, PYWSP_MESSAGE_TYPE
from .factory import MessageFactory

@dataclass
class WebSocketErrorMessage:
    error_code: int = 0
    error_message: str = ""

T = TypeVar("T")

def message(cls: Optional[Type[T]] = None, *, type: str) -> Union[Callable[[Type[T]], Type[T]], Type[T]]:
    """Decorator used to tag message classes (dataclasses) used with WebSocket."""
    def wrap(cls: Type[T]) -> Type[T]:
        # First, we wrap the class in dataclass since we want all that goodness
        cls = dataclass(cls)

        setattr(cls, PYWSP_MESSAGE_ID, -1)
        setattr(cls, PYWSP_MESSAGE_TYPE, type)
        if cls.__annotations__:
            cls.__annotations__.update({
                PYWSP_MESSAGE_ID: "int",
                PYWSP_MESSAGE_TYPE: "str"
            })
        return cls

    # See if we're being called as @message or @message().
    if cls is None:
        # We're called with parens.
        return wrap

    # We're called as @message without parens.
    return wrap(cls)


def deserialize_message(
        message_payload: Dict[str, Any],
        factory: MessageFactory) -> Any:

    assert MESSAGE_ID in message_payload
    assert MESSAGE_TYPE in message_payload
    message_type: str = message_payload[MESSAGE_TYPE]
    data = message_payload["data"]
    message = factory.create(message_type, **data)
    setattr(message, MESSAGE_ID, message_payload[MESSAGE_ID])
    setattr(message, MESSAGE_TYPE, message_payload[MESSAGE_TYPE])
    return message
