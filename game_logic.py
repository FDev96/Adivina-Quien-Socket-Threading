import random
import threading
from characters import CHARACTERS, VALID_ATTRIBUTES, get_character


class GameState:
    def __init__(self, player1_name: str, player2_name: str):
        secrets = random.sample([c["name"] for c in CHARACTERS], 2)
        self.secrets = {player1_name: secrets[0], player2_name: secrets[1]}
        self.board = [c["name"] for c in CHARACTERS]
        self.eliminated = {player1_name: set(), player2_name: set()}
        self.history = []          # list of dicts visible to both players
        self.current_turn = player1_name
        self.winner: str | None = None
        self._lock = threading.Lock()

    def _opponent_of(self, player: str) -> str:
        players = list(self.secrets.keys())
        return players[1] if player == players[0] else players[0]

    def is_valid_question(self, attribute: str, value) -> bool:
        if attribute not in VALID_ATTRIBUTES:
            return False
        allowed = VALID_ATTRIBUTES[attribute]
        # normalize booleans sent as strings from JSON
        if isinstance(allowed[0], bool):
            if isinstance(value, str):
                if value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False
        return value in allowed

    def answer_question(self, asker: str, attribute: str, value) -> bool:
        """Return whether the OPPONENT's secret character has the given attribute."""
        opponent = self._opponent_of(asker)
        secret_char = get_character(self.secrets[opponent])
        char_value = secret_char[attribute]

        # normalize for bool comparison
        if isinstance(char_value, bool) and isinstance(value, str):
            value = value.lower() == "true"

        return char_value == value

    def apply_question(self, asker: str, attribute: str, value, answer: bool) -> None:
        with self._lock:
            self.history.append({
                "player": asker,
                "type": "question",
                "attribute": attribute,
                "value": value,
                "answer": answer,
            })
            self.current_turn = self._opponent_of(asker)

    def apply_guess(self, guesser: str, name: str) -> bool:
        """Return True if the guess is correct. Sets winner on correct guess."""
        opponent = self._opponent_of(guesser)
        correct = self.secrets[opponent] == name
        with self._lock:
            self.history.append({
                "player": guesser,
                "type": "guess",
                "name": name,
                "correct": correct,
            })
            if correct:
                self.winner = guesser
            else:
                # wrong guess → guesser loses immediately
                self.winner = opponent
        return correct

    def toggle_eliminated(self, player: str, name: str) -> None:
        with self._lock:
            if name in self.eliminated[player]:
                self.eliminated[player].discard(name)
            else:
                self.eliminated[player].add(name)

    def is_turn(self, player: str) -> bool:
        return self.current_turn == player

    def is_over(self) -> bool:
        return self.winner is not None
