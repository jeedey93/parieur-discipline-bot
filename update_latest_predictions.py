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
    # Accept either Verified or Unavailable, or just "AI Analysis Summary:"
    marker_verified = "AI Analysis Summary:\nCurrent Roster Data Verified."
    marker_unavailable = "AI Analysis Summary:\nCurrent Roster Data Unavailable."
    marker_generic = "AI Analysis Summary:"
    idx = content.find(marker_verified)
    if idx != -1:
        return content[idx + len(marker_verified):].lstrip('\n')
    idx = content.find(marker_unavailable)
    if idx != -1:
        return content[idx + len(marker_unavailable):].lstrip('\n')
    idx = content.find(marker_generic)
    if idx != -1:
        return content[idx + len(marker_generic):].lstrip('\n')
    return "No AI analysis found."

def safe_float(val):
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0

def parse_confidence(line):
    # Accept variations like:
    # Confidence Level: Medium Units: 1u | Confidence : 58.0%
    # Confidence: Medium, 1u, 58%
    # Confidence Level: Medium | Units: 1u | Confidence: 58%
    # Confidence Level: Medium, Units: 1u, Confidence: 58%
    # Confidence Level: Medium Units: 1 Unit | Confidence : 58.0%
    # Confidence Level: Medium Units: 1 | Confidence : 58.0%
    regexes = [
        r"Confidence Level[: ]*([Hh]igh|[Mm]edium)[,| ]+Units?[: ]*([0-9.]+)[ ]*(?:u|Unit[s]?)?[,| ]+\|? ?Confidence[: ]*([0-9.]+)%",
        r"Confidence Level[: ]*([Hh]igh|[Mm]edium)[,| ]+Units?[: ]*([0-9.]+)[ ]*(?:u|Unit[s]?)?[,| ]+Confidence[: ]*([0-9.]+)%",
        r"Confidence[: ]*([Hh]igh|[Mm]edium)[,| ]*([0-9.]+)[ ]*(?:u|Unit[s]?)?[,| ]*([0-9.]+)%",
        r"Confidence Level[: ]*([Hh]igh|[Mm]edium)[,| ]*Units?[: ]*([0-9.]+)[ ]*(?:u|Unit[s]?)?[,| ]*Confidence[: ]*([0-9.]+)%",
        r"Confidence Level[: ]*([Hh]igh|[Mm]edium)[,| ]*Units?[: ]*([0-9.]+)[ ]*(?:u|Unit[s]?)?[,| ]*Confidence[: ]*([0-9.]+)",
        r"Confidence[: ]*([Hh]igh|[Mm]edium)[,| ]*([0-9.]+)[ ]*(?:u|Unit[s]?)?[,| ]*([0-9.]+)"
    ]
    for regex in regexes:
        match = re.search(regex, line)
        if match:
            level = match.group(1).capitalize()
            units = match.group(2)
            percent = match.group(3)
            emoji = "🔥" if level == "High" else ("👍" if level == "Medium" else "")
            return emoji, level, units, percent
    # Fallback: try to extract just the level
    match = re.search(r"Confidence Level[: ]*([Hh]igh|[Mm]edium)", line)
    if match:
        level = match.group(1).capitalize()
        emoji = "🔥" if level == "High" else ("👍" if level == "Medium" else "")
        return emoji, level, "", ""
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
    # Flexible parsing for Bet of the Day and plays
    i = 0
    found_bet_of_day = False
    found_recommended = False
    while i < len(lines):
        line = lines[i].strip()
        # Bet of the Day header
        if line.startswith("BET OF THE DAY") or line.startswith("Bet of the Day"):
            found_bet_of_day = True
            i += 1
            continue
        # Recommended Plays header
        if line.startswith("RECOMMENDED PLAYS") or line.startswith("Recommended Plays"):
            found_recommended = True
            i += 1
            continue
        # Play header (numbered or unnumbered)
        play_header = None
        match = re.match(r"\d+\.\s+(.+)", line)
        if match:
            play_header = match.group(1).strip()
        elif re.match(r".+@\s*[\d.]+", line) or re.match(r".+vs.+@\s*[\d.]+", line):
            play_header = line
        elif re.match(r".+-\d+\.\d+\s+vs\s+.+@\s*[\d.]+", line):
            play_header = line
        if play_header:
            details = []
            confidence_emoji = ""
            confidence_line = ""
            play_units = 0.0
            play_conf = None
            i += 1
            while i < len(lines) and lines[i].strip() and not re.match(r"\d+\.\s+.+", lines[i]) and not lines[i].strip().startswith("BET OF THE DAY") and not lines[i].strip().startswith("RECOMMENDED PLAYS"):
                details.append(lines[i].strip())
                if lines[i].strip().startswith("Confidence Level:"):
                    confidence_emoji, level, units, percent = parse_confidence(lines[i].strip())
                    play_conf = level
                    play_units = safe_float(units)
                    confidence_line = f"{confidence_emoji} Confidence: {level} ({units}u, {percent}%)"
                i += 1
            play_block = [f"{play_header}", ""]
            justification = " ".join([d for d in details if not d.startswith("Confidence Level:")])
            if confidence_line:
                justification = justification + (" " if justification else "") + confidence_line
            play_block.append(justification)
            play_block.append("")
            if not found_bet_of_day and not found_recommended:
                # If Bet of the Day header not found, treat first play as Bet of the Day
                bet_of_day = play_block
                bet_of_day_conf = play_conf
                bet_of_day_units = play_units
                if bet_of_day_conf in summary:
                    summary[bet_of_day_conf] += 1
                summary["units"] += bet_of_day_units
                found_bet_of_day = True
            else:
                plays.append("\n".join(play_block))
                if play_conf in summary:
                    summary[play_conf] += 1
                    summary["units"] += play_units
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
        output.append("")
        output.extend(bet_of_day)
        output.append("---\n")
        output.append("")
    if plays:
        output.append("**Other Recommended Plays**")
        output.append("")
        output.extend(plays)
        output.append("")
    return "\n".join(output)

def update_latest_predictions():
    predictions_dir = "predictions"
    sports = ["nhl", "nba"]
    output_md = "docs/index.md"

    # Find the latest date among all sports
    latest_dates = []
    for sport in sports:
        folder = os.path.join(predictions_dir, sport)
        latest_text_file = get_latest_file(folder, f"{sport}_daily_predictions", ext="txt")
        if latest_text_file:
            date_str = os.path.basename(latest_text_file).split("_")[-1].replace(".txt", "")
            latest_dates.append(date_str)
    # Use the most recent date
    overall_latest_date = max(latest_dates) if latest_dates else ""

    content = f"# Latest Predictions ({overall_latest_date})\n\n"
    for sport in sports:
        folder = os.path.join(predictions_dir, sport)
        latest_text_file = get_latest_file(folder, f"{sport}_daily_predictions", ext="txt")
        content += f"## {sport.upper()}\n"
        if latest_text_file:
            ai_content = extract_ai_analysis(read_file(latest_text_file))
            formatted_ai = format_ai_analysis(ai_content)
            content += formatted_ai + "\n\n"
        else:
            content += f"No {sport.upper()} predictions found.\n\n"

    with open(output_md, "w") as f:
        f.write(content)

if __name__ == "__main__":
    update_latest_predictions()
