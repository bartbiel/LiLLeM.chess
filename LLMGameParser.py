#LLMGameParser.py

# GameParser.py

from dataclasses import dataclass
from typing import List, Optional
import chess.pgn
from io import StringIO


@dataclass
class GameAnalysisResult:
    white: str
    black: str
    result: str
    moves: List[str]
    opening: Optional[str]
    pgn: str


class GameParser:
    """
    Prosty parser PGN → GameAnalysisResult
    Bez analizy, bez LLM, tylko czyste dane z partii.
    """

    def parse_game(self, pgn_text: str) -> GameAnalysisResult:
        """
        Parsuje PGN i wyciąga:
        - gracza białymi
        - gracza czarnymi
        - wynik
        - listę ruchów algebraicznych
        - nazwę otwarcia (jeśli jest w tagach)
        - pełny PGN
        """

        game = chess.pgn.read_game(StringIO(pgn_text))

        if game is None:
            raise ValueError("Nie udało się sparsować PGN.")

        white = game.headers.get("White", "?")
        black = game.headers.get("Black", "?")
        result = game.headers.get("Result", "*")
        opening = game.headers.get("Opening", None)

        # --- Pobieramy ruchy ---
        moves = []
        node = game

        while node.variations:
            next_node = node.variation(0)
            moves.append(next_node.san())
            node = next_node

        return GameAnalysisResult(
            white=white,
            black=black,
            result=result,
            moves=moves,
            opening=opening,
            pgn=pgn_text
        )
