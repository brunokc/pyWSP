
class WebSocketException(Exception):
    """WebSocketException"""

class WebSocketInvalidMessage(WebSocketException):
    """Invalid message received"""

class WebSocketUnsupportedMessageType(WebSocketException):
    """Unsupported message type."""
