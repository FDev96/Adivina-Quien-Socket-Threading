# Adivina Quién — Elecciones Colombia 2026

Juego multijugador **Adivina Quién** con los candidatos presidenciales y vicepresidenciales reales de las elecciones colombianas de 2026. Construido con sockets Python crudos y hilos, y un cliente HTML/JS vanilla que se comunica a través de un protocolo WebSocket implementado manualmente.

---

## Tech Stack

| Componente   | Tecnología                                |
|--------------|-------------------------------------------|
| Servidor     | Python 3.10+ — `socket` + `threading`     |
| Protocolo    | WebSocket sobre TCP crudo (RFC 6455)      |
| Cliente      | HTML5 + CSS3 + JavaScript vanilla         |
| Concurrencia | `threading.Thread` + `threading.Lock`     |
| Imágenes     | Wikipedia thumbnails (330px)              |

> **Sin dependencias externas.** El servidor completo funciona con la librería estándar de Python.

---

## Arquitectura

```
Main Thread
  └── socket.bind() → listen() → accept() loop
        ├── ClientThread (uno por conexión)
        │     ├── WebSocket handshake (manual SHA-1 + base64)
        │     ├── Se registra con MatchManager
        │     └── Bucle de mensajes (pregunta / adivinanza / toggle)
        ├── MatchManager (threading.Lock)
        │     └── Cuando hay 2 jugadores en cola → crea GameThread
        └── GameThread
              ├── Envía board completo (15 objetos con image, party, etc.)
              ├── Asigna personaje secreto a cada jugador
              └── Juego impulsado por eventos de ClientThread

HTTP Thread (separado)
  └── Sirve archivos /public/* (index.html, CSS, JS)
```

### Thread Safety

- `MatchManager` usa un único `threading.Lock` para proteger la cola de espera.
- `GameState` usa `threading.Lock` para transiciones de turno y actualizaciones de historial.
- Cada `ClientThread` tiene su propio socket — sin acceso compartido.

---

## File Structure

```
DYPFINAL/
├── server.py              # Servidor principal: socket, threading, HTTP handler
├── websocket_handler.py   # WebSocket manual: handshake, frame encode/decode
├── game_logic.py          # GameState, lógica de turnos, validación de respuestas
├── characters.py          # 15 candidatos 2026 con imágenes, atributos y preguntas
├── requirements.txt       # Vacío — solo stdlib
├── public/
│   ├── index.html         # Interfaz del juego
│   ├── css/style.css      # Dark theme glassmorphism, grid 5×3
│   └── js/app.js          # Cliente WebSocket, render de tablero y panel secreto
└── README.md
```

---

## Cómo Ejecutar

```bash
python server.py
```

Abrir **dos pestañas** en `http://localhost:8080`. El MatchManager las empareja automáticamente.

Para múltiples partidas: abrir 4 pestañas → se forman dos partidas independientes. Cada `GameThread` está aislado.

---

## Personajes — Candidatos Reales 2026

**15 figuras políticas colombianas** extraídas de las elecciones presidenciales del 31 de mayo de 2026. Las imágenes provienen de Wikipedia Commons (330px).

### Candidatos incluidos

