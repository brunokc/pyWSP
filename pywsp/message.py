from dataclasses import dataclass
from inspect import signature
from typing import Any, Callable, Optional, Type, TypeVar, Union

T = TypeVar("T")

def message(cls: Optional[Type[T]] = None, *, type: str) -> Union[Callable[[Type[T]], Type[T]], Type[T]]:
    """Decorator used to tag data classes used with WebSocket."""
    def wrap(cls: Type[T]) -> Type[T]:
        # First, we wrap the class in dataclass since we want all that goodness
        cls = dataclass(cls)

        PYWSP_MESSAGE_ID = "_pywsp_message_id"
        PYWSP_MESSAGE_TYPE = "_pywsp_message_type"

        setattr(cls, PYWSP_MESSAGE_ID, -1)
        setattr(cls, PYWSP_MESSAGE_TYPE, type)
        if cls.__annotations__:
            cls.__annotations__[PYWSP_MESSAGE_ID] = "int"
            cls.__annotations__[PYWSP_MESSAGE_TYPE] = "str"
        return cls

    # See if we're being called as @message or @message().
    if cls is None:
        # We're called with parens.
        return wrap

    # We're called as @message without parens.
    return wrap(cls)


@dataclass
class WebSocketMessage:
    """Base class used when defining messages to be sent/received through the WebSocket."""
    id: int = -1
    type: str = ""


class WebSocketErrorMessage:
    error_code: int = 0
    error_message: str = ""
