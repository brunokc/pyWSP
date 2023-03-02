import sys
sys.path += ".."

from dataclasses import dataclass, asdict
from typing import List

def message(cls=None, *, type: str):
    def wrap(cls):
        # Tag class with the type so we will know how to serialize it
        setattr(cls, "type", type)
        return dataclass(cls)

    # See if we're being called as @dataclass or @dataclass().
    if cls is None:
        # We're called with parens.
        return wrap

    # We're called as @dataclass without parens.
    return wrap(cls)


@dataclass
class WebSocketMessage:
    id: int
    type: str

    def __init__(self, id):
        self.id = id
        self.type = self.__class__.type


@message(type="foo")
class FooMessage(WebSocketMessage):
    foo: str

@message(type="bar")
class BarMessage(WebSocketMessage):
    bar: List[FooMessage]


foo = FooMessage(1, "foo1")
print("Foo:")
print(asdict(foo))

bar = BarMessage(2, "bar", [FooMessage(2, "foo2"), FooMessage(3, "foo3")])
print("Bar:")
print(asdict(bar))