| # | Nombre | Cargo | Partido | ¿Pasó 2ª vuelta? |
|---|--------|-------|---------|-----------------|
| 1 | Iván Cepeda | Presidente | Pacto Histórico | ✅ 40.9% |
| 2 | Claudia López | Presidente | Con Claudia, Imparables | ❌ |
| 3 | Abelardo de la Espriella | Presidente | Defensores de la Patria | ✅ 43.7% |
| 4 | Sergio Fajardo | Presidente | Dignidad & Compromiso | ❌ 4.25% |
| 5 | Paloma Valencia | Presidente | Centro Democrático | ❌ 6.92% |
| 6 | Roy Barreras | Presidente | La Fuerza | ❌ |
| 7 | Mauricio Lizcano | Presidente | Firme con Lizcano | ❌ |
| 8 | Santiago Botero | Presidente | Romper el Sistema | ❌ |
| 9 | Gustavo Petro | Presidente | Colombia Humana | — (no candidato) |
| 10 | Álvaro Uribe | Presidente | Centro Democrático | — (no candidato) |
| 11 | Aída Quilcué | Vicepresidente | Pacto Histórico | ✅ (fórmula Cepeda) |
| 12 | Juan Daniel Oviedo | Vicepresidente | Centro Democrático | ❌ |
| 13 | José Manuel Restrepo | Vicepresidente | Defensores de la Patria | ✅ (fórmula De la Espriella) |
| 14 | Edna Bonilla | Vicepresidente | Dignidad & Compromiso | ❌ |
| 15 | Martha Lucía Zamora | Vicepresidente | La Fuerza | ❌ |

### Estructura de cada personaje (`characters.py`)

```python
{
    "name":                "Iván Cepeda",
    "image":               "https://upload.wikimedia.org/...",  # Wikipedia 330px
    "photo_position":      "center top",   # CSS object-position por personaje
    "role":                "Presidente",   # Presidente | Vicepresidente
    "party":               "Pacto Histórico",
    "gender":              "male",
    "hair_color":          "black",        # black | brown | blonde | red | white | none
    "hair_type":           "straight",     # straight | curly | bald
    "eye_color":           "brown",        # brown | blue | green
    "has_glasses":         False,
    "has_hat":             False,
    "has_beard":           False,
    "has_mustache":        False,
    "skin_tone":           "medium",       # light | medium | dark
    "paso_segunda_vuelta": True,           # ¿No se quemó en primera vuelta?
    "fue_alcalde":         False,          # ¿Fue alcalde/alcaldesa?
    "fue_presidente":      False,          # ¿Ha sido presidente de Colombia?
    "fun_fact":            "..."
}
```

---

## Atributos y Preguntas

El juego soporta 13 atributos consultables. Las preguntas se generan desde `get_question_templates()` en `characters.py` y se usan en frontend y backend.

### Atributos físicos

| Atributo | Valores | Pregunta |
|----------|---------|---------|
| `gender` | male, female | "¿Es hombre/mujer?" |
| `hair_color` | black, brown, blonde, red, white, none | "¿Tiene el pelo negro/café/...?" |
| `hair_type` | straight, curly, bald | "¿Tiene el pelo liso/rizado?" |
| `eye_color` | brown, blue, green | "¿Tiene ojos cafés/azules/verdes?" |
| `has_glasses` | true, false | "¿Lleva gafas?" |
| `has_hat` | true, false | "¿Lleva sombrero o gorra?" |
| `has_beard` | true, false | "¿Tiene barba?" |
| `has_mustache` | true, false | "¿Tiene bigote?" |
| `skin_tone` | light, medium, dark | "¿Tiene piel clara/trigueña/oscura?" |

### Atributos políticos (divertidos)

| Atributo | Pregunta |
|----------|---------|
| `role` | "¿Es candidato/a a Presidente / Vicepresidente?" |
| `paso_segunda_vuelta` | "¿Tu candidato/a NO se quemó en primera vuelta?" |
| `fue_alcalde` | "¿Tu candidato/a fue alcalde o alcaldesa?" |
| `fue_presidente` | "¿Tu candidato/a ha sido presidente/a de Colombia?" |

---

## Interfaz

### Layout

- **Header sticky**: título + indicador de turno (pill animado).
- **Tablero (5×3)**: grilla simétrica que ocupa todo el alto del viewport. Las cards se auto-dimensionan al espacio disponible. El clic voltea la card (flip 3D) para marcarla como eliminada.
- **Panel lateral**: scroll independiente con tres secciones:
  1. **Tu personaje secreto** — foto 180px, nombre, badge de cargo (púrpura), badge de partido (cyan), dato curioso (💡).
  2. **Hacer una pregunta** — selector de atributo + valor + botón "Preguntar".
  3. **Hacer una adivinanza** — selector de personaje + botón "Adivinar!".
  4. **Historial de preguntas** — lista scrolleable con ✅/❌.

