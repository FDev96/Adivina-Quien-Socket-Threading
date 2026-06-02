# Guess Who — Multiplayer

A multiplayer **Guess Who** game built with raw Python sockets and threads, and a vanilla HTML/JS client communicating over a manually implemented WebSocket protocol.

---

## Tech Stack

| Component    | Technology                        |
|--------------|-----------------------------------|
| Server       | Python 3.10+ — `socket` + `threading` |
| Protocol     | WebSocket over raw TCP (no libs)  |
| Client       | HTML5 + CSS3 + JavaScript vanilla |
| Concurrency  | `threading.Thread` + `threading.Lock` |

> **No external dependencies.** The entire server runs on Python's standard library.

---

## Architecture

```
Main Thread
  └── socket.bind() → listen() → accept() loop
        ├── ClientThread (one per connection)
        │     ├── WebSocket handshake (manual SHA-1 + base64)
        │     ├── Registers with MatchManager
        │     └── Message loop (question / guess / toggle)
        ├── MatchManager (threading.Lock)
        │     └── When 2 players queued → spawns GameThread
        └── GameThread
              ├── Creates GameState (board + secrets)
              ├── Sends game_start to both players
              └── Game driven by ClientThread events

HTTP Thread (separate)
  └── Serves /public/* files (index.html, CSS, JS)
```

### Thread Safety

- `MatchManager` uses a single `threading.Lock` to protect the waiting queue.
- `GameState` uses `threading.Lock` for turn transitions and history updates.
- Each `ClientThread` owns its socket — no shared socket access.

---

## File Structure

```
DYPFINAL/
├── server.py              # Main server: socket, threading, HTTP handler
├── websocket_handler.py   # Manual WebSocket: handshake, frame encode/decode
├── game_logic.py          # GameState, turn logic, answer validation
├── characters.py          # 24 characters with attributes
├── requirements.txt       # Empty — stdlib only
├── public/
│   ├── index.html         # Game UI (waiting → playing → game over)
│   ├── css/style.css      # Dark glassmorphism theme
│   └── js/app.js          # WebSocket client, board rendering
└── README.md
```

---

## How to Run

```bash
python server.py
```

Then open **two browser tabs** at:

```
http://localhost:8080
```

Both tabs connect to `ws://localhost:8765`. The MatchManager pairs them automatically and the game starts.

### Multiple simultaneous games

Open 4 tabs — two games form independently. Each `GameThread` is isolated; threads from different games never share a `GameState`.

---

## WebSocket Implementation

The `websocket_handler.py` module implements the WebSocket protocol (RFC 6455) from scratch:

### Handshake

1. Server reads the HTTP `Upgrade: websocket` request.
2. Extracts `Sec-WebSocket-Key` from headers.
3. Computes `Sec-WebSocket-Accept = base64(SHA-1(key + GUID))`.
4. Sends `101 Switching Protocols` response.

```python
accept = base64.b64encode(
    hashlib.sha1((ws_key + GUID).encode()).digest()
).decode()
```

### Frame Format

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-------+-+-------------+-------------------------------+
|F|R|R|R| opcode|M| Payload len |    Extended payload length    |
|I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
|N|V|V|V|       |S|             |                               |
| |1|2|3|       |K|             |                               |
+-+-+-+-+-------+-+-------------+-------------------------------+
```

Client frames are always masked; server frames are unmasked. Masking/unmasking uses XOR with a 4-byte key:

```python
payload = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))
```

---

## Communication Protocol

### Client → Server

```json
{ "type": "question", "attribute": "hair_color", "value": "red" }
{ "type": "guess",    "name": "Carlos" }
{ "type": "toggle",   "name": "Maria" }
```

### Server → Client

```json
{ "type": "waiting" }
{ "type": "game_start", "board": [...], "your_turn": true, "player_number": 1, "your_secret": "Alex" }
{ "type": "question_result", "question": "Does he/she have red hair?", "answer": true, "your_turn": false }
{ "type": "opponent_asked",  "question": "Does he/she wear glasses?", "your_turn": true }
{ "type": "game_over", "winner": true, "opponent_secret": "Ben", "your_secret": "Alex" }
{ "type": "opponent_disconnected" }
```

---

## Game Rules

1. Server assigns turn to Player 1 at game start.
2. On your turn you can:
   - **Ask** — pick an attribute + value; server answers **Yes/No** based on the opponent's secret character.
   - **Guess** — name a character; correct → you win, wrong → you lose immediately.
3. After a question, the turn passes to the opponent.
4. Clicking a character card on the board toggles it as eliminated (local visual aid only).

---

## Characters

24 characters with these attributes:

| Attribute    | Values |
|--------------|--------|
| `gender`     | male, female |
| `hair_color` | black, brown, blonde, red, white, none |
| `hair_type`  | straight, curly, bald |
| `eye_color`  | brown, blue, green |
| `has_glasses`| true, false |
| `has_hat`    | true, false |
| `has_beard`  | true, false |
| `has_mustache` | true, false |
| `skin_tone`  | light, medium, dark |

---

## Verification

```bash
# 1. Start the server
python server.py

# 2. Open two browser tabs at http://localhost:8080
# 3. Matchmaking happens automatically
# 4. Play a full game

# For concurrency test: open 4 tabs → two independent games run in parallel
```
