import sys
sys.path += ".."

from dataclasses import dataclass, asdict
from typing import Dict, List

from inspect import signature

from pywsp import *

# def message(cls=None, *, type: str):
#     """Decorator used to tag data classes used with WebSocket."""
#     def wrap(cls):
#         # First, we wrap the class in dataclass since we want all that goodness
#         cls = dataclass(cls)

#         # Now, find the position of the 'type' argument, as we'll send it automatically to
#         # dataclass's auto-generated __init__ function so derived classes don't have to.
#         old_init = cls.__init__
#         sig = signature(old_init)
#         type_index = next(i for i, p in enumerate(sig.parameters.values()) if p.name == "type")
#         # Subtract the "self" parameter
#         type_index -= 1

#         # The new __init__ won't need to include the type parameter
#         def new_init(self, *args, **kwargs):
#             print(f"args: {args}")
#             print(f"kwargs: {kwargs}")

#             # If we have positional parameters, call the original init passing everything from the
#             # original __init__ before the type parameter, followed by type itself, then the rest of
#             # the positional parameters.
#             # If keyword parameters were used, just add type to them.
#             if len(args) > 0:
#                 old_init(self, *args[0:type_index], type, *args[type_index:], **kwargs)
#             else:
#                 old_init(self, type=type, **kwargs)

#         cls.__init__ = new_init
#         return cls

#     # See if we're being called as @message or @message().
#     if cls is None:
#         # We're called with parens.
#         return wrap

#     # We're called as @message without parens.
#     return wrap(cls)



# @dataclass
# class WebSocketMessage:
#     id: int
##     type: str

@message(type="foo")
class FooMessage(WebSocketMessage):
    foo: str

print("=> Creating Foo with positional args")
foo = FooMessage(1, "foo1")
print("Foo:")
print(foo)
print(asdict(foo))

print("=> Creating Foo with keyword args")
foo = FooMessage(id=1, foo="foo1")
print("Foo:")
print(foo)
print(asdict(foo))

print("=> Creating Bar with positional args")
@message(type="bar")
class BarMessage(WebSocketMessage):
    bar: List[FooMessage]

bar = BarMessage(2, [FooMessage(2, "foo2"), FooMessage(3, "foo3")])
print("Bar:")
print(bar)
print(asdict(bar))

print("=> Creating Zoo with positional args")
@message(type="zoo")
class ZooMessage(WebSocketMessage):
    zoo: Dict[str, BarMessage]
    foo: FooMessage

zoo = ZooMessage(4,
    { "bar": BarMessage(5, [FooMessage(6, "foo6"), FooMessage(7, "foo7")]) },
    FooMessage(8, "foo8")
)
print("Zoo:")
print(zoo)
print(asdict(zoo))