### Renderizado de imágenes

Cada personaje tiene un campo `photo_position` (CSS `object-position`) para centrar la cara correctamente en el recorte de la card. Si la URL falla, se muestra un SVG fallback.

```javascript
const pos = char.photo_position || 'center top';
card.innerHTML = `<img src="${char.image}" style="object-position:${pos}" ...>`;
```

---

## Implementación WebSocket

El módulo `websocket_handler.py` implementa RFC 6455 desde cero con solo stdlib.

### Handshake

```python
accept = base64.b64encode(
    hashlib.sha1((ws_key + GUID).encode()).digest()
).decode()
```

### Frame Format

```
 0 1 2 3 4 5 6 7 | 8 9 0 1 2 3 4 5 | 16 .. 31
 FIN + opcode    | MASK + len       | Payload
```

El cliente siempre enmascara frames; el servidor nunca. XOR con clave de 4 bytes:

```python
payload = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))
```

---

## Protocolo de Comunicación (JSON sobre WebSocket)

### Cliente → Servidor

```json
{ "type": "question", "attribute": "paso_segunda_vuelta", "value": true }
{ "type": "guess",    "name": "Claudia López" }
{ "type": "toggle",   "name": "Roy Barreras" }
```

### Servidor → Cliente

```json
{ "type": "waiting" }
{ "type": "game_start",
  "board": [{ "name": "...", "image": "...", "role": "...", "party": "...",
              "photo_position": "...", "gender": "...", ... }],
  "your_turn": true,
  "player_number": 1,
  "your_secret": "Sergio Fajardo" }
{ "type": "question_result", "question": "¿Tu candidato/a se quemó en primera vuelta?", "answer": true, "your_turn": false }
{ "type": "opponent_asked",  "question": "¿Es mujer?", "your_turn": true }
{ "type": "game_over", "winner": true, "opponent_secret": "Gustavo Petro", "your_secret": "Aída Quilcué" }
{ "type": "opponent_disconnected" }
```

> El board se envía como lista de objetos completos (no solo nombres) para que el cliente tenga todos los datos sin peticiones adicionales.

---

## Reglas del Juego

1. El servidor asigna el turno al **Jugador 1** al inicio.
2. En tu turno podés:
   - **Preguntar** — elegir atributo + valor; el servidor responde **Sí/No** comparando con el personaje secreto del oponente.
   - **Adivinar** — nombrar un personaje; si acertás ganás, si fallás perdés inmediatamente.
3. Después de una pregunta, el turno pasa al oponente.
4. Clic en una card del tablero la marca como eliminada (gestión local, no afecta al servidor).

---

## Verificación

```bash
# Iniciar el servidor
python server.py

# Abrir dos pestañas en http://localhost:8080
# El matchmaking es automático → jugar una partida completa

# Concurrencia: abrir 4 pestañas → dos partidas independientes
```

### Checklist de pruebas

- [ ] Matchmaking automático al abrir dos pestañas
- [ ] Panel "Tu personaje secreto" muestra foto, cargo y partido correctamente
- [ ] Preguntas políticas ("¿se quemó?", "¿fue alcalde?") responden correctamente
- [ ] Flip 3D al eliminar una card
- [ ] Modal de victoria/derrota con secretos revelados
- [ ] Notificación al desconectar oponente
- [ ] Dos partidas simultáneas sin interferencia

---

## Despliegue

```bash
python server.py
```

| Puerto | Uso |
|--------|-----|
| `8080` | HTTP — sirve archivos estáticos de `/public` |
| `8765` | WebSocket — protocolo del juego |

Para proxy inverso (Nginx, Caddy, etc.):
- `ws://localhost:8765` → WebSocket
- `http://localhost:8080` → estáticos
