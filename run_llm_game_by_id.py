import os
import sys
import io
import json
import requests
import chess.pgn
from dotenv import load_dotenv
from LLMChessAnalyzer import LLMChessAnalyzer

load_dotenv()


def fetch_last_game(username: str):
    """Fetch last game with PGN + FENs via Lichess API."""
    print(f"[INFO] Fetching last game for {username}...")

    url = f"https://lichess.org/api/games/user/{username}?max=1&pgnInJson=true"
    headers = {"Accept": "application/x-ndjson"}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch PGN (status {response.status_code}).")

    line = response.text.strip().split("\n")[0]
    game_json = json.loads(line)

    if "pgn" not in game_json:
        raise RuntimeError("PGN missing in Lichess response.")

    return {
        "pgn": game_json["pgn"],
        "fens": game_json.get("fens", []),
        "fen_final": game_json.get("fen", None),
        "id": game_json.get("id", None)
    }


def fetch_game_by_id(game_id: str):
    """Fetch PGN only."""
    print(f"[INFO] Fetching game {game_id}...")

    url = f"https://lichess.org/game/export/{game_id}?pgn=1"
    response = requests.get(url)

    if response.status_code != 200:
        raise RuntimeError(f"Game fetch failed (status {response.status_code}).")

    return {
        "pgn": response.text,
        "fens": None,
        "fen_final": None,
        "id": game_id
    }


def print_moves_from_pgn(pgn_text):
    """Prints game moves in classical chess notation (e.g., 1. e4 e5 2. Nf3 Nc6)."""
    pgn = io.StringIO(pgn_text)
    game = chess.pgn.read_game(pgn)
    if pgn is None or game is None:
        print("[ERROR] Could not parse PGN.")
        return

    moves = []
    board = game.board()

    move_number = 1
    pair = []

    for move in game.mainline_moves():
        san = board.san(move)
        board.push(move)
        pair.append(san)

        if len(pair) == 2:
            moves.append(f"{move_number}. {pair[0]} {pair[1]}")
            pair = []
            move_number += 1

    if len(pair) == 1:
        moves.append(f"{move_number}. {pair[0]}")

    print("\n=== MOVES ===")
    print(" ".join(moves))
    print("=============\n")


def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python run_llm_game_by_id.py last USERNAME")
        print("  python run_llm_game_by_id.py GAME_ID USERNAME")
        return

    mode = sys.argv[1]
    user = sys.argv[2]

    if mode == "last":
        game = fetch_last_game(user)
    else:
        game = fetch_game_by_id(mode)

    pgn_text = game["pgn"]

    # print moves in human-readable form
    print_moves_from_pgn(pgn_text)

    print("[INFO] Initializing LLM analyzer...")

    llm_model_path = os.getenv("MISTRAL_MODEL_PATH")
    if not llm_model_path:
        raise RuntimeError("MISTRAL_MODEL_PATH is not set in environment variables!")

    analyzer = LLMChessAnalyzer(
        model_path=llm_model_path,
        stockfish_path="stockfish.exe"
    )

    print("[INFO] Generating analysis...\n")

    result = analyzer.analyze_game(pgn_text, n_worst=2)

    print("\n=========== LLM ANALYSIS ===========\n")
    print(result["analysis"])

    print("\n=========== WORST MOVES (Stockfish) ===========")
    for num, san, loss in result["worst_moves"]:
        print(f"Move {num}: {san} (eval change: {loss})")


if __name__ == "__main__":
    main()
