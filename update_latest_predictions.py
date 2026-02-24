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

def safe_float(val):
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0

def parse_confidence(line):
    match = re.search(r"Confidence Level: (High|Medium) Units: ([0-9.]*)u \| Confidence ?: ([0-9.]+)%", line)
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
    bet_of_day_header = None
    bet_of_day_units = 0.0
    bet_of_day_conf = None
    plays = []
    summary = {"High": 0, "Medium": 0, "units": 0.0}
    table_lines = []
    # Odds table parsing unchanged
    i = 0
    in_table = False
    while i < len(lines):
        line = lines[i].strip()
        if re.match(r"^[A-Za-z ]+vs [A-Za-z ]+$", line):
            table_lines.append("| Matchup | Odds/Spreads |")
            table_lines.append("|:---|:---|")
            in_table = True
        elif in_table and line == "------":
            in_table = False
        elif in_table:
            table_lines.append(f"| {line} |")
        i += 1
    # Parse Bet of the Day (new format)
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("### Bet of the Day:"):
            bet_of_day_header = line.replace("### Bet of the Day:", "").strip()
            bet_of_day.append(f"> **{bet_of_day_header}**")
            i += 1
            details = []
            confidence_line = ""
            while i < len(lines) and lines[i].strip() and not lines[i].startswith("### NBA Betting Plays:"):
                details.append(lines[i].strip())
                if lines[i].strip().startswith("Confidence Level:"):
                    emoji, level, units, percent = parse_confidence(lines[i].strip())
                    bet_of_day_conf = level
                    bet_of_day_units = safe_float(units)
                    confidence_line = f"{emoji} **Confidence:** {level} ({units}u, {percent}%)"
                i += 1
            for d in details:
                if d.startswith("Confidence Level:") and confidence_line:
                    bet_of_day.append(f"> {confidence_line}")
                elif not d.startswith("Confidence Level:"):
                    bet_of_day.append(f"> {d}")
            bet_of_day.append("")
            summary[bet_of_day_conf] += 1
            summary["units"] += bet_of_day_units
            break
        i += 1
    # Parse Recommended Plays (new format)
    i = 0
    in_recommended = False
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("### NBA Betting Plays:"):
            in_recommended = True
            i += 1
            continue
        if in_recommended:
            # Look for numbered play headers
            match = re.match(r"\d+\.\s+\*\*(.+)\*\*", line)
            if match:
                play_header = match.group(1).strip()
                details = []
                confidence_emoji = ""
                confidence_line = ""
                play_units = 0.0
                play_conf = None
                i += 1
                while i < len(lines) and lines[i].strip() and not re.match(r"\d+\.\s+\*\*.+\*\*", lines[i]):
                    details.append(lines[i].strip())
                    if lines[i].strip().startswith("Confidence Level:"):
                        confidence_emoji, level, units, percent = parse_confidence(lines[i].strip())
                        play_conf = level
                        play_units = safe_float(units)
                        confidence_line = f"{confidence_emoji} **Confidence:** {level} ({units}u, {percent}%)"
                    i += 1
                play_block = [f"> **{play_header}**"]
                for d in details:
                    if d.startswith("Confidence Level:") and confidence_line:
                        play_block.append(f"> {confidence_line}")
                    elif not d.startswith("Confidence Level:"):
                        play_block.append(f"> {d}")
                play_block.append("")
                plays.append("\n".join(play_block))
                if play_conf:
                    summary[play_conf] += 1
                    summary["units"] += play_units
            else:
                i += 1
        else:
            i += 1
    summary_lines = ["### Summary"]
    summary_lines.append(f"- High Confidence Plays: {summary['High']}")
    summary_lines.append(f"- Medium Confidence Plays: {summary['Medium']}")
    summary_lines.append(f"- Total Units Risked: {summary['units']}u\n")
    output = []
    output.extend(summary_lines)
    if table_lines:
        output.append("### Odds & Spreads Table")
        output.extend(table_lines)
        output.append("")
    if bet_of_day:
        output.append("---")
        output.append("🏆 **BET OF THE DAY**")
        output.extend(bet_of_day)
        output.append("---\n")
    if plays:
        output.append("**Other Recommended Plays**")
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
