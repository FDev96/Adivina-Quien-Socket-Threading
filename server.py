import socket
import threading
import json
import os
import mimetypes
from game_logic import GameState
from characters import CHARACTERS
import websocket_handler as ws

HOST = "0.0.0.0"
WS_PORT = 8765
HTTP_PORT = 8080
STATIC_DIR = os.path.join(os.path.dirname(__file__), "public")


# ---------------------------------------------------------------------------
# MatchManager — thread-safe waiting queue
# ---------------------------------------------------------------------------

class MatchManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._queue: list["ClientThread"] = []

    def register(self, client: "ClientThread") -> tuple["ClientThread", "ClientThread"] | None:
        with self._lock:
            self._queue.append(client)
            if len(self._queue) >= 2:
                p1 = self._queue.pop(0)
                p2 = self._queue.pop(0)
                return p1, p2
        return None


match_manager = MatchManager()


# ---------------------------------------------------------------------------
# GameThread — runs one complete match
# ---------------------------------------------------------------------------

class GameThread(threading.Thread):
    def __init__(self, p1: "ClientThread", p2: "ClientThread"):
        super().__init__(daemon=True)
        self.p1 = p1
        self.p2 = p2

    def run(self):
        p1, p2 = self.p1, self.p2
        state = GameState(p1.player_id, p2.player_id)
        p1.game = state
        p2.game = state

        board_data = CHARACTERS

        p1.send({"type": "game_start", "board": board_data, "your_turn": True,  "player_number": 1, "your_secret": state.secrets[p1.player_id]})
        p2.send({"type": "game_start", "board": board_data, "your_turn": False, "player_number": 2, "your_secret": state.secrets[p2.player_id]})

        # The game is event-driven from here; ClientThreads call back into the
        # game state and notify both players directly.


# ---------------------------------------------------------------------------
# ClientThread — one thread per WebSocket connection
# ---------------------------------------------------------------------------

class ClientThread(threading.Thread):
    _id_counter = 0
    _id_lock = threading.Lock()

    def __init__(self, sock: socket.socket, addr):
        super().__init__(daemon=True)
        with ClientThread._id_lock:
            ClientThread._id_counter += 1
            self.player_id = f"Player{ClientThread._id_counter}"
        self.sock = sock
        self.addr = addr
        self.game: GameState | None = None
        self._partner: "ClientThread | None" = None

    def run(self):
        if not ws.perform_handshake(self.sock):
            self.sock.close()
            return

        self.send({"type": "waiting"})
        pair = match_manager.register(self)
        if pair:
            p1, p2 = pair
            p1._partner = p2
            p2._partner = p1
            gt = GameThread(p1, p2)
            gt.start()

        self._message_loop()

    def _message_loop(self):
        while True:
            raw = ws.recv_frame(self.sock)
            if raw is None:
                self._handle_disconnect()
                break
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            self._handle_message(msg)

    def _handle_message(self, msg: dict):
        state = self.game
        if state is None or state.is_over():
            return

        mtype = msg.get("type")

        if mtype == "question":
            if not state.is_turn(self.player_id):
                self.send({"type": "error", "message": "Not your turn"})
                return
            attr = msg.get("attribute", "")
            val = msg.get("value")
            # booleans arrive as JSON booleans
            if not state.is_valid_question(attr, val):
                self.send({"type": "error", "message": "Invalid question"})
                return
            answer = state.answer_question(self.player_id, attr, val)
            question_text = _format_question(attr, val)
            state.apply_question(self.player_id, attr, val, answer)
            self.send({"type": "question_result", "question": question_text, "answer": answer, "your_turn": False})
            if self._partner:
                self._partner.send({"type": "opponent_asked", "question": question_text, "your_turn": True})

        elif mtype == "guess":
            if not state.is_turn(self.player_id):
                self.send({"type": "error", "message": "Not your turn"})
                return
            name = msg.get("name", "")
            correct = state.apply_guess(self.player_id, name)
            partner = self._partner

            players = list(state.secrets.keys())
            opponent_id = players[1] if self.player_id == players[0] else players[0]

            if correct:
                self.send({"type": "game_over", "winner": True,  "opponent_secret": name,                    "your_secret": state.secrets[self.player_id]})
                if partner:
                    partner.send({"type": "game_over", "winner": False, "opponent_secret": state.secrets[self.player_id], "your_secret": state.secrets[partner.player_id]})
            else:
                self.send({"type": "game_over", "winner": False, "opponent_secret": state.secrets[opponent_id], "your_secret": state.secrets[self.player_id]})
                if partner:
                    partner.send({"type": "game_over", "winner": True,  "opponent_secret": state.secrets[self.player_id], "your_secret": state.secrets[partner.player_id]})

        elif mtype == "toggle":
            name = msg.get("name", "")
            if state:
                state.toggle_eliminated(self.player_id, name)

    def _handle_disconnect(self):
        if self._partner:
            self._partner.send({"type": "opponent_disconnected"})
        try:
            self.sock.close()
        except OSError:
            pass

    def send(self, data: dict) -> bool:
        return ws.send_frame(self.sock, json.dumps(data))


