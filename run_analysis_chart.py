#run_analysis_chart.py
from analyzerChart import analyze_latest_games
from plotter import generate_plots
from plotter import generate_accuracy_plot, generate_top_blunders

def main():
    username = "bielbart77"
    print(f"Analysing latest games for {username} ...")

    results = analyze_latest_games(username=username, max_games=10, perf_type="rapid")

    print("Done. Results:\n")
    for r in results:
        print(r)

    print("Generating plots...")
    generate_plots(results)
    print("Plots saved.")

    summarize_all(results)
    print("Global summary done.")

    print("Generating Accuracy chart...")
    generate_accuracy_plot(results)
    print("Accuracy chart done.")

    print("Generating TOP blunders...")
    generate_top_blunders(results)
    print("TOP blunders saved in plots/TOP_BLUNDERS.txt")


def summarize_all(results):
    total_cpl = []
    total_inacc = 0
    total_mist = 0
    total_blunder = 0

    for r in results:
        total_cpl.extend(r.cpl_list)
        total_inacc += r.count_inacc
        total_mist += r.count_mist
        total_blunder += r.count_blunder

    avg_cpl = sum(abs(c) for c in total_cpl) / len(total_cpl)
    accuracy = max(0, 100 - (avg_cpl / 30))

    print("\n===== GLOBAL SUMMARY =====")
    print(f"Overall Average CPL: {avg_cpl:.1f}")
    print(f"Overall Accuracy: {accuracy:.1f}%")
    print(f"Total Inaccuracies: {total_inacc}")
    print(f"Total Mistakes: {total_mist}")
    print(f"Total Blunders: {total_blunder}")
    print("==========================\n")


if __name__ == "__main__":
    main()
