import os
from glob import glob

def get_latest_file(folder, prefix):
    files = glob(os.path.join(folder, f"{prefix}_*.txt"))
    if not files:
        return None
    latest = max(files, key=os.path.getctime)
    return latest

def read_file(path):
    with open(path, "r") as f:
        return f.read()

def update_latest_predictions():
    predictions_dir = "predictions"
    sports = ["nba", "nhl"]
    output_md = "LATEST_PREDICTIONS.md"

    content = "# Latest Predictions\n\n"
    for sport in sports:
        folder = os.path.join(predictions_dir, sport)
        latest_file = get_latest_file(folder, f"{sport}_daily_predictions")
        if latest_file:
            date_str = os.path.basename(latest_file).split("_")[-1].replace(".txt", "")
            content += f"## {sport.upper()} ({date_str})\n"
            content += "```\n" + read_file(latest_file) + "\n```\n\n"

    with open(output_md, "w") as f:
        f.write(content)

if __name__ == "__main__":
    update_latest_predictions()
