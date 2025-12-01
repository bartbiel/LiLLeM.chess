# analyzerChart.py
import io
import chess
import chess.pgn
from stockfish import Stockfish
from lichessAPI import LichessClient


# ============================================================
#   DATA MODEL
# ============================================================
class GameAnalysisResult:
    def __init__(self, game_id, white, black, result, mistakes, cpl_list, pgn_game):
        self.game_id = self._normalize_gid(game_id)
        self.white = white
        self.black = black
        self.result = result
        self.mistakes = mistakes
        self.cpl_list = cpl_list
        self.pgn_game = pgn_game

        # computed fields
        self.avg_cpl = self.calculate_avg_cpl()
        self.count_inacc = sum("Inaccuracy" in m for m in mistakes)
        self.count_mist = sum("Mistake" in m for m in mistakes)
        self.count_blunder = sum("Blunder" in m for m in mistakes)
        self.accuracy = self.calculate_accuracy()

    def _normalize_gid(self, gid):
        if gid.startswith("https://"):
            gid = gid.split("/")[-1]
        return gid

    def calculate_avg_cpl(self):
        if not self.cpl_list:
            return 0
        return sum(abs(cp) for cp in self.cpl_list) / len(self.cpl_list)

    def calculate_accuracy(self):
        # simple but surprisingly stable model:
        return max(0, min(100, 100 - (self.avg_cpl / 30)))

    def __str__(self):
        header = f"Game {self.game_id} — {self.white} vs {self.black} — Result: {self.result}"
        stats = (
            f"    Average CPL: {self.avg_cpl:.1f}\n"
            f"    Accuracy: {self.accuracy:.1f}%\n"
            f"    Inaccuracies: {self.count_inacc}\n"
            f"    Mistakes: {self.count_mist}\n"
            f"    Blunders: {self.count_blunder}\n"
        )
        breakdown = "\n".join([f"  • {m}" for m in self.mistakes])
        return f"{header}\n{stats}{breakdown}\n"


# ============================================================
#   GAME ANALYZER
# ============================================================
class GameAnalyzer:
    def __init__(self, stockfish_path="stockfish.exe"):
        self.stockfish = Stockfish(stockfish_path)
        self.stockfish.update_engine_parameters({
            "Threads": 4,
            "Minimum Thinking Time": 30,
            "Skill Level": 20
        })

    # ---------- CLASSIFY MISTAKE ----------
    def classify_mistake(self, cp_before, cp_after):
        delta = cp_after - cp_before

        if delta > -50:
            return None
        if delta > -150:
            return "Inaccuracy"
        if delta > -300:
            return "Mistake"
        return "Blunder"

    # ---------- SAFE EVAL ----------
    def eval_position(self, board):
        """Safe evaluation with mate fallback."""
        self.stockfish.set_fen_position(board.fen())
        raw = self.stockfish.get_evaluation()

        if raw["type"] == "cp":
            return raw["value"]
        else:
            # Mate in X => convert to big cp
            return -10000 if raw["value"] < 0 else 10000

    # ---------- SAFE SAN ----------
    def safe_san(self, board, move):
        """Try SAN, fallback to UCI."""
        try:
            return board.san(move)
        except Exception:
            return move.uci()

    # ---------- ANALYZE FULL GAME ----------
    def analyze_game(self, pgn_text):
        game = chess.pgn.read_game(io.StringIO(pgn_text))
        board = game.board()

        white = game.headers.get("White", "?")
        black = game.headers.get("Black", "?")
        game_id = game.headers.get("Site", "Unknown")
        result = game.headers.get("Result", "?")

        mistakes = []
        prev_eval = 0
        cpl_list = []

        for idx, move in enumerate(game.mainline_moves(), start=1):
            san_before = self.safe_san(board, move)
            board.push(move)

            cp = self.eval_position(board)
            cpl_list.append(cp)

            delta = cp - prev_eval
            mistake_type = self.classify_mistake(prev_eval, cp)

            if mistake_type:
                mistakes.append(f"{idx}. {san_before} — {mistake_type} (Δ = {delta})")

            prev_eval = cp

        return GameAnalysisResult(
            game_id=game_id,
            white=white,
            black=black,
            result=result,
            mistakes=mistakes,
            cpl_list=cpl_list,
            pgn_game=game
        )


# ============================================================
#   FETCH + ANALYZE USER GAMES
# ============================================================
def analyze_latest_games(username="bielbart77", max_games=5, perf_type="rapid"):
    client = LichessClient()
    analyzer = GameAnalyzer()

    games = client.get_user_games(
        username=username,
        max_games=max_games,
        perf_type=perf_type
    )

    results = []
    for g in games:
        result = analyzer.analyze_game(g.pgn)
        results.append(result)

    return results
