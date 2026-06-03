# Adivina Quién — Políticos Colombianos

Un juego multijugador **Adivina Quién** transformado para usar personajes de políticos colombianos reales, construido con sockets Python crudos y hilos, y un cliente HTML/JS vanilla que se comunica a través de un protocolo WebSocket implementado manualmente.

---

## Tech Stack

| Componente    | Tecnología                        |
|--------------|-----------------------------------|
| Servidor      | Python 3.10+ — `socket` + `threading` |
| Protocolo     | WebSocket sobre TCP crudo (sin librerías)  |
| Cliente       | HTML5 + CSS3 + JavaScript vanilla |
| Concurrencia  | `threading.Thread` + `threading.Lock` |
| Imágenes      | Wikipedia thumbnails (220px) |

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
              ├── Crea GameState (tablero + secretos)
              ├── Envía game_start a ambos jugadores
              └── Juego impulsado por eventos de ClientThread

HTTP Thread (separado)
  └── Sirve archivos /public/* (index.html, CSS, JS)

Nginx (proxy inverso)
  ├── Proxy WebSocket: /ws → app:8765
  ├── Proxy HTTP: / → app:8080
  └── Sirve archivos estáticos
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
├── websocket_handler.py   # Manual WebSocket: handshake, frame encode/decode
├── game_logic.py          # GameState, lógica de turnos, validación de respuestas
├── characters.py          # 33 políticos colombianos con imágenes y datos divertidos
├── requirements.txt       # Vacío — solo stdlib
├── public/
│   ├── index.html         # Interfaz del juego en español con imágenes de políticos
│   ├── css/style.css      # Estilo actualizado para tarjetas de imágenes
│   └── js/app.js          # Cliente WebSocket con renderizado de imágenes y preguntas divertidas
└── README.md
```

---

## Cómo Ejecutar

### Ejecución Local

```bash
# Iniciar el servidor
python server.py
```

Luego abrir **dos pestañas del navegador** en:

```
http://localhost:8080
```

Ambas pestañas se conectarán a `ws://localhost:8765`. El MatchManager las empareja automáticamente y el juego comienza.

### Múltiples partidas simultáneas

Abrir 4 pestañas — se forman dos partidas independientes. Cada `GameThread` está aislado; los hilos de diferentes partidas nunca comparten un `GameState`.

---

---

## Implementación WebSocket

El módulo `websocket_handler.py` implementa el protocolo WebSocket (RFC 6455) desde cero:

### Handshake

1. El servidor lee la petición HTTP `Upgrade: websocket`.
2. Extrae `Sec-WebSocket-Key` de los headers.
3. Calcula `Sec-WebSocket-Accept = base64(SHA-1(key + GUID))`.
4. Envía respuesta `101 Switching Protocols`.

```python
accept = base64.b64encode(
    hashlib.sha1((ws_key + GUID).encode()).digest()
).decode()
```

### Frame Format

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-------+-+-------------+-------------------------------+
|F|R|R|R| opcode|M| Payload len |    Extended payload length    |
|I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
|N|V|V|V|       |S|             |                               |
| |1|2|3|       |K|             |                               |
+-+-+-+-+-+-+-+-+-+-------+-+-------------+-------------------------------+
```

Los frames del cliente siempre están enmascarados; los del servidor no. El enmascaramiento/desenmascaramiento usa XOR con una clave de 4 bytes:

```python
payload = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))
```

---

## Protocolo de Comunicación

### Cliente → Servidor

```json
{ "type": "question", "attribute": "hair_color", "value": "rojo" }
{ "type": "guess",    "name": "Carlos" }
{ "type": "toggle",   "name": "Maria" }
```

### Servidor → Cliente

```json
{ "type": "waiting" }
{ "type": "game_start", "board": [...], "your_turn": true, "player_number": 1, "your_secret": "Alex" }
{ "type": "question_result", "question": "¿Tiene pelo rojo?", "answer": true, "your_turn": false }
{ "type": "opponent_asked",  "question": "¿Lleva gafas?", "your_turn": true }
{ "type": "game_over", "winner": true, "opponent_secret": "Ben", "your_secret": "Alex" }
{ "type": "opponent_disconnected" }
```

---

## Reglas del Juego

1. El servidor asigna el turno al Jugador 1 al inicio.
2. En tu turno puedes:
   - **Preguntar** — seleccionar atributo + valor; el servidor responde **Sí/No** basado en el personaje secreto del oponente.
   - **Adivinar** — nombrar un personaje; correcto → ganas, incorrecto → pierdes inmediatamente.
3. Después de una pregunta, el turno pasa al oponente.
4. Hacer clic en una carta del tablero la marca como eliminada (ayuda visual local).

---

## Personajes Colombianos

**33 políticos colombianos** con imágenes de Wikipedia, datos divertidos y información de partidos:

### Estructura de Personajes

Cada personaje incluye:

| Atributo    | Valores | Descripción |
|--------------|--------|-------------|
| `name`       | String | Nombre completo del político |
| `image`      | URL | Imagen de Wikipedia (220px) |
| `gender`     | male, female | Género |
| `hair_color` | black, brown, blonde, red, white, none | Color de pelo |
| `hair_type`  | straight, curly, bald | Tipo de pelo |
| `eye_color`  | brown, blue, green | Color de ojos |
| `has_glasses`| true, false | Lleva lentes |
| `has_hat`    | true, false | Lleva sombrero/gorra |
| `has_beard`  | true, false | Tiene barba |
| `has_mustache` | true, false | Tiene bigote |
| `skin_tone`  | light, medium, dark | Tono de piel |
| `fun_fact`   | String | Dato curioso divertido |
| `party`      | String | Partido político |

### Ejemplos de Personajes

- **Gustavo Petro** - Cantaba vallenatos en su juventud (Colombia Humana)
- **Iván Duque** - Tiene un MBA de Harvard (Centro Democrático)
- **Ángela María Orozco** - Primera alcaldesa de Bogotá (Liberal)
- **Rodolfo Hernández** - Exalcalde de Bucaramanga (Liga de Gobernantes)

### Preguntas Divertidas en Español

El sistema genera preguntas automáticamente con toques humorísticos:

- "¿Cantaba vallenatos en su juventud?" (referencia a Gustavo Petro)
- "¿Tiene un MBA de Harvard?" (referencia a Iván Duque)
- "¿Es una política mujer?" (género)
- "¿Tiene el pelo café?" (color de pelo)
- "¿Lleva lentes?" (accesorios)

---

## Interfaz en Español con Imágenes

La interfaz de usuario está completamente traducida al español con imágenes reales:

### Características de la Interfaz

- **Pantalla de espera**: "Esperando a un oponente…" con spinner animado
- **Tarjetas de personajes**: Imagen real + nombre + dato curioso (💡)
- **Botones**: "Preguntar", "Adivinar", "Jugar de Nuevo"
- **Indicador de turno**: "Tu turno" / "Turno del oponente"
- **Modal de fin**: "¡Has Ganado!" / "¡Has Perdido!"
- **Historial**: "Historial de Preguntas" con iconos ✅/❌

### Renderizado de Imágenes

- Las imágenes se cargan desde URLs de Wikipedia
- Manejo de errores con imagen SVG fallback
- Diseño responsive con `object-fit: cover`
- Tooltip con dato curioso al pasar el mouse sobre 💡

### Preguntas Dinámicas

El sistema genera preguntas en español basadas en los atributos:

```javascript
function getQuestionText(attr, value) {
  // Ejemplos:
  // "¿Es un político hombre?" (gender: male)
  // "¿Tiene el pelo café?" (hair_color: brown)
  // "¿Lleva lentes?" (has_glasses: true)
  // "¿Cantaba vallenatos en su juventud?" (fun_fact)
}
```

---

## Verificación

```bash
# 1. Iniciar el servidor
python server.py

# 2. Abrir dos pestañas del navegador en http://localhost:8080
# 3. El matchmaking ocurre automáticamente
# 4. Jugar una partida completa con personajes colombianos

# Para prueba de concurrencia: abrir 4 pestañas → dos partidas independientes
```

### Pruebas adicionales

- **Desconexión**: Cerrar una pestaña → el otro jugador debe ser notificado
- **Concurrencia**: 2+ partidas simultáneas sin interferencia
- **Carga de imágenes**: Verificar que todas las URLs de Wikipedia carguen correctamente
- **Preguntas divertidas**: Probar que las preguntas se generan correctamente en español

### Pruebas de Imágenes

- URLs rotas: El sistema muestra imagen SVG fallback
- Carga lenta: Imágenes con `loading="lazy"`
- Responsive: Se adaptan a diferentes tamaños de pantalla

---

## Despliegue

Para producción, el servidor puede ejecutarse directamente o tras un proxy inverso:

```bash
# Ejecutar directamente
python server.py
```

Para configurar tras un proxy inverso (Nginx, Apache, etc.):
- Proxy WebSocket: `ws://localhost:8765`
- Servir archivos estáticos: `/public`

## Cambos Realizados (Versión Colombianos)

### Transformación de Personajes
- ✅ **33 políticos colombianos** reemplazando personajes genéricos
- ✅ **Imágenes de Wikipedia** con thumbnails de 220px
- ✅ **Datos divertidos** (fun facts) para cada personaje
- ✅ **Información de partidos** políticos

### Actualización Frontend
- ✅ **Renderizado de imágenes** reemplazando emojis
- ✅ **CSS actualizado** para tarjetas de imágenes
- ✅ **Preguntas dinámicas** en español con toques humorísticos
- ✅ **Manejo de errores** con imágenes SVG fallback

### Mejoras de Juego
- ✅ **33 personajes** vs 24 originales (más variedad)
- ✅ **Contexto cultural** colombiano en preguntas
- ✅ **Interfaz más rica** con imágenes reales
- ✅ **Datos educativos** sobre políticos colombianos

### Compatibilidad
- ✅ **Backend sin cambios** - compatible con nueva estructura
- ✅ **Protocolo WebSocket** inalterado
- ✅ **Múltiples partidas** simultáneas soportadas

### NOTA: Docker y Nginx
- Los archivos Dockerfile, docker-compose.yml y nginx.conf fueron eliminados según solicitud
- El servidor funciona con su servidor HTTP integrado en el puerto 8080
- WebSocket funciona directamente en el puerto 8765
- Puede ser desplegado con cualquier proxy inverso en el futuro