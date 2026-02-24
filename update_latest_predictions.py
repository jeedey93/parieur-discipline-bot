import os
from glob import glob
import re

def get_latest_file(folder, prefix, ext="txt"):
    files = glob(os.path.join(folder, f"{prefix}_*.{ext}"))
    if not files:
        return None
    latest = max(files, key=os.path.getctime)
    return latest

def read_file(path):
    with open(path, "r") as f:
        return f.read()

def extract_ai_analysis(content):
    marker = "AI Analysis Summary:\nCurrent Roster Data Verified."
    idx = content.find(marker)
    if idx != -1:
        return content[idx + len(marker):].lstrip('\n')
    else:
        return "No AI analysis found."

def parse_confidence(line):
    # Returns emoji, confidence level, units, percent
    match = re.search(r"Confidence Level: (High|Medium) Units: ([0-9.]+)u \| Confidence %: ([0-9.]+)%", line)
    if match:
        level = match.group(1)
        units = match.group(2)
        percent = match.group(3)
        emoji = "🔥" if level == "High" else ("👍" if level == "Medium" else "")
        return emoji, level, units, percent
    return "", "", "", ""

def format_ai_analysis(ai_content):
    if ai_content.strip() == "No AI analysis found.":
        return ai_content
    lines = ai_content.strip().split("\n")
    bet_of_day = []
    plays = []
    summary = {"High": 0, "Medium": 0, "units": 0.0}
    i = 0
    # Try to extract odds/spreads table if present
    table_lines = []
    in_table = False
    while i < len(lines):
        line = lines[i].strip()
        if re.match(r"^[A-Za-z ]+vs [A-Za-z ]+$", line):
            # Table header
            table_lines.append("| Matchup | Odds/Spreads |")
            table_lines.append("|:---|:---|")
            in_table = True
        elif in_table and line == "------":
            # End of table
            in_table = False
        elif in_table:
            table_lines.append(f"| {line} |")
        i += 1
    # Reset i for play parsing
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Bet of the Day
        if line.startswith("Bet of the Day:"):
            bet_of_day.append(line)
            i += 1
            while i < len(lines) and lines[i].strip():
                bet_of_day.append(lines[i].strip())
                i += 1
            continue
        # Recommended play
        elif re.match(r"^[A-Za-z0-9 .+\-]+@ [0-9.]+", line):
            play_header = line
            details = []
            confidence_emoji = ""
            confidence_line = ""
            i += 1
            while i < len(lines) and lines[i].strip() and not lines[i].startswith("Bet of the Day:") and not re.match(r"^[A-Za-z0-9 .+\-]+@ [0-9.]+", lines[i]):
                details.append(lines[i].strip())
                if lines[i].strip().startswith("Confidence Level:"):
                    confidence_emoji, level, units, percent = parse_confidence(lines[i].strip())
                    if level in ("High", "Medium"):
                        confidence_line = f"{confidence_emoji} **Confidence:** {level} ({units}u, {percent}%)"
                        summary[level] += 1
                        if units:
                            try:
                                summary["units"] += float(units)
                            except Exception:
                                pass
                i += 1
            play_block = [f"> **{play_header}**"]
            for d in details:
                if d.startswith("Confidence Level:") and confidence_line:
                    play_block.append(f"> {confidence_line}")
                elif not d.startswith("Confidence Level:"):
                    play_block.append(f"> {d}")
            play_block.append("")
            plays.append("\n".join(play_block))
        else:
            i += 1
    # Format summary
    summary_lines = ["### Summary"]
    summary_lines.append(f"- **High Confidence Plays:** {summary['High']}")
    summary_lines.append(f"- **Medium Confidence Plays:** {summary['Medium']}")
    summary_lines.append(f"- **Total Units Risked:** {summary['units']}u\n")
    # Format Bet of the Day at the top
    output = []
    output.extend(summary_lines)
    if table_lines:
        output.append("### Odds & Spreads Table")
        output.extend(table_lines)
        output.append("")
    if bet_of_day:
        output.append("---")
        output.append("> \U0001F3C6 **" + bet_of_day[0][15:] + "**")
        for d in bet_of_day[1:]:
            output.append(f"> {d}")
        output.append("---\n")
    output.extend(plays)
    return "\n".join(output)

def update_latest_predictions():
    predictions_dir = "predictions"
    sports = ["nba", "nhl"]
    output_md = "LATEST_PREDICTIONS.md"

    content = "# Latest Predictions\n\n"
    for sport in sports:
        folder = os.path.join(predictions_dir, sport)
        latest_text_file = get_latest_file(folder, f"{sport}_daily_predictions", ext="txt")
        if latest_text_file:
            date_str = os.path.basename(latest_text_file).split("_")[-1].replace(".txt", "")
            content += f"## {sport.upper()} ({date_str})\n"
            ai_content = extract_ai_analysis(read_file(latest_text_file))
            formatted_ai = format_ai_analysis(ai_content)
            content += formatted_ai + "\n\n"
        else:
            content += f"## {sport.upper()}\nNo {sport.upper()} predictions found.\n\n"

    with open(output_md, "w") as f:
        f.write(content)

if __name__ == "__main__":
    update_latest_predictions()
