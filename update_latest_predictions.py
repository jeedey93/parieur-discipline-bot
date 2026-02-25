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
    bet_of_day_justification = ""
    bet_of_day_confidence_line = ""
    plays = []
    summary = {"High": 0, "Medium": 0, "units": 0.0}
    # Remove table_lines and odds table parsing
    i = 0
    in_table = False
    while i < len(lines):
        line = lines[i].strip()
        # Odds table parsing removed
        i += 1
    # Flexible parsing for Bet of the Day and plays
    i = 0
    found_bet_of_day = False
    found_recommended = False
    temp_plays = []
    while i < len(lines):
        line = lines[i].strip()
        # Detect Bet of the Day header anywhere (with or without asterisks/colons)
        if re.match(r"\*?\*?BET OF THE DAY:?[\*\s]*", line, re.IGNORECASE):
            found_bet_of_day = True
            i += 1
            # Next play is Bet of the Day
            # Skip empty lines
            while i < len(lines) and not lines[i].strip():
                i += 1
            # Parse the play header (must include odds)
            if i < len(lines):
                play_header = lines[i].strip()
                # If the play header does not contain '@', look ahead for the next line with '@'
                if '@' not in play_header:
                    lookahead = i + 1
                    while lookahead < len(lines):
                        next_line = lines[lookahead].strip()
                        if '@' in next_line:
                            play_header = next_line
                            i = lookahead
                            break
                        lookahead += 1
                details = []
                confidence_emoji = ""
                confidence_line = ""
                play_units = 0.0
                play_conf = None
                i += 1
                while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith("---") and not re.match(r"\*?\*?Recommended Plays:?[\*\s]*", lines[i].strip(), re.IGNORECASE):
                    details.append(lines[i].strip())
                    if lines[i].strip().startswith("Confidence Level:") or lines[i].strip().startswith("🔥 Confidence:") or lines[i].strip().startswith("👍 Confidence:"):
                        confidence_emoji, level, units, percent = parse_confidence(lines[i].strip())
                        play_conf = level
                        play_units = safe_float(units)
                        confidence_line = f"{confidence_emoji} Confidence: {level} ({units}u, {percent}%)"
                    i += 1
                justification = " ".join([d for d in details if not d.startswith("Confidence Level:") and not d.startswith("🔥 Confidence:") and not d.startswith("👍 Confidence:")])
                bet_of_day_header = play_header
                bet_of_day_justification = justification
                bet_of_day_confidence_line = confidence_line
                bet_of_day_conf = play_conf
                bet_of_day_units = play_units
                if bet_of_day_conf in summary:
                    summary[bet_of_day_conf] += 1
                summary["units"] += bet_of_day_units
            continue
        # Recommended Plays header
        if re.match(r"\*?\*?Recommended Plays:?[\*\s]*", line, re.IGNORECASE):
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
            while i < len(lines) and lines[i].strip() and not re.match(r"\d+\.\s+.+", lines[i]) and not lines[i].strip().startswith("---") and not re.match(r"\*?\*?BET OF THE DAY:?[\*\s]*", lines[i].strip(), re.IGNORECASE) and not re.match(r"\*?\*?Recommended Plays:?[\*\s]*", lines[i].strip(), re.IGNORECASE):
                details.append(lines[i].strip())
                if lines[i].strip().startswith("Confidence Level:") or lines[i].strip().startswith("🔥 Confidence:") or lines[i].strip().startswith("👍 Confidence:"):
                    confidence_emoji, level, units, percent = parse_confidence(lines[i].strip())
                    play_conf = level
                    play_units = safe_float(units)
                    confidence_line = f"{confidence_emoji} Confidence: {level} ({units}u, {percent}%)"
                i += 1
            play_block = [f"{play_header}", ""]
            justification = " ".join([d for d in details if not d.startswith("Confidence Level:") and not d.startswith("🔥 Confidence:") and not d.startswith("👍 Confidence:")])
            if confidence_line:
                justification = justification + (" " if justification else "") + confidence_line
            play_block.append(justification)
            play_block.append("")
            temp_plays.append({
                "block": play_block,
                "conf": play_conf,
                "units": play_units,
                "justification": justification
            })
        else:
            i += 1
    # Remove Bet of the Day from recommended plays if present
    plays = []
    for play in temp_plays:
        if bet_of_day_header and play["block"][0] == bet_of_day_header:
            continue
        plays.append("\n".join(play["block"]))
        if play["conf"] in summary:
            summary[play["conf"]] += 1
            summary["units"] += play["units"]
    summary_lines = ["### Summary"]
    summary_lines.append(f"- High Confidence Plays: {summary['High']}")
    summary_lines.append(f"- Medium Confidence Plays: {summary['Medium']}")
    summary_lines.append(f"- Total Units Risked: {summary['units']}u\n")
    output = []
    output.extend(summary_lines)
    # Odds table removed from output
    if bet_of_day_header:
        output.append("---")
        output.append("🏆 **BET OF THE DAY**")
        output.append("")
        output.append(bet_of_day_header)
        output.append("")
        if bet_of_day_justification:
            output.append(bet_of_day_justification)
        if bet_of_day_confidence_line:
            output.append(bet_of_day_confidence_line)
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
