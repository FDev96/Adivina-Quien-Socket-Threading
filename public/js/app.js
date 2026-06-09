(() => {
  'use strict';

  const WS_PROTOCOL = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const WS_URL = `${WS_PROTOCOL}//${location.host}/ws`;

  // Mapas de valores de atributo para el formulario de preguntas
  const ATTR_VALUES = {
    paso_segunda_vuelta: [true, false],
    fue_alcalde:         [true, false],
    fue_presidente:      [true, false],
    role:                ['Presidente', 'Vicepresidente'],
    gender:              ['male', 'female'],
    hair_color:   ['black', 'brown', 'blonde', 'red', 'white', 'none'],
    hair_type:    ['straight', 'curly', 'bald'],
    eye_color:    ['brown', 'blue', 'green'],
    has_glasses:  [true, false],
    has_hat:      [true, false],
    has_beard:    [true, false],
    has_mustache: [true, false],
    skin_tone:    ['light', 'medium', 'dark'],
  };

  // ── Estado ──────────────────────────────────────────────────────────────────
  let socket = null;
  let myTurn = false;
  let board = [];
  let eliminated = new Set();   // nombres eliminados por este cliente
  let gameOver = false;

  // ── Referencias DOM ─────────────────────────────────────────────────────────────
  const $ = id => document.getElementById(id);
  const screenWaiting = $('screen-waiting');
  const screenGame    = $('screen-game');
  const boardEl        = $('board');
  const turnIndicator  = $('turn-indicator');
  const secretCharImg   = $('secret-char-img');
  const secretCharName  = $('secret-char-name');
  const secretCharRole  = $('secret-char-role');
  const secretCharParty = $('secret-char-party');
  const secretCharFact  = $('secret-char-fact');
  const attrSelect    = $('attr-select');
  const valSelect     = $('val-select');
  const btnAsk        = $('btn-ask');
  const guessSelect   = $('guess-select');
  const btnGuess      = $('btn-guess');
  const historyList   = $('history-list');
  const modalGameover = $('modal-gameover');
  const modalDisconn  = $('modal-disconnect');

  // ── WebSocket ──────────────────────────────────────────────────────────────
  function connect() {
    socket = new WebSocket(WS_URL);
    socket.addEventListener('message', e => handleMessage(JSON.parse(e.data)));
    socket.addEventListener('close', () => {
      if (!gameOver) showDisconnect();
    });
  }

  // ── Manejadores de mensajes ───────────────────────────────────────────────────────
  function handleMessage(msg) {
    switch (msg.type) {
      case 'waiting':     break; // ya está en pantalla de espera
      case 'game_start':  onGameStart(msg);        break;
      case 'question_result': onQuestionResult(msg); break;
      case 'opponent_asked':  onOpponentAsked(msg);  break;
      case 'game_over':       onGameOver(msg);        break;
      case 'opponent_disconnected': showDisconnect(); break;
    }
  }

  function onGameStart(msg) {
    board  = msg.board;
    myTurn = msg.your_turn;

    const secretChar = board.find(c => c.name === msg.your_secret) || { name: msg.your_secret };
    renderSecretChar(secretChar);
    renderBoard();
    populateGuessSelect();
    updateTurnUI();

    screenWaiting.classList.remove('active');
    screenGame.classList.add('active');
  }

  function renderSecretChar(char) {
    secretCharImg.src           = char.image || '';
    secretCharImg.alt           = char.name  || '';
    secretCharName.textContent  = char.name  || '—';
    secretCharRole.textContent  = char.role  || '';
    secretCharParty.textContent = char.party || '';
    secretCharFact.textContent  = char.fun_fact || '';
  }

  function onQuestionResult(msg) {
    addHistory(msg.question, msg.answer, false);
    myTurn = msg.your_turn;
    updateTurnUI();
  }

  function onOpponentAsked(msg) {
    addHistory(msg.question, null, true);
    myTurn = msg.your_turn;
    updateTurnUI();
  }

  function onGameOver(msg) {
    gameOver = true;
    const modal = $('modal-gameover');
    $('modal-icon').textContent  = msg.winner ? '🏆' : '💀';
    $('modal-title').textContent = msg.winner ? '¡Has Ganado!' : '¡Has Perdido!';
    $('modal-body').textContent  = 
      `El secreto del oponente era ${msg.opponent_secret}. El tuyo era ${msg.your_secret}.`;
    modal.classList.remove('hidden');
  }

  function showDisconnect() {
    gameOver = true;
    modalDisconn.classList.remove('hidden');
  }

  // ── Renderizado del tablero ────────────────────────────────────────────────────────
  function renderBoard() {
    boardEl.innerHTML = '';
    board.forEach(char => {
      const card = document.createElement('div');
      card.className = 'char-card' + (eliminated.has(char.name) ? ' eliminated' : '');
      card.dataset.name = char.name;
      
      // Crear el contenido con imagen y nombre
      const pos = char.photo_position || 'center top';
      card.innerHTML = `
        <div class="char-card-inner">
          <div class="char-front">
            <div class="char-avatar">
              <img src="${char.image}" alt="${char.name}" loading="lazy"
                   style="object-position:${pos}"
                   onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHZpZXdCb3g9IjAgMCAyMCAyMCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTIwIDEwSDBWMjAiIHN0cm9rZT0iIzAwQTAwMCIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+'">
            </div>
            <div class="char-name">${char.name}</div>
            <div class="char-fact" title="Dato curioso: ${char.fun_fact}">💡</div>
          </div>
          <div class="char-back">
            <div class="char-back-icon">✕</div>
            <div class="char-back-text">Eliminado</div>
          </div>
        </div>`;
      
      card.addEventListener('click', () => toggleCard(card, char.name));
      boardEl.appendChild(card);
    });
  }

  function toggleCard(card, name) {
    if (eliminated.has(name)) {
      eliminated.delete(name);
      card.classList.remove('eliminated');
    } else {
      eliminated.add(name);
      card.classList.add('eliminated');
    }
    send({ type: 'toggle', name });
  }

  // ── Selector de adivinanza ───────────────────────────────────────────────────────────
  function populateGuessSelect() {
    guessSelect.innerHTML = '<option value="">Seleccionar personaje…</option>';
    board.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.name;
      opt.textContent = c.name;
      guessSelect.appendChild(opt);
    });
  }

  // ── UI de turno ────────────────────────────────────────────────────────────────
  function updateTurnUI() {
    if (myTurn) {
      turnIndicator.textContent = 'Tu turno';
      turnIndicator.className   = 'turn-indicator your-turn';
      btnAsk.disabled   = false;
      btnGuess.disabled = false;
      updateAskButton();
    } else {
      turnIndicator.textContent = "Turno del oponente";
      turnIndicator.className   = 'turn-indicator opponent-turn';
      btnAsk.disabled   = true;
      btnGuess.disabled = true;
    }
  }

  function updateAskButton() {
    btnAsk.disabled = !(myTurn && attrSelect.value && valSelect.value !== '');
  }

  // ── Selectores de atributo/valor ──────────────────────────────────────────────────────
  attrSelect.addEventListener('change', () => {
    const attr = attrSelect.value;
    valSelect.innerHTML = '<option value="">Seleccionar valor…</option>';

    if (!attr) {
      valSelect.disabled = true;
      updateAskButton();
      return;
    }

    const values = ATTR_VALUES[attr] || [];
    values.forEach(v => {
      const opt = document.createElement('option');
      opt.value       = String(v);
      opt.textContent = getQuestionText(attr, v);
      valSelect.appendChild(opt);
    });
    valSelect.disabled = false;
    updateAskButton();
  });

  valSelect.addEventListener('change', updateAskButton);

  // ── Función para generar texto de preguntas divertidas ─────────────────────────────────
  function getQuestionText(attr, value) {
    const questions = {
      paso_segunda_vuelta: {
        true:  "¿Tu candidato/a NO se quemó en primera vuelta?",
        false: "¿Tu candidato/a se quemó en primera vuelta?",
      },
      fue_alcalde: {
        true:  "¿Tu candidato/a fue alcalde o alcaldesa?",
        false: "¿Tu candidato/a nunca fue alcalde ni alcaldesa?",
      },
      fue_presidente: {
        true:  "¿Tu candidato/a ha sido presidente/a de Colombia?",
        false: "¿Tu candidato/a nunca ha sido presidente/a de Colombia?",
      },
      role: {
        Presidente:     "¿Es candidato/a a Presidente?",
        Vicepresidente: "¿Es candidato/a a Vicepresidente?",
      },
      gender: {
        male:   "¿Es hombre?",
        female: "¿Es mujer?",
      },
      hair_color: {
        black:  "¿Tiene el pelo negro?",
        brown:  "¿Tiene el pelo café?",
        blonde: "¿Tiene el pelo rubio?",
        red:    "¿Tiene el pelo rojo?",
        white:  "¿Tiene el pelo blanco/canoso?",
        none:   "¿Está calvo/a?",
      },
      hair_type: {
        straight: "¿Tiene el pelo liso?",
        curly:    "¿Tiene el pelo rizado?",
        bald:     "¿Está completamente calvo/a?",
      },
      eye_color: {
        brown: "¿Tiene ojos cafés?",
        blue:  "¿Tiene ojos azules?",
        green: "¿Tiene ojos verdes?",
      },
      has_glasses: {
        true:  "¿Lleva gafas?",
        false: "¿No lleva gafas?",
      },
      has_hat: {
        true:  "¿Lleva sombrero o gorra?",
        false: "¿No lleva sombrero ni gorra?",
      },
      has_beard: {
        true:  "¿Tiene barba?",
        false: "¿No tiene barba?",
      },
      has_mustache: {
        true:  "¿Tiene bigote?",
        false: "¿No tiene bigote?",
      },
      skin_tone: {
        light:  "¿Tiene piel clara?",
        medium: "¿Tiene piel trigueña?",
        dark:   "¿Tiene piel oscura?",
      },
    };
    
    return questions[attr]?.[value] || `¿${value}?`;
  }

  // ── Botón de pregunta ─────────────────────────────────────────────────────────────
  btnAsk.addEventListener('click', () => {
    const attr = attrSelect.value;
    let   val  = valSelect.value;
    if (!attr || val === '') return;

    // convertir strings booleanos de vuelta a booleanos
    if (val === 'true')  val = true;
    if (val === 'false') val = false;

    // Generar pregunta divertida
    const questionText = getQuestionText(attr, val);
    
    send({ type: 'question', attribute: attr, value: val, question: questionText });
    btnAsk.disabled   = true;
    btnGuess.disabled = true;
  });

  // ── Botón de adivinanza ───────────────────────────────────────────────────────────
  btnGuess.addEventListener('click', () => {
    const name = guessSelect.value;
    if (!name) return;
    send({ type: 'guess', name });
    btnAsk.disabled   = true;
    btnGuess.disabled = true;
  });

  // ── Historial ────────────────────────────────────────────────────────────────
  function addHistory(question, answer, isOpponent) {
    const li = document.createElement('li');

    if (answer === null) {
      // el oponente preguntó, respuesta desconocida para nosotros
      li.className = 'history-item';
      li.innerHTML = `<strong>Oponente preguntó:</strong> ${question}`;
    } else {
      li.className = `history-item ${answer ? 'answer-yes' : 'answer-no'}`;
      const who = isOpponent ? 'Oponente' : 'Tú';
      const icon = answer ? '✅' : '❌';
      li.innerHTML = `<strong>${who}:</strong> ${question} <span class="answer-icon">${icon}</span>`;
    }

    historyList.prepend(li);
  }

  // ── Helpers ────────────────────────────────────────────────────────────────
  function send(data) {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(data));
    }
  }

  // ── Inicialización ───────────────────────────────────────────────────────────
  connect();
})();
