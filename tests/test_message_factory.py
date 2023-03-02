import sys
sys.path += ".."

import logging
from pywsp import *
import pytest
from typing import List

logging.basicConfig(level=logging.DEBUG, format="%(name)s: %(message)s")

_LOGGER = logging.getLogger(__name__)

@message(type="foo")
class FooMessage(WebSocketMessage):
    foo: str

@message(type="bar")
class BarMessage(WebSocketMessage):
    bar: List[FooMessage]


class TestMessageFactory():
    def test_simple_message_serialization(self) -> None:
        factory = MessageFactory()
        factory.register_message_types(FooMessage)

        foomsg = factory.create("foo", id=123, foo="foo")
        assert foomsg == FooMessage(123, "foo")

    def test_nested_message_serialization(self) -> None:
        factory = MessageFactory()
        factory.register_message_types(BarMessage)

        foos = [FooMessage(1, "foo")]

        barmsg = factory.create("bar", id=123, bar=foos)
        assert barmsg == BarMessage(123, [FooMessage(1, "foo")])

    def test_exception_on_non_decorated_type(self) -> None:
        class BadMessage(WebSocketMessage):
            doestmatter: str

        factory = MessageFactory()
        with pytest.raises(TypeError):
            factory.register_message_types(BadMessage)
