#analyzer.py
import chess
import chess.pgn
import requests
from stockfish import Stockfish


# -------------------------------------------------------
# CPL CALCULATION
# -------------------------------------------------------

def convert_eval(e):
    if isinstance(e, dict) and "mate" in e:
        return 10000 if e["mate"] > 0 else -10000
    return e["cp"]

def calculate_cpl(eval_before, eval_after, turn):
    before = convert_eval(eval_before)
    after = convert_eval(eval_after)

    if turn == "white":
        return before - after
    else:
        return after - before


# -------------------------------------------------------
# CLIENT TO DOWNLOAD GAMES
# -------------------------------------------------------

class LichessClient:
    def __init__(self):
        self.session = requests.Session()

    def fetch_latest_games(self, username, max_games=5):
        url = f"https://lichess.org/api/games/user/{username}"
        params = {
            "max": max_games,
            "moves": True,
            "pgnInJson": True
        }

        resp = self.session.get(
            url,
            params=params,
            headers={"Accept": "application/x-ndjson"}
        )

        games = []
        for line in resp.text.splitlines():
            if not line.strip():
                continue
            data = line.strip()
            games.append(data)
        return games


# -------------------------------------------------------
# GAME ANALYZER
# -------------------------------------------------------

class GameAnalyzer:
    def __init__(self, stockfish_path="stockfish.exe"):
        self.stockfish = Stockfish(
            stockfish_path,
            parameters={
                "Threads": 2,
                "Minimum Thinking Time": 30,
                "Hash": 256
            }
        )

    def analyze_game(self, pgn_text):
        game = chess.pgn.read_game(io.StringIO(pgn_text))
        board = game.board()

        mistakes = []
        cpl_list = []  # <- do wykresu

        move_number = 1

        for move in game.mainline_moves():

            # eval before
            self.stockfish.set_fen_position(board.fen())
            eval_before = self.stockfish.get_evaluation()

            san = board.san(move)

            # apply move
            board.push(move)

            # eval after
            self.stockfish.set_fen_position(board.fen())
            eval_after = self.stockfish.get_evaluation()

            # delta eval
            before_cp = convert_eval(eval_before)
            after_cp = convert_eval(eval_after)
            delta = before_cp - after_cp if eval_before and eval_after else 0

            # CPL
            turn = "white" if (board.turn == chess.BLACK) else "black"
            cpl = calculate_cpl(eval_before, eval_after, turn)
            cpl_list.append(cpl)

            # classify mistake
            if abs(delta) >= 300:
                issue = "Blunder"
            elif abs(delta) >= 150:
                issue = "Mistake"
            elif abs(delta) >= 50:
                issue = "Inaccuracy"
            else:
                issue = None

            if issue:
                mistakes.append({
                    "move_number": move_number,
                    "san": san,
                    "type": issue,
                    "delta": delta,
                    "cpl": cpl
                })

            move_number += 1

        return mistakes, cpl_list, game


# -------------------------------------------------------
# EXTERNAL FUNCTION
# -------------------------------------------------------

def analyze_latest_games(username="bielbart77", max_games=5):
    client = LichessClient()
    analyzer = GameAnalyzer()

    raw_games = client.fetch_latest_games(username=username, max_games=max_games)

    all_results = []

    for g in raw_games:
        mistakes, cpl_list, game = analyzer.analyze_game(g)
        result = {
            "id": game.headers.get("Site", "unknown"),
            "white": game.headers.get("White", "?"),
            "black": game.headers.get("Black", "?"),
            "result": game.headers.get("Result", "?"),
            "mistakes": mistakes,
            "cpl": cpl_list
        }
        all_results.append(result)

    return all_results
