import logging
import pytest
from pywsp import *
from typing import List

logging.basicConfig(level=logging.DEBUG, format="%(name)s: %(message)s")

_LOGGER = logging.getLogger(__name__)

@message(type="foo")
class FooMessage:
    foo: str

@message(type="bar")
class BarMessage:
    bar: List[FooMessage]


class TestMessageFactory():
    def test_simple_message_serialization(self) -> None:
        factory = MessageFactory()
        factory.register_message_types(FooMessage)

        foomsg = factory.create("foo", foo="foo")
        assert foomsg == FooMessage("foo")

    def test_nested_message_serialization(self) -> None:
        factory = MessageFactory()
        factory.register_message_types(BarMessage)

        foos = [FooMessage("foo")]

        barmsg = factory.create("bar", bar=foos)
        assert barmsg == BarMessage([FooMessage("foo")])

    def test_use_decorator_as_function(self) -> None:
        class AlmostGoodMessage:
            doesntmatter: str

        NowGoodMessage = message(AlmostGoodMessage, type="almost_good")

        # This should work now
        factory = MessageFactory()
        factory.register_message_types(NowGoodMessage)

        # nowgood = [NowGoodMessage(123, "blah")]

        nowgoodmsg = factory.create("almost_good", doesntmatter="blah")
        assert nowgoodmsg == NowGoodMessage("blah")

    def test_exception_on_non_decorated_type(self) -> None:
        # Purposely missing the @message decorator
        class BadMessage:
            doesntmatter: str

        factory = MessageFactory()
        with pytest.raises(TypeError):
            factory.register_message_types(BadMessage)

        # This should work now
        NowGoodMessage = message(BadMessage, type="bad")
        factory.register_message_types(NowGoodMessage)
