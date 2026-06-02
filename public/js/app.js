(() => {
  'use strict';

  const WS_URL = `ws://${location.hostname}:8765`;

  // Attribute value maps for the question form
  const ATTR_VALUES = {
    gender:       ['male', 'female'],
    hair_color:   ['black', 'brown', 'blonde', 'red', 'white', 'none'],
    hair_type:    ['straight', 'curly', 'bald'],
    eye_color:    ['brown', 'blue', 'green'],
    has_glasses:  [true, false],
    has_hat:      [true, false],
    has_beard:    [true, false],
    has_mustache: [true, false],
    skin_tone:    ['light', 'medium', 'dark'],
  };

  // Avatar emojis indexed by character name
  const AVATARS = {
    Alex:'🧑', Ana:'👩', Ben:'🧔', Clara:'👩‍🦰', David:'👨‍🦱', Elena:'👩‍🦳',
    Frank:'🧓', Grace:'👱‍♀️', Hector:'🧑‍🦲', Iris:'🤓', Jake:'👱', Karen:'👩‍🦳',
    Leo:'🧑‍🦲', Maya:'👩‍🦱', Nick:'🕵️', Olivia:'👸', Paul:'🧑‍🦰', Quinn:'👩',
    Ryan:'😏', Sofia:'👒', Tom:'🕶️', Uma:'🧕', Victor:'🥸', Wendy:'🧙‍♀️',
  };

  // ── State ──────────────────────────────────────────────────────────────────
  let socket = null;
  let myTurn = false;
  let board = [];
  let eliminated = new Set();   // names toggled off by this client
  let gameOver = false;

  // ── DOM refs ───────────────────────────────────────────────────────────────
  const $ = id => document.getElementById(id);
  const screenWaiting = $('screen-waiting');
  const screenGame    = $('screen-game');
  const boardEl       = $('board');
  const turnIndicator = $('turn-indicator');
  const secretName    = $('secret-name');
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

  // ── Message handlers ───────────────────────────────────────────────────────
  function handleMessage(msg) {
    switch (msg.type) {
      case 'waiting':     break; // already on waiting screen
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
    secretName.textContent = msg.your_secret;

    renderBoard();
    populateGuessSelect();
    updateTurnUI();

    screenWaiting.classList.remove('active');
    screenGame.classList.add('active');
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
    $('modal-title').textContent = msg.winner ? 'You Win!' : 'You Lose!';
    $('modal-body').textContent  =
      `Opponent's secret was ${msg.opponent_secret}. Yours was ${msg.your_secret}.`;
    modal.classList.remove('hidden');
  }

  function showDisconnect() {
    gameOver = true;
    modalDisconn.classList.remove('hidden');
  }

  // ── Board rendering ────────────────────────────────────────────────────────
  function renderBoard() {
    boardEl.innerHTML = '';
    board.forEach(char => {
      const card = document.createElement('div');
      card.className = 'char-card' + (eliminated.has(char.name) ? ' eliminated' : '');
      card.dataset.name = char.name;
      card.innerHTML = `
        <div class="char-card-inner">
          <div class="char-front">
            <div class="char-avatar">${AVATARS[char.name] || '🙂'}</div>
            <div class="char-name">${char.name}</div>
          </div>
          <div class="char-back">
            <div class="char-back-icon">✕</div>
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

  // ── Guess select ───────────────────────────────────────────────────────────
  function populateGuessSelect() {
    guessSelect.innerHTML = '<option value="">Select character…</option>';
    board.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.name;
      opt.textContent = c.name;
      guessSelect.appendChild(opt);
    });
  }

  // ── Turn UI ────────────────────────────────────────────────────────────────
  function updateTurnUI() {
    if (myTurn) {
      turnIndicator.textContent = 'Your turn';
      turnIndicator.className   = 'turn-indicator your-turn';
      btnAsk.disabled   = false;
      btnGuess.disabled = false;
      updateAskButton();
    } else {
      turnIndicator.textContent = "Opponent's turn";
      turnIndicator.className   = 'turn-indicator opponent-turn';
      btnAsk.disabled   = true;
      btnGuess.disabled = true;
    }
  }

  function updateAskButton() {
    btnAsk.disabled = !(myTurn && attrSelect.value && valSelect.value !== '');
  }

  // ── Attribute / value selects ──────────────────────────────────────────────
  attrSelect.addEventListener('change', () => {
    const attr = attrSelect.value;
    valSelect.innerHTML = '<option value="">Select value…</option>';

    if (!attr) {
      valSelect.disabled = true;
      updateAskButton();
      return;
    }

    const values = ATTR_VALUES[attr] || [];
    values.forEach(v => {
      const opt = document.createElement('option');
      opt.value       = String(v);
      opt.textContent = String(v);
      valSelect.appendChild(opt);
    });
    valSelect.disabled = false;
    updateAskButton();
  });

  valSelect.addEventListener('change', updateAskButton);

  // ── Ask button ─────────────────────────────────────────────────────────────
  btnAsk.addEventListener('click', () => {
    const attr = attrSelect.value;
    let   val  = valSelect.value;
    if (!attr || val === '') return;

    // convert boolean strings back to booleans
    if (val === 'true')  val = true;
    if (val === 'false') val = false;

    send({ type: 'question', attribute: attr, value: val });
    btnAsk.disabled   = true;
    btnGuess.disabled = true;
  });

  // ── Guess button ───────────────────────────────────────────────────────────
  btnGuess.addEventListener('click', () => {
    const name = guessSelect.value;
    if (!name) return;
    send({ type: 'guess', name });
    btnAsk.disabled   = true;
    btnGuess.disabled = true;
  });

  // ── History ────────────────────────────────────────────────────────────────
  function addHistory(question, answer, isOpponent) {
    const li = document.createElement('li');

    if (answer === null) {
      // opponent asked, answer unknown to us
      li.className = 'history-item';
      li.textContent = `Opponent asked: ${question}`;
    } else {
      li.className = `history-item ${answer ? 'answer-yes' : 'answer-no'}`;
      const who = isOpponent ? 'Opp' : 'You';
      li.textContent = `${who}: ${question} → ${answer ? 'Yes ✓' : 'No ✗'}`;
    }

    historyList.prepend(li);
  }

  // ── Helpers ────────────────────────────────────────────────────────────────
  function send(data) {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(data));
    }
  }

  // ── Init ───────────────────────────────────────────────────────────────────
  connect();
})();
