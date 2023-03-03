import logging
import pytest
from pywsp import *
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

    def test_use_decorator_as_function(self) -> None:
        class AlmostGoodMessage(WebSocketMessage):
            doesntmatter: str

        NowGoodMessage = message(AlmostGoodMessage, type="almost_good")

        # This should work now
        factory = MessageFactory()
        factory.register_message_types(NowGoodMessage)

        # nowgood = [NowGoodMessage(123, "blah")]

        nowgoodmsg = factory.create("almost_good", id=123, doesntmatter="blah")
        assert nowgoodmsg == NowGoodMessage(123, "blah")

    def test_exception_on_non_decorated_type(self) -> None:
        # Purposely missing the @message decorator
        class BadMessage(WebSocketMessage):
            doesntmatter: str

        factory = MessageFactory()
        with pytest.raises(TypeError):
            factory.register_message_types(BadMessage)

        # This should work now
        NowGoodMessage = message(BadMessage, type="bad")
        factory.register_message_types(NowGoodMessage)
