from dataclasses import dataclass
from inspect import signature
from typing import Any, Callable, Optional, Type, TypeVar, Union

T = TypeVar("T")
Class = TypeVar("Class")

def message(cls: Optional[Type[T]] = None, *, type: str) -> Union[Callable[[Type[T]], Type[T]], Type[T]]:
    """Decorator used to tag data classes used with WebSocket."""
    def wrap(cls: Type[T]) -> Type[T]:
        # First, we wrap the class in dataclass since we want all that goodness
        cls = dataclass(cls)

        # Now, find the position of the 'type' argument, as we'll send it automatically to
        # dataclass's auto-generated __init__ function so derived classes don't have to.
        old_init = cls.__init__
        sig = signature(old_init)
        type_index = next(i for i, p in enumerate(sig.parameters.values()) if p.name == "type")
        # Subtract the "self" parameter
        type_index -= 1

        # The new __init__ won't need to include the type parameter
        def new_init(self: Type[T], *args: Any, **kwargs: Any) -> None:
            # If we have positional parameters, call the original init passing everything from the
            # original __init__ before the type parameter, followed by type itself, then the rest of
            # the positional parameters.
            # If keyword parameters were used, just add type to them.
            if len(args) > 0:
                new_args = [*args[0:type_index], type, *args[type_index:]]
                old_init(self, *new_args, **kwargs)
            else:
                kwargs.update({"type": type})
                old_init(self, **kwargs)

        cls.__init__ = new_init # type: ignore [assignment]
        setattr(cls, "_pywsp_message_type", type)
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
    id: int
    type: str
