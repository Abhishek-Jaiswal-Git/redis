import socket
from typing import Any, Iterable, List, Optional, Tuple


CRLF = b"\r\n"


class RedisClient:
    """Tiny RESP client used to keep the demo dependency-free."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 6379,
        timeout: float = 5.0,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[int] = None,
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.username = username
        self.password = password
        self.database = database
        self._socket: Optional[socket.socket] = None
        self._buffer = b""

    def connect(self) -> None:
        if self._socket is not None:
            return
        self._socket = socket.create_connection((self.host, self.port), timeout=self.timeout)
        if self.password:
            if self.username:
                self.command("AUTH", self.username, self.password)
            else:
                self.command("AUTH", self.password)
        if self.database is not None:
            self.command("SELECT", self.database)

    def command(self, *args: Any) -> Any:
        self.connect()
        assert self._socket is not None
        self._socket.sendall(_encode_command(args))
        return self._read_reply()

    def close(self) -> None:
        if self._socket is not None:
            self._socket.close()
            self._socket = None

    def _read_reply(self) -> Any:
        while True:
            parsed = _parse_reply(self._buffer)
            if parsed is not None:
                value, offset = parsed
                self._buffer = self._buffer[offset:]
                return value

            assert self._socket is not None
            chunk = self._socket.recv(4096)
            if not chunk:
                raise ConnectionError("Redis connection closed")
            self._buffer += chunk
    def pipeline(self, commands: List[List[Any]]) -> List[Any]:
        """Sends multiple commands in one go and reads all replies."""
        if not commands:
            return []
        self.connect()
        assert self._socket is not None
        
        # Concatenate all encoded commands into one byte string
        all_encoded = b"".join([_encode_command(cmd) for cmd in commands])
        self._socket.sendall(all_encoded)
        
        # Read the corresponding number of replies
        return [self._read_reply() for _ in range(len(commands))]


def _encode_command(args: Iterable[Any]) -> bytes:
    pieces = []
    values = [str(arg).encode("utf-8") for arg in args]
    pieces.append(f"*{len(values)}\r\n".encode("ascii"))
    for value in values:
        pieces.append(f"${len(value)}\r\n".encode("ascii"))
        pieces.append(value)
        pieces.append(CRLF)
    return b"".join(pieces)


def _parse_reply(buffer: bytes, offset: int = 0) -> Optional[Tuple[Any, int]]:
    if offset >= len(buffer):
        return None

    prefix = buffer[offset : offset + 1]
    if prefix == b"+":
        return _parse_simple_string(buffer, offset)
    if prefix == b"-":
        line = _read_line(buffer, offset + 1)
        if line is None:
            return None
        message, next_offset = line
        raise RuntimeError(message.decode("utf-8"))
    if prefix == b":":
        line = _read_line(buffer, offset + 1)
        if line is None:
            return None
        value, next_offset = line
        return int(value), next_offset
    if prefix == b"$":
        return _parse_bulk_string(buffer, offset)
    if prefix == b"*":
        return _parse_array(buffer, offset)

    raise RuntimeError(f"Unsupported RESP prefix: {prefix!r}")


def _parse_simple_string(buffer: bytes, offset: int) -> Optional[Tuple[str, int]]:
    line = _read_line(buffer, offset + 1)
    if line is None:
        return None
    value, next_offset = line
    return value.decode("utf-8"), next_offset


def _parse_bulk_string(buffer: bytes, offset: int) -> Optional[Tuple[Optional[str], int]]:
    line = _read_line(buffer, offset + 1)
    if line is None:
        return None

    length, next_offset = line
    size = int(length)
    if size == -1:
        return None, next_offset

    end = next_offset + size
    if len(buffer) < end + 2:
        return None
    return buffer[next_offset:end].decode("utf-8"), end + 2


def _parse_array(buffer: bytes, offset: int) -> Optional[Tuple[List[Any], int]]:
    line = _read_line(buffer, offset + 1)
    if line is None:
        return None

    length, next_offset = line
    count = int(length)
    if count == -1:
        return None, next_offset

    values = []
    cursor = next_offset
    for _ in range(count):
        item = _parse_reply(buffer, cursor)
        if item is None:
            return None
        value, cursor = item
        values.append(value)
    return values, cursor


def _read_line(buffer: bytes, offset: int) -> Optional[Tuple[bytes, int]]:
    end = buffer.find(CRLF, offset)
    if end == -1:
        return None
    return buffer[offset:end], end + 2
