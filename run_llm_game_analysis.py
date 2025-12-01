#run_llm_game_analysis.py

from analyzerChart import analyze_latest_games
from LLMChessAnalyzer import LLMChessAnalyzer

def main():
    username = "bielbart77"
    max_games = 1   # <<< analizujemy TYLKO jedną partię

    print(f"Fetching last game for user: {username}")

    results = analyze_latest_games(username=username, max_games=max_games)

    if not results:
        print("No games found.")
        return

    game = results[0]  # tylko pierwsza partia

    print(f"\nAnalyzing game {game.game_id} with LLM...\n")

    llm = LLMChessAnalyzer(
        mistral_snapshot_path="PATH/TO/YOUR/MISTRAL/SNAPSHOT"  # <-- ustaw swoją ścieżkę
    )

    summary = llm.summarize_game(game)

    print("\n======================== LLM SUMMARY ========================")
    print(summary)
    print("==============================================================\n")

    # save to file
    output_file = f"analysis/LLM_SINGLE_{game.game_id[:8]}.txt"

    import os
    os.makedirs("analysis", exist_ok=True)

    with open(output_file, "w", encoding="utf8") as f:
        f.write(summary)

    print(f"Summary saved to: {output_file}")


if __name__ == "__main__":
    main()
