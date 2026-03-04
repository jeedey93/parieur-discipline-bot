import os
import re
from glob import glob
from datetime import datetime


def get_latest_file(folder, prefix, ext="txt"):
    files = glob(os.path.join(folder, f"{prefix}_*.{ext}"))
    if not files:
        return None
    latest = max(files, key=os.path.getctime)
    return latest


def read_file(path):
    with open(path, "r") as f:
        return f.read()


def format_date_nice(date_str):
    """Convert 2026-03-03 to March 3, 2026"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%B %d, %Y").replace(" 0", " ")
    except Exception:
        return date_str


def parse_record(summary_path):
    """Parse the total_results_summary.txt and return NBA/NHL records."""
    nba_record = {"wins": 0, "losses": 0}
    nhl_record = {"wins": 0, "losses": 0}
    if not os.path.exists(summary_path):
        return nba_record, nhl_record
    content = read_file(summary_path)
    current_sport = None
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("NBA:"):
            current_sport = "nba"
        elif line.startswith("NHL:"):
            current_sport = "nhl"
        elif line.startswith("TOTAL:") and current_sport:
            m = re.match(r"TOTAL:\s*(\d+)\s*wins?,\s*(\d+)\s*losses?", line)
            if m:
                record = nba_record if current_sport == "nba" else nhl_record
                record["wins"] = int(m.group(1))
                record["losses"] = int(m.group(2))
    return nba_record, nhl_record


def format_sport_content(raw_text, sport_emoji, sport_name):
    """Format the raw prediction text into clean markdown sections."""
    lines = raw_text.strip().splitlines()

    # Find the line where the actual picks/recommendations start.
    # We look for lines that START with BET OF THE DAY or a heading with
    # "Unified Final Recommendation" — but not inside a paragraph.
    i = 0
    for idx, line in enumerate(lines):
        stripped = line.strip()
        upper = stripped.upper()

        # Match lines that are clearly the start of recommendations:
        # "🏆 **BET OF THE DAY**"
        # "### Unified Final Recommendation List"
        # "**Unified Final Recommendation List**"
        # But NOT a sentence like "Here's an analysis... unified final recommendation list:"
        is_bet_of_day = upper.startswith("BET OF THE DAY") or upper.startswith("🏆")
        is_unified_header = (
            (stripped.startswith("#") or stripped.startswith("**"))
            and "UNIFIED FINAL RECOMMENDATION" in upper
        )
        if is_bet_of_day or is_unified_header:
            i = idx
            break
    else:
        # No clear split found — treat everything as recommendations
        return "", raw_text.strip()

    # Build the analysis summary as a collapsible section
    analysis_text = "\n".join(lines[:i]).strip()

    # Build recommendations section
    recs_text = "\n".join(lines[i:]).strip()

    return analysis_text, recs_text


def ensure_line_breaks_after_plays(text):
    """Ensure there is a blank line after each play header line so the
    justification renders on a new line in markdown.

    A 'play header' is a bold line like **Team vs Opponent ...** that is
    immediately followed by a non-blank line (Confidence Level or justification).
    We also handle the BET OF THE DAY header + play combo.
    """
    lines = text.split("\n")
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        result.append(line)

        # Check if this line is a play header (bold play line)
        is_play_header = (
            stripped.startswith("**") and stripped.endswith("**")
            and ("vs" in stripped.lower() or "over" in stripped.lower() or "under" in stripped.lower() or "@" in stripped)
            and "BET OF THE DAY" not in stripped
            and "Other Recommended" not in stripped
            and "Unified Final" not in stripped
        )

        # Also handle numbered plays like "**1. Team vs Opponent ...**"
        if not is_play_header and stripped.startswith("**") and stripped.endswith("**"):
            inner = stripped.strip("*").strip()
            if re.match(r'^\d+\.?\\s+', inner) and ("vs" in inner.lower() or "@" in inner):
                is_play_header = True

        if is_play_header:
            # Check if next non-blank line exists and is NOT already separated
            if i + 1 < len(lines) and lines[i + 1].strip() != "":
                result.append("")  # Insert blank line

        i += 1

    return "\n".join(result)


def build_sport_section(raw_text, sport_key, sport_name, sport_emoji, record):
    """Build a complete sport section with nice formatting."""
    if not raw_text:
        return f"\n> ℹ️ No {sport_name} predictions available today.\n\n"

    analysis_text, recs_text = format_sport_content(raw_text, sport_emoji, sport_name)

    wins = record["wins"]
    losses = record["losses"]
    total = wins + losses
    win_pct = f"{(wins / total * 100):.1f}%" if total > 0 else "N/A"

    md = ""

    # Record bar
    md += f"> 📊 **Season Record:** {wins}W - {losses}L ({win_pct})\n\n"

    # Analysis summary (collapsible)
    if analysis_text:
        # Clean up the analysis text for better rendering inside <details>
        cleaned = analysis_text.strip()
        # Remove leading "Here's an analysis..." intro line if present
        intro_patterns = [
            r"^Here'?s an analysis.*?:\s*\n",
            r"^Here'?s a comparison.*?:\s*\n",
        ]
        for pat in intro_patterns:
            cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.strip().lstrip("-").strip()

        # Remove trailing --- that looks messy inside details
        cleaned = re.sub(r'\n---\s*$', '', cleaned).strip()
        # Remove leading --- as well
        cleaned = re.sub(r'^---\s*\n', '', cleaned).strip()

        # Convert markdown headings to HTML for reliable rendering inside <details>
        def heading_to_html(m):
            level = len(m.group(1))
            text = m.group(2).strip()
            return f"<h{level}>{text}</h{level}>"
        cleaned = re.sub(r'^(#{1,6})\s+(.+)$', heading_to_html, cleaned, flags=re.MULTILINE)

        # Convert --- separators to <hr> for reliable rendering
        cleaned = re.sub(r'^\s*---\s*$', '<hr>', cleaned, flags=re.MULTILINE)

        # Convert **bold** to <strong> for reliable rendering inside HTML
        cleaned = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', cleaned)

        # Convert *italic* to <em> (but not bullet points)
        cleaned = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', cleaned)

        # Convert bullet points (* item) to HTML list items
        lines_list = cleaned.split('\n')
        in_list = False
        new_lines = []
        for line in lines_list:
            stripped = line.strip()
            if stripped.startswith('* ') or stripped.startswith('- '):
                if not in_list:
                    new_lines.append('<ul>')
                    in_list = True
                # Handle nested bullets (4 spaces indent)
                if line.startswith('    ') or line.startswith('\t'):
                    item_text = stripped[2:]
                    new_lines.append(f'  <li>{item_text}</li>')
                else:
                    item_text = stripped[2:]
                    new_lines.append(f'<li>{item_text}</li>')
            else:
                if in_list:
                    new_lines.append('</ul>')
                    in_list = False
                # Convert blank lines to <br> for spacing
                if stripped == '':
                    new_lines.append('<br>')
                else:
                    new_lines.append(f'<p>{stripped}</p>' if stripped and not stripped.startswith('<') else stripped)
        if in_list:
            new_lines.append('</ul>')
        cleaned = '\n'.join(new_lines)

        # Add a hint for the collapsible section with a visual arrow
        md += "<details>\n"
        md += "<summary style='cursor:pointer;font-size:1.1em;'><span style='font-size:1.2em;'>▶️</span> <b>Morning vs Noon Comparison & Analysis</b> <span style='color:gray'>(click to expand for details)</span></summary>\n\n"
        md += cleaned + "\n\n"
        md += "</details>\n\n"

    # Recommendations
    if recs_text:
        recs_text = ensure_line_breaks_after_plays(recs_text)
        md += recs_text + "\n\n"

    return md


def format_dual_bet(raw_text):
    """Format the dual bet of the day into a nicely styled markdown section."""
    lines = raw_text.strip().splitlines()

    md = ""

    # Parse picks from the raw text
    picks = []
    current_pick = None
    footer_lines = []
    in_footer = False

    for line in lines:
        stripped = line.strip()

        # Skip the header line and separator lines
        if stripped.startswith("🔥 DUAL BET OF THE DAY"):
            continue
        if stripped == "⸻":
            if current_pick:
                picks.append(current_pick)
                current_pick = None
            continue

        # Detect pick headers
        if stripped.startswith("🎯 PICK #"):
            current_pick = {"header": stripped, "body": []}
            continue

        # Detect footer (starts with "Two sports" or legacy French closing)
        if stripped.startswith("Two sports") or stripped.startswith("We follow the value") or stripped.startswith("Deux sports") or stripped.startswith("On suit la value"):
            in_footer = True

        if in_footer:
            if stripped:
                footer_lines.append(stripped)
            continue

        # Add body text to current pick
        if current_pick is not None and stripped:
            current_pick["body"].append(stripped)
        elif current_pick is None and stripped and not stripped.startswith("Two leagues") and not stripped.startswith("Deux ligues"):
            # Stray line before any pick – skip
            pass

    # Flush last pick if not yet added
    if current_pick:
        picks.append(current_pick)

    # Render each pick as a blockquote card
    for pick in picks:
        header = pick["header"]
        body = "\n>\n> ".join(pick["body"])

        # Extract the sport emoji for the card accent
        if "NHL" in header:
            sport_accent = "🏒"
        elif "NBA" in header:
            sport_accent = "🏀"
        else:
            sport_accent = "🎯"

        # Extract the bet line (e.g. "Washington Capitals ML vs Utah Mammoth @ 1.83")
        # It's usually everything after the sport emoji tag
        bet_line = header
        for tag in ["🎯 PICK #1 – NHL 🏒", "🎯 PICK #2 – NBA 🏀",
                     "🎯 PICK #1 – NBA 🏀", "🎯 PICK #2 – NHL 🏒",
                     "🎯 PICK #1 –", "🎯 PICK #2 –"]:
            if bet_line.startswith(tag):
                bet_line = bet_line[len(tag):].strip()
                break

        # Determine pick number
        pick_num = "1" if "#1" in header else "2"
        sport_label = "NHL" if "NHL" in header else "NBA"

        md += f"> ### {sport_accent} PICK #{pick_num} — {sport_label}\n"
        md += f"> **{bet_line}**\n"
        md += f">\n"
        if body:
            md += f"> {body}\n"
        md += "\n"


    return md


def update_latest_predictions():
    predictions_dir = "predictions"
    sports_config = [
        {"key": "nhl", "name": "NHL", "emoji": "🏒"},
        {"key": "nba", "name": "NBA", "emoji": "🏀"},
    ]
    output_md = "docs/index.md"
    summary_path = "bot_results/total_results_summary.txt"
    dual_bet_path = os.path.join(predictions_dir, "dual_bet_of_the_day.txt")

    # Parse records
    nba_record, nhl_record = parse_record(summary_path)
    records = {"nba": nba_record, "nhl": nhl_record}

    # Find the latest date among all sports
    latest_dates = []
    sport_files = {}
    for cfg in sports_config:
        sport = cfg["key"]
        folder = os.path.join(predictions_dir, sport)
        latest_text_file = get_latest_file(folder, f"{sport}_daily_predictions", ext="txt")
        sport_files[sport] = latest_text_file
        if latest_text_file:
            date_str = os.path.basename(latest_text_file).split("_")[-1].replace(".txt", "")
            latest_dates.append(date_str)
    overall_latest_date = max(latest_dates) if latest_dates else ""

    # ── Build the page ──
    nice_date = format_date_nice(overall_latest_date)
    # content = f"### 📅 {nice_date}\n\n" if nice_date else ""
    content = ""

    # ── Dual Bet of the Day (hero section) ──
    if os.path.exists(dual_bet_path):
        dual_content = read_file(dual_bet_path).strip()
        if dual_content:
            content += format_dual_bet(dual_content)
            content += "\n---\n\n"

    # ── Overall record summary ──
    total_w = nba_record["wins"] + nhl_record["wins"]
    total_l = nba_record["losses"] + nhl_record["losses"]
    total_games = total_w + total_l
    overall_pct = f"{(total_w / total_games * 100):.1f}%" if total_games > 0 else "N/A"

    content += "## 📈 Overall Performance\n\n"
    content += "| | Wins | Losses | Win % |\n"
    content += "|---|:---:|:---:|:---:|\n"
    content += f"| 🏒 NHL | {nhl_record['wins']} | {nhl_record['losses']} | {(nhl_record['wins'] / (nhl_record['wins'] + nhl_record['losses']) * 100):.1f}% |\n" if (nhl_record['wins'] + nhl_record['losses']) > 0 else f"| 🏒 NHL | 0 | 0 | N/A |\n"
    content += f"| 🏀 NBA | {nba_record['wins']} | {nba_record['losses']} | {(nba_record['wins'] / (nba_record['wins'] + nba_record['losses']) * 100):.1f}% |\n" if (nba_record['wins'] + nba_record['losses']) > 0 else f"| 🏀 NBA | 0 | 0 | N/A |\n"
    content += f"| **Total** | **{total_w}** | **{total_l}** | **{overall_pct}** |\n\n"

    content += "---\n\n"

    # ── Sport sections ──
    for cfg in sports_config:
        sport = cfg["key"]
        name = cfg["name"]
        emoji = cfg["emoji"]

        content += f"## {emoji} {name} Predictions\n\n"

        latest_file = sport_files.get(sport)
        if latest_file:
            raw = read_file(latest_file)
            content += build_sport_section(raw, sport, name, emoji, records[sport])
        else:
            content += f"> ℹ️ No {name} predictions available today.\n\n"

        content += "---\n\n"


    with open(output_md, "w") as f:
        f.write(content)
    print(f"✅ Updated {output_md}")


if __name__ == "__main__":
    update_latest_predictions()
