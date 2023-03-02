from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .message import WebSocketMessage
    from .socket import WebSocket

class WebSocketCallback(ABC):
    @abstractmethod
    def on_new_connection(self, ws: "WebSocket") -> None:
        pass

    @abstractmethod
    async def on_new_message(self, ws: "WebSocket", message: "WebSocketMessage") -> None:
        pass
