# run_llm_game_by_id.py

from pathlib import Path
import sys
import os
from dotenv import load_dotenv

from analyzerChart import GameAnalyzer
from lichessLLMAPI import LichessLLMAPI
from LLMChessAnalyzer import LLMChessAnalyzer

load_dotenv()


def get_last_game_id(api: LichessLLMAPI, username: str) -> str:
    """
    Pobiera ID ostatniej partii użytkownika z Lichess.
    """
    print(f"Pobieram ostatnią partię użytkownika: {username}...")

    ndjson = api.get_user_games(username, max_games=1)

    # NDJSON = każda linia to osobny JSON → bierzemy pierwszą
    first_line = ndjson.split("\n")[0].strip()

    if not first_line:
        raise RuntimeError(f"Brak partii dla użytkownika {username}")

    import json
    data = json.loads(first_line)

    game_id = data.get("id")
    if not game_id:
        raise RuntimeError("Nie znaleziono ID partii w odpowiedzi Lichess API")

    print(f"Znaleziono ostatnią partię o ID: {game_id}")
    return game_id


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python run_llm_game_by_id.py <game_id>")
        print("  python run_llm_game_by_id.py last <username>")
        sys.exit(1)

    arg1 = sys.argv[1]
    lichess_api_token = os.getenv("LICHESS_API_TOKEN")

    api = LichessLLMAPI(token=lichess_api_token)

    # TRYB 1:  last <username>
    if arg1 == "last":
        if len(sys.argv) < 3:
            print("Musisz podać nazwę użytkownika: python run_llm_game_by_id.py last <username>")
            sys.exit(1)

        username = sys.argv[2]
        game_id = get_last_game_id(api, username)

    # TRYB 2:  <game_id>
    else:
        game_id = arg1

    print(f"Downloading PGN for game {game_id}...")
    pgn = api.get_game_pgn(game_id)

    analyzer = GameAnalyzer()
    result = analyzer.analyze_game(pgn)

    from pathlib import Path
    llm_model_path = Path(os.getenv("MISTRAL_MODEL_PATH"))


    llm = LLMChessAnalyzer(
        mistral_snapshot_path=llm_model_path,
        device="cpu"  # lub "cuda"
    )

    print("\n===== GENERATING LLM ANALYSIS =====\n")
    summary = llm.summarize_game(result)
    print(summary)

    # zapis analizy do pliku
    output_file = f"LLM_{game_id}.txt"
    with open(output_file, "w", encoding="utf8") as f:
        f.write(summary)

    print(f"\nSaved analysis to {output_file}")


if __name__ == "__main__":
    main()
