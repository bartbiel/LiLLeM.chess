import os
import re
import matplotlib.pyplot as plt




# ============================================================
#   HELPERS
# ============================================================

def ensure_plots_dir():
    """Creates the 'plots' directory if it does not already exist."""
    if not os.path.exists("plots"):
        os.makedirs("plots")


def safe_game_id(game_id):
    """Returns a safe filename-friendly version of game_id."""
    return re.sub(r'[^A-Za-z0-9_-]', '_', str(game_id))[:16]  # short & safe


# ============================================================
#   Δ VALUE EXTRACTOR
# ============================================================

def extract_delta(text):
    """
    Extracts Δ = -123 style numbers from mistake text.
    Returns 0 if not found to avoid crashes.
    """
    match = re.search(r"Δ\s*=\s*(-?\d+)", text)
    return int(match.group(1)) if match else 0


# ============================================================
#   TOP BLUNDERS RANKING
# ============================================================

def generate_top_blunders(results, top_n=10):
    """Creates a global TOP_BLUNDERS.txt ranking based on Δ values."""
    ensure_plots_dir()

    all_blunders = []

    for game in results:
        for entry in game.mistakes:
            if "Blunder" in entry:
                delta = abs(extract_delta(entry))
                all_blunders.append((delta, game.game_id, entry))

    # Sort by biggest Δ first
    all_blunders.sort(reverse=True, key=lambda x: x[0])

    output_file = "plots/TOP_BLUNDERS.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("=== TOP BLUNDERS (GLOBAL) ===\n\n")
        for delta, gid, msg in all_blunders[:top_n]:
            safe_id = safe_game_id(gid)
            f.write(f"{safe_id:16} | Δ={delta:4} | {msg}\n")


# ============================================================
#   ACCURACY PLOT
# ============================================================

def generate_accuracy_plot(results):
    """
    Generates a single line plot showing accuracy trend over all games.
    Requires each game to have .accuracy field.
    """
    ensure_plots_dir()

    try:
        accuracies = [g.accuracy for g in results]
    except AttributeError:
        print("[WARN] Some game objects do not have the 'accuracy' attribute — skipping accuracy plot.")
        return

    plt.figure(figsize=(10, 4))
    plt.plot(accuracies)
    plt.title("Accuracy Trend Across Games")
    plt.xlabel("Game Index")
    plt.ylabel("Accuracy (%)")
    plt.grid(True)

    plt.savefig("plots/ACCURACY_TREND.png")
    plt.close()


# ============================================================
#   CPL PLOTS PER GAME
# ============================================================

def generate_cpl_plots(results):
    """Generates a CPL plot for each game."""
    ensure_plots_dir()

    for game in results:
        if not hasattr(game, "cpl_list") or not game.cpl_list:
            print(f"[WARN] Game {game.game_id} has no cpl_list — skipping CPL plot.")
            continue

        safe_id = safe_game_id(game.game_id)
        filename = f"plots/CPL_{safe_id}.png"

        plt.figure(figsize=(10, 4))
        plt.plot(game.cpl_list)
        plt.title(f"CPL – {game.white} vs {game.black}")
        plt.xlabel("Move Number")
        plt.ylabel("Centipawn Loss")
        plt.grid(True)
        plt.savefig(filename)
        plt.close()



# ============================================================
#   MAIN ENTRY POINT
# ============================================================

def generate_plots(results):
    """
    Generates all statistical outputs:
      - CPL plot for each game
      - Global accuracy trend
      - TOP_BLUNDERS ranking file
    """
    generate_cpl_plots(results)
    generate_accuracy_plot(results)
    generate_top_blunders(results)
    if not os.path.exists("plots"):
        os.makedirs("plots")

    # CPL per game
    for r in results:
        safe_id = re.sub(r'[^A-Za-z0-9_-]', '_', r.game_id)
        filename = f"plots/CPL_{safe_id}.png"

        plt.figure(figsize=(10, 4))
        plt.plot(r.cpl_list)
        plt.title(f"CPL – {r.white} vs {r.black}")
        plt.xlabel("Move Number")
        plt.ylabel("Centipawn Eval")
        plt.grid(True)
        plt.savefig(filename)
        plt.close()

    # accuracy trend
    generate_accuracy_plot(results)

    # blunders ranking
    generate_top_blunders(results)

    # NEW: heatmaps
    from heatmap_generator import generate_all_heatmaps
    generate_all_heatmaps(results)


