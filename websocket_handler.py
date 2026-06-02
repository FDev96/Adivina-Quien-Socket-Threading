import hashlib
import base64
import struct
import socket as _socket

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def perform_handshake(sock: _socket.socket) -> bool:
    """Parse HTTP Upgrade request and reply with WebSocket handshake."""
    data = b""
    while b"\r\n\r\n" not in data:
        chunk = sock.recv(1024)
        if not chunk:
            return False
        data += chunk

    headers = {}
    lines = data.decode("utf-8", errors="replace").split("\r\n")
    for line in lines[1:]:
        if ": " in line:
            key, _, value = line.partition(": ")
            headers[key.strip().lower()] = value.strip()

    ws_key = headers.get("sec-websocket-key", "")
    if not ws_key:
        return False

    accept = base64.b64encode(
        hashlib.sha1((ws_key + GUID).encode()).digest()
    ).decode()

    response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {accept}\r\n"
        "\r\n"
    )
    sock.sendall(response.encode())
    return True


def recv_frame(sock: _socket.socket) -> str | None:
    """Receive one WebSocket frame and return its text payload, or None on close/error."""
    try:
        while True:
            header = _recv_exact(sock, 2)
            if header is None:
                return None

            opcode = header[0] & 0x0F
            masked = (header[1] & 0x80) != 0
            payload_len = header[1] & 0x7F

            if opcode == 0x8:  # close
                return None
            if opcode == 0x9:  # ping → reply pong, then keep reading
                _send_frame(sock, b"", opcode=0xA)
                continue
            if opcode == 0xA:  # unsolicited pong — ignore, keep reading
                continue

            if payload_len == 126:
                ext = _recv_exact(sock, 2)
                if ext is None:
                    return None
                payload_len = struct.unpack(">H", ext)[0]
            elif payload_len == 127:
                ext = _recv_exact(sock, 8)
                if ext is None:
                    return None
                payload_len = struct.unpack(">Q", ext)[0]

            mask_key = b""
            if masked:
                mask_key = _recv_exact(sock, 4)
                if mask_key is None:
                    return None

            payload = _recv_exact(sock, payload_len)
            if payload is None:
                return None

            if masked:
                payload = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))

            return payload.decode("utf-8", errors="replace")
    except (OSError, ConnectionResetError):
        return None


def send_frame(sock: _socket.socket, message: str) -> bool:
    """Send a text WebSocket frame."""
    return _send_frame(sock, message.encode("utf-8"), opcode=0x1)


def send_close(sock: _socket.socket) -> None:
    """Send a WebSocket close frame."""
    _send_frame(sock, b"", opcode=0x8)


def _send_frame(sock: _socket.socket, payload: bytes, opcode: int) -> bool:
    length = len(payload)
    header = bytearray()
    header.append(0x80 | opcode)

    if length < 126:
        header.append(length)
    elif length < 65536:
        header.append(126)
        header += struct.pack(">H", length)
    else:
        header.append(127)
        header += struct.pack(">Q", length)

    try:
        sock.sendall(bytes(header) + payload)
        return True
    except (OSError, BrokenPipeError):
        return False


def _recv_exact(sock: _socket.socket, n: int) -> bytes | None:
    buf = b""
    while len(buf) < n:
        try:
            chunk = sock.recv(n - len(buf))
        except (OSError, ConnectionResetError):
            return None
        if not chunk:
            return None
        buf += chunk
    return buf