# ---------------------------------------------------------------------------
# HTTP server — serves static files from /public
# ---------------------------------------------------------------------------

def http_server():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, HTTP_PORT))
    srv.listen(10)
    print(f"[HTTP] Serving static files on http://localhost:{HTTP_PORT}")
    while True:
        conn, _ = srv.accept()
        threading.Thread(target=_handle_http, args=(conn,), daemon=True).start()


def _handle_http(conn: socket.socket):
    try:
        data = b""
        while b"\r\n\r\n" not in data:
            chunk = conn.recv(1024)
            if not chunk:
                return
            data += chunk

        first_line = data.decode("utf-8", errors="replace").split("\r\n")[0]
        parts = first_line.split()
        if len(parts) < 2:
            return

        path = parts[1].split("?")[0]
        if path == "/":
            path = "/index.html"

        file_path = os.path.normpath(os.path.join(STATIC_DIR, path.lstrip("/")))
        # prevent directory traversal
        if not file_path.startswith(os.path.abspath(STATIC_DIR) + os.sep):
            _send_http(conn, 403, "text/plain", b"Forbidden")
            return

        if not os.path.isfile(file_path):
            _send_http(conn, 404, "text/plain", b"Not Found")
            return

        mime, _ = mimetypes.guess_type(file_path)
        mime = mime or "application/octet-stream"
        with open(file_path, "rb") as f:
            body = f.read()
        _send_http(conn, 200, mime, body)
    except OSError:
        pass
    finally:
        conn.close()


def _send_http(conn: socket.socket, status: int, content_type: str, body: bytes):
    status_text = {200: "OK", 403: "Forbidden", 404: "Not Found"}.get(status, "Unknown")
    headers = (
        f"HTTP/1.1 {status} {status_text}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Connection: close\r\n"
        "\r\n"
    )
    conn.sendall(headers.encode() + body)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_question(attribute: str, value) -> str:
    from characters import get_question_templates
    templates = get_question_templates()
    if attribute in templates:
        key = value
        if isinstance(value, bool):
            key = value
        elif value == "true":
            key = True
        elif value == "false":
            key = False
        return templates[attribute].get(key, f"¿{attribute}: {value}?")
    return f"¿{attribute}: {value}?"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    http_thread = threading.Thread(target=http_server, daemon=True)
    http_thread.start()

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, WS_PORT))
    srv.listen(10)
    print(f"[WS]   WebSocket server on ws://localhost:{WS_PORT}")
    print(f"[INFO] Open http://localhost:{HTTP_PORT} in your browser")

    while True:
        conn, addr = srv.accept()
        ct = ClientThread(conn, addr)
        ct.start()


if __name__ == "__main__":
    main()
