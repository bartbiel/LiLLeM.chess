# run_analysis.py
from baseAnalyzer import analyze_latest_games

def main():
    username = "bielbart77"
    print(f"Analysing latest games for {username} ...")
    results = analyze_latest_games(username=username, max_games=5)
    print("Done. Results:\n")
    for r in results:
        print(r)

if __name__ == "__main__":
    main()
