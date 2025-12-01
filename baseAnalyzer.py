#baseAnalyzer.py
import io
import chess
import chess.pgn
from stockfish import Stockfish
from lichessAPI import LichessClient


class GameAnalysisResult:
    def __init__(self, game_id, white, black, result, mistakes):
        self.game_id = game_id
        self.white = white
        self.black = black
        self.result = result
        self.mistakes = mistakes

    def __str__(self):
        header = f"Game {self.game_id} — {self.white} vs {self.black} — Result: {self.result}"
        breakdown = "\n".join([f"  • {m}" for m in self.mistakes])
        return f"{header}\n{breakdown}\n"


class GameAnalyzer:
    def __init__(self, stockfish_path="stockfish.exe"):
        self.stockfish = Stockfish(stockfish_path)
        self.stockfish.update_engine_parameters({"Threads": 4, "Minimum Thinking Time": 30})

    def classify_mistake(self, cp_before, cp_after):
        delta = cp_after - cp_before
        if delta > -50:
            return None
        if delta > -150:
            return "Inaccuracy"
        if delta > -300:
            return "Mistake"
        return "Blunder"

    def analyze_game(self, pgn_text):
        game = chess.pgn.read_game(io.StringIO(pgn_text))
        board = game.board()

        white = game.headers.get("White")
        black = game.headers.get("Black")
        result = game.headers.get("Result", "?")

        mistakes = []
        prev_eval = 0

        for idx, move in enumerate(game.mainline_moves(), start=1):
            # SAN BEFORE pushing
            san = board.san(move)

            # Now push
            board.push(move)

            self.stockfish.set_fen_position(board.fen())
            eval_cp = self.stockfish.get_evaluation()

            if eval_cp["type"] == "cp":
                cp = eval_cp["value"]
            else:
                cp = -10000 if eval_cp["value"] < 0 else 10000

            mistake_type = self.classify_mistake(prev_eval, cp)
            if mistake_type:
                mistakes.append(f"{idx}. {san} — {mistake_type} (Δ = {cp - prev_eval})")

            prev_eval = cp


        return GameAnalysisResult("unknown", white, black, result, mistakes)


def analyze_latest_games(username="bielbart77", max_games=5):
    client = LichessClient()
    analyzer = GameAnalyzer()

    games = client.get_user_games(
        username=username,
        max_games=max_games,
        perf_type="rapid"
    )

    results = []
    for g in games:
        pgn_text = g.pgn       # <-- POPRAWIONE!
        game_id = g.game_id    # <-- z Twojego JSON
        result = analyzer.analyze_game(pgn_text)
        result.game_id = game_id
        results.append(result)

    return results


if __name__ == "__main__":
    print("Analyzing games...")

    results = analyze_latest_games(max_games=3)

    for r in results:
        print(r)
