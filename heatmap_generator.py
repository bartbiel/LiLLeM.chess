#heatmap_generator.py
import numpy as np
import matplotlib.pyplot as plt
import os
import chess

# ============================================================
#   HEATMAP HELPER — ensure plots/heatmaps folder exists
# ============================================================
def ensure_dir():
    if not os.path.exists("plots/heatmaps"):
        os.makedirs("plots/heatmaps")


# ============================================================
#   1) HEATMAP OF MOVE FREQUENCY PER SQUARE
# ============================================================
def heatmap_move_frequency(results):
    ensure_dir()

    freq = np.zeros((8, 8), dtype=int)

    for r in results:
        game = r.pgn_game
        board = game.board()
        for move in game.mainline_moves():
            square = move.to_square
            r_idx = 7 - chess.square_rank(square)
            c_idx = chess.square_file(square)
            freq[r_idx, c_idx] += 1
            board.push(move)

    plt.figure(figsize=(6, 6))
    plt.imshow(freq, cmap="hot", interpolation="nearest")
    plt.title("Move Frequency Heatmap")
    plt.colorbar(label="Moves to Square")
    plt.xticks(range(8), list("abcdefgh"))
    plt.yticks(range(8), list("87654321"))
    plt.savefig("plots/heatmaps/move_frequency.png")
    plt.close()


# ============================================================
#   2) HEATMAP OF BLUNDERS PER SQUARE
# ============================================================
def extract_square_from_mistake(msg):
    # msg looks like: "14. Nf3 — Blunder (Δ = -340)"
    import re
    match = re.search(r"^(\d+)\. ([A-Za-z0-9+=#]+)", msg)
    if not match:
        return None
    san = match.group(2)

    try:
        move = chess.Move.from_uci(san)
        return move.to_square
    except:
        return None


def heatmap_blunders(results):
    ensure_dir()

    freq = np.zeros((8, 8), dtype=int)

    for r in results:
        for msg in r.mistakes:
            if "Blunder" not in msg:
                continue

            # parse target square from SAN — this is tricky
            import re
            # SAN to UCI conversion (approx): extract last 2 letters
            match = re.search(r"([a-h][1-8])", msg)
            if not match:
                continue
            square_str = match.group(1)
            try:
                square = chess.parse_square(square_str)
            except:
                continue

            r_idx = 7 - chess.square_rank(square)
            c_idx = chess.square_file(square)
            freq[r_idx, c_idx] += 1

    plt.figure(figsize=(6, 6))
    plt.imshow(freq, cmap="hot", interpolation="nearest")
    plt.title("Blunders Heatmap")
    plt.colorbar(label="Blunders on Square")
    plt.xticks(range(8), list("abcdefgh"))
    plt.yticks(range(8), list("87654321"))
    plt.savefig("plots/heatmaps/blunders.png")
    plt.close()


# ============================================================
#   3) HEATMAP OF CENTIPAWN LOSS DISTRIBUTION
# ============================================================
def heatmap_cpl(results):
    ensure_dir()

    freq = np.zeros((8, 8), dtype=float)
    count = np.zeros((8, 8), dtype=int)

    for r in results:
        game = r.pgn_game
        board = game.board()

        for cp, move in zip(r.cpl_list, game.mainline_moves()):
            square = move.to_square
            r_idx = 7 - chess.square_rank(square)
            c_idx = chess.square_file(square)

            freq[r_idx, c_idx] += abs(cp)
            count[r_idx, c_idx] += 1
            board.push(move)

    avg_cpl = np.divide(freq, count, out=np.zeros_like(freq), where=(count != 0))

    plt.figure(figsize=(6, 6))
    plt.imshow(avg_cpl, cmap="hot", interpolation="nearest")
    plt.title("Average CPL per Square")
    plt.colorbar(label="CPL")
    plt.xticks(range(8), list("abcdefgh"))
    plt.yticks(range(8), list("87654321"))
    plt.savefig("plots/heatmaps/cpl_heatmap.png")
    plt.close()


# ============================================================
#   MASTER GENERATOR
# ============================================================
def generate_all_heatmaps(results):
    heatmap_move_frequency(results)
    heatmap_blunders(results)
    heatmap_cpl(results)
