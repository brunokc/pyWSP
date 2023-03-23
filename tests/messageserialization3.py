import sys
sys.path += ".."

from dataclasses import asdict, is_dataclass
import json
from typing import Any, List

from pywsp.message import message

class JsonSerializer(json.JSONEncoder):
    def default(self, obj: Any) -> str:
        # Since datetime derives from date, check for it first
        if is_dataclass(obj):
            return asdict(obj)
        return str(obj)

def default_serializer(obj: Any):
    # Since datetime derives from date, check for it first
    if is_dataclass(obj):
        return asdict(obj)


@message(type="foo")
class FooMessage:
    foo: str

@message(type="bar")
class BarMessage:
    bar: List[FooMessage]

id = 0
def serialize(obj):
    global id
    id += 1
    if obj._pywsp_message_id:
        obj._pywsp_message_id = id
        envelope = {
            "@id": obj._pywsp_message_id,
            "@type": obj._pywsp_message_type,
            "data": obj
        }
        print(f"envelope: {envelope}")
        print("json: ", json.dumps(envelope, indent=2, default=lambda x: asdict(x) if is_dataclass(x) else x))

foo = FooMessage("foostr")
print(f"Foo (id: {foo._pywsp_message_id}, type: {foo._pywsp_message_type}):")
print(asdict(foo))
# print(dir(foo))
serialize(foo)

bar = BarMessage([FooMessage("foostr2"), FooMessage("foostr3")])
print(f"Bar (id: {bar._pywsp_message_id}, type: {bar._pywsp_message_type}):")
print(asdict(bar))
# print(dir(bar))
serialize(bar)
