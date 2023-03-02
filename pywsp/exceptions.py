
class WebSocketException(Exception):
    """WebSocketException"""

class WebSocketInvalidMessage(WebSocketException):
    """Invalid message received"""
    def __init__(self, message: str):
        self._message = message

class WebSocketUnsupportedMessageType(WebSocketException):
    """Unsupported message type."""
    def __init__(self, message_type: str):
        self.message_type = message_type
