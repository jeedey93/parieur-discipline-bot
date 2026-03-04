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
    with open(path, "r", encoding="utf-8") as f:
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
    Additionally, ensure a blank line after the confidence/unit/win probability line.
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

        # Insert a blank line after confidence/unit/win probability line
        if (
            re.match(r"^Confidence Level:\s*", stripped, re.IGNORECASE)
            or re.match(r"^Confidence:\s*", stripped, re.IGNORECASE)
        ):
            # Only insert if next line is not already blank
            if i + 1 < len(lines) and lines[i + 1].strip() != "":
                result.append("")

        i += 1

    return "\n".join(result)


def format_recommendations_as_cards(recs_text):
    """Format plain recommendation text into styled cards."""
    if not recs_text:
        return ""

    lines = recs_text.split('\n')
    formatted = []
    current_card = None
    in_bet_of_day = False
    in_other_plays = False

    for line in lines:
        stripped = line.strip()

        # Detect BET OF THE DAY section
        if '🏆' in stripped and 'BET OF THE DAY' in stripped.upper():
            if current_card:
                formatted.append(format_single_card(current_card, is_featured=in_bet_of_day))
            in_bet_of_day = True
            continue

        # Detect "Other Recommended Plays" section
        if 'Other Recommended' in stripped or 'Unified Final Recommendation' in stripped:
            if current_card:
                formatted.append(format_single_card(current_card, is_featured=in_bet_of_day))
                current_card = None
            in_bet_of_day = False
            in_other_plays = True
            formatted.append(f"\n<h3 style='margin: 30px 0 20px 0; color: #333;'>Other Recommended Plays</h3>\n\n")
            continue

        # Detect new play (starts with ** and contains vs or @)
        if stripped.startswith('**') and ('vs' in stripped or '@' in stripped) and not 'BET OF THE DAY' in stripped.upper():
            # Save previous card
            if current_card:
                formatted.append(format_single_card(current_card, is_featured=in_bet_of_day))

            # Extract play number if present
            play_num = None
            match = re.match(r'^\*\*(\d+)\.\s+(.+?)\*\*', stripped)
            if match:
                play_num = match.group(1)
                bet_line = match.group(2)
            else:
                bet_line = stripped.strip('*')

            current_card = {
                'number': play_num,
                'bet': bet_line,
                'details': [],
                'description': '',
                'changes': ''
            }
            continue

        # Collect card details
        if current_card:
            if 'Confidence Level:' in stripped or 'Confidence:' in stripped:
                current_card['details'].append(stripped)
            elif stripped.startswith('*Changes:') or stripped.startswith('*Change from'):
                current_card['changes'] = stripped.lstrip('*').strip()
            elif stripped and not stripped.startswith('---') and not stripped.startswith('Based on'):
                current_card['description'] += ' ' + stripped

    # Don't forget last card
    if current_card:
        formatted.append(format_single_card(current_card, is_featured=in_bet_of_day))

    return '\n'.join(formatted)


def format_single_card(card, is_featured=False):
    """Format a single recommendation card."""
    if is_featured:
        # Featured "Bet of the Day" card
        card_html = "<div style='background: linear-gradient(135deg, #FFD70015 0%, #FFA50005 100%); border: 2px solid #FFA500; border-radius: 8px; padding: 25px; margin: 20px 0; box-shadow: 0 4px 12px rgba(255,165,0,0.2);'>\n\n"
        card_html += "<div style='display: flex; align-items: center; margin-bottom: 15px;'>\n"
        card_html += "<span style='font-size: 2em; margin-right: 10px;'>🏆</span>\n"
        card_html += "<span style='font-size: 1.3em; font-weight: bold; color: #FF8C00;'>BET OF THE DAY</span>\n"
        card_html += "</div>\n\n"
    else:
        # Regular play card
        card_html = "<div style='background: white; border: 1px solid #e0e0e0; border-left: 4px solid #667eea; border-radius: 8px; padding: 20px; margin: 15px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>\n\n"
        if card['number']:
            card_html += f"<div style='font-size: 0.85em; color: #667eea; font-weight: bold; margin-bottom: 8px;'>PLAY #{card['number']}</div>\n\n"

    # Bet line
    card_html += f"<div style='font-size: 1.25em; font-weight: bold; color: #333; margin-bottom: 12px;'>{card['bet']}</div>\n\n"

    # Details (Confidence, Units, Win Prob)
    if card['details']:
        details_html = ' | '.join(card['details'])
        card_html += f"<div style='font-size: 0.9em; color: #667eea; font-weight: 600; margin-bottom: 12px; padding: 8px 0; border-top: 1px solid #f0f0f0; border-bottom: 1px solid #f0f0f0;'>{details_html}</div>\n\n"

    # Description
    if card['description']:
        card_html += f"<div style='color: #666; line-height: 1.6; margin-bottom: 10px;'>{card['description'].strip()}</div>\n\n"

    # Changes (if any)
    if card['changes']:
        card_html += f"<div style='font-size: 0.85em; color: #999; font-style: italic; padding-top: 10px; border-top: 1px dashed #e0e0e0;'>{card['changes']}</div>\n\n"

    card_html += "</div>\n\n"

    return card_html


def build_sport_section(raw_text, sport_key, sport_name, sport_emoji, record):
    """Build a complete sport section with nice formatting."""
    if not raw_text:
        return f"\n> ℹ️ No {sport_name} predictions available today.\n\n"

    analysis_text, recs_text = format_sport_content(raw_text, sport_emoji, sport_name)

    md = ""

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
        md += "<details style='background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;'>\n"
        md += "<summary style='cursor:pointer;font-size:1.1em; font-weight: bold; color: #667eea;'><span style='font-size:1.2em;'>▶️</span> Morning vs Noon Analysis <span style='color:#999; font-weight: normal;'>(click to expand)</span></summary>\n\n"
        md += "<div style='margin-top: 15px;'>\n"
        md += cleaned + "\n"
        md += "</div>\n\n"
        md += "</details>\n\n"

    # Format recommendations as styled cards
    if recs_text:
        formatted_recs = format_recommendations_section(recs_text)
        md += formatted_recs + "\n\n"

    return md


def format_recommendations_section(recs_text):
    """Parse and format recommendation text into styled cards."""
    if not recs_text:
        return ""

    lines = recs_text.split('\n')
    output = []
    current_pick = None
    is_bet_of_day = False

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Detect BET OF THE DAY
        if '🏆' in line and 'BET OF THE DAY' in line.upper():
            if current_pick:
                output.append(format_pick_card(current_pick, is_bet_of_day))
            is_bet_of_day = True
            i += 1
            continue

        # Detect "Other Recommended Plays" header
        if 'Other Recommended' in line:
            if current_pick:
                output.append(format_pick_card(current_pick, is_bet_of_day))
                current_pick = None
            is_bet_of_day = False
            output.append("\n<h3 style='margin: 30px 0 20px 0; color: #333; font-size: 1.5em;'>📋 Other Recommended Plays</h3>\n\n")
            i += 1
            continue

        # Detect a bet line (starts with ** and looks like a bet)
        # Format: **Team vs Team** or **Team ML vs Team** or **Team +X.X vs Team @ odds**
        is_bet_line = (line.startswith('**') and line.endswith('**') and
                      'BET OF THE DAY' not in line and
                      'Unified Final' not in line and
                      'Other Recommended' not in line and
                      ('vs' in line.lower() or 'ML' in line or 'over' in line.lower() or 'under' in line.lower() or '+' in line or '-' in line))
        if is_bet_line:
            # Save previous pick
            if current_pick:
                output.append(format_pick_card(current_pick, is_bet_of_day))

            # Extract play number if it exists
            play_num = None
            bet_text = line.strip('*')
            if bet_text[0].isdigit() and '.' in bet_text[:3]:
                parts = bet_text.split('.', 1)
                play_num = parts[0].strip()
                bet_text = parts[1].strip() if len(parts) > 1 else bet_text

            current_pick = {
                'number': play_num,
                'bet': bet_text,
                'confidence': '',
                'description': '',
                'changes': ''
            }
            i += 1
            continue

        # Collect details for current pick
        if current_pick:
            if 'Confidence Level:' in line or 'Confidence:' in line:
                current_pick['confidence'] = line
            elif line.startswith('*Changes:') or line.startswith('*Change from'):
                current_pick['changes'] = line.lstrip('*').strip()
            elif line and not line.startswith('---') and not line.startswith('Based on'):
                if current_pick['description']:
                    current_pick['description'] += ' '
                current_pick['description'] += line

        i += 1

    # Don't forget the last pick
    if current_pick:
        output.append(format_pick_card(current_pick, is_bet_of_day))

    return '\n'.join(output)


def format_pick_card(pick, is_featured=False):
    """Format a single pick as a styled card."""
    if is_featured:
        # Gold gradient for Bet of the Day
        html = "<div style='background: linear-gradient(135deg, #FFD70020 0%, #FFA50010 100%); border: 2px solid #FFA500; border-radius: 10px; padding: 25px; margin: 20px 0; box-shadow: 0 4px 12px rgba(255,165,0,0.15);'>\n\n"
        html += "<div style='display: inline-block; background: #FFA500; color: white; padding: 6px 12px; border-radius: 20px; font-size: 0.85em; font-weight: bold; margin-bottom: 15px;'>🏆 BET OF THE DAY</div>\n\n"
    else:
        # Clean white card with blue accent
        html = "<div style='background: white; border: 1px solid #e0e0e0; border-left: 4px solid #667eea; border-radius: 8px; padding: 20px; margin: 15px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>\n\n"
        if pick['number']:
            html += f"<div style='display: inline-block; background: #667eea; color: white; padding: 4px 10px; border-radius: 12px; font-size: 0.8em; font-weight: bold; margin-bottom: 10px;'>#{pick['number']}</div>\n\n"

    # Extract odds from changes note if not in bet text
    bet_display = pick['bet']
    if '@' not in bet_display and pick['changes']:
        # Try to extract odds from changes note
        # Patterns: "from 1.74 (morning) to 1.77 (noon)" or "remained the same as morning (1.67)"
        odds_match = re.search(r'to (\d+\.\d+) \(noon\)|same as morning \((\d+\.\d+)\)', pick['changes'])
        if odds_match:
            odds = odds_match.group(1) or odds_match.group(2)
            bet_display = f"{bet_display} @ {odds}"

    # Bet line - large and bold
    html += f"<div style='font-size: 1.3em; font-weight: bold; color: #222; margin-bottom: 15px; line-height: 1.3;'>{bet_display}</div>\n\n"

    # Confidence details in a styled bar with colored badge
    if pick['confidence']:
        confidence_badge = get_confidence_badge(pick['confidence'])
        html += f"<div style='background: #f8f9fa; padding: 10px 15px; border-radius: 6px; font-size: 0.9em; color: #555; margin-bottom: 15px;'>{confidence_badge} {pick['confidence']}</div>\n\n"

    # Description
    if pick['description']:
        html += f"<div style='color: #666; line-height: 1.7; margin-bottom: 12px;'>{pick['description'].strip()}</div>\n\n"

    # Changes note in lighter style
    if pick['changes']:
        html += f"<div style='font-size: 0.85em; color: #999; font-style: italic; padding-top: 12px; border-top: 1px dashed #e0e0e0; margin-top: 10px;'>💡 {pick['changes']}</div>\n\n"

    html += "</div>\n\n"
    return html


def parse_last_n_days_results(sport_key, days=5):
    """Parse last N days of results for a sport and return combined record with units."""
    results_dir = os.path.join("bot_results", sport_key)
    results_files = sorted(glob(os.path.join(results_dir, f"{sport_key}_daily_results_*.txt")))

    if not results_files:
        return {"wins": 0, "losses": 0, "units_won": 0, "units_lost": 0, "net_units": 0}

    # Get last N files
    recent_files = results_files[-days:] if len(results_files) >= days else results_files

    total_wins = 0
    total_losses = 0
    total_units_won = 0
    total_units_lost = 0

    for file_path in recent_files:
        try:
            content = read_file(file_path)

            # Parse wins and losses from the summary
            win_match = re.search(r'\*\*Total Wins:\s*(\d+)\*\*', content)
            loss_match = re.search(r'\*\*Total Losses:\s*(\d+)\*\*', content)

            if win_match:
                total_wins += int(win_match.group(1))
            if loss_match:
                total_losses += int(loss_match.group(1))

            # Parse individual picks to calculate units
            lines = content.strip().splitlines()
            current_pick = None

            for line in lines:
                stripped = line.strip()

                # Match numbered pick lines
                pick_match = re.match(r'^\d+\.\s+\*\*(.+?)\*\*', stripped)
                if pick_match:
                    if current_pick:
                        # Process previous pick
                        if current_pick["outcome"] == "WIN":
                            total_units_won += (current_pick["odds"] - 1) * current_pick["units"]
                        elif current_pick["outcome"] == "LOSS":
                            total_units_lost += current_pick["units"]

                    bet_text = pick_match.group(1)
                    odds_match = re.search(r'@\s*(\d+\.?\d*)', bet_text)
                    odds = float(odds_match.group(1)) if odds_match else 1.0

                    current_pick = {
                        "units": 1.0,
                        "odds": odds,
                        "outcome": None
                    }
                    continue

                # Extract confidence/units
                if current_pick and ('Confidence Level:' in stripped or 'Confidence:' in stripped):
                    if 'High' in stripped:
                        current_pick["units"] = 1.5
                    elif 'Medium' in stripped:
                        current_pick["units"] = 1.0
                    continue

                # Match outcome
                if current_pick and re.match(r'^\*\s+Outcome:', stripped):
                    outcome_text = re.sub(r'^\*\s+Outcome:\s*', '', stripped)
                    if "**WIN**" in outcome_text:
                        current_pick["outcome"] = "WIN"
                    elif "**LOSS**" in outcome_text:
                        current_pick["outcome"] = "LOSS"
                    elif "**PUSH**" in outcome_text:
                        current_pick["outcome"] = "PUSH"
                    elif "WIN" in outcome_text.upper() and "not a win" not in outcome_text.lower():
                        current_pick["outcome"] = "WIN"
                    elif "PUSH" in outcome_text.upper():
                        current_pick["outcome"] = "PUSH"
                    elif "LOSS" in outcome_text.upper():
                        current_pick["outcome"] = "LOSS"
                    continue

            # Don't forget last pick
            if current_pick and current_pick["outcome"]:
                if current_pick["outcome"] == "WIN":
                    total_units_won += (current_pick["odds"] - 1) * current_pick["units"]
                elif current_pick["outcome"] == "LOSS":
                    total_units_lost += current_pick["units"]

        except Exception:
            continue

    net_units = total_units_won - total_units_lost
    return {
        "wins": total_wins,
        "losses": total_losses,
        "units_won": total_units_won,
        "units_lost": total_units_lost,
        "net_units": net_units
    }


def parse_all_results(sport_key):
    """Parse all results files for a sport to get season totals with units.

    First tries to read wins/losses from total_results_summary.txt for accuracy,
    then parses individual files for units calculation.
    """
    # Read wins/losses from total_results_summary.txt
    summary_path = os.path.join("bot_results", "total_results_summary.txt")
    total_wins = 0
    total_losses = 0

    if os.path.exists(summary_path):
        try:
            summary_content = read_file(summary_path)
            # Find the sport section
            sport_upper = sport_key.upper()
            sport_section_match = re.search(rf'{sport_upper}:.*?TOTAL:\s*(\d+)\s*wins?,\s*(\d+)\s*losses?',
                                           summary_content, re.DOTALL | re.IGNORECASE)
            if sport_section_match:
                total_wins = int(sport_section_match.group(1))
                total_losses = int(sport_section_match.group(2))
        except Exception:
            pass  # Fall back to parsing individual files

    # Parse individual results files for units calculation
    results_dir = os.path.join("bot_results", sport_key)
    results_files = sorted(glob(os.path.join(results_dir, f"{sport_key}_daily_results_*.txt")))

    if not results_files:
        return {"wins": total_wins, "losses": total_losses, "units_won": 0, "units_lost": 0, "net_units": 0}

    total_units_won = 0
    total_units_lost = 0

    for file_path in results_files:
        try:
            content = read_file(file_path)

            # Parse individual picks to calculate units
            lines = content.strip().splitlines()
            current_pick = None

            for line in lines:
                stripped = line.strip()

                # Match numbered pick lines
                pick_match = re.match(r'^\d+\.\s+\*\*(.+?)\*\*', stripped)
                if pick_match:
                    if current_pick:
                        # Process previous pick
                        if current_pick["outcome"] == "WIN":
                            total_units_won += (current_pick["odds"] - 1) * current_pick["units"]
                        elif current_pick["outcome"] == "LOSS":
                            total_units_lost += current_pick["units"]

                    bet_text = pick_match.group(1)
                    odds_match = re.search(r'@\s*(\d+\.?\d*)', bet_text)
                    odds = float(odds_match.group(1)) if odds_match else 1.0

                    current_pick = {
                        "units": 1.0,
                        "odds": odds,
                        "outcome": None
                    }
                    continue

                # Extract confidence/units
                if current_pick and ('Confidence Level:' in stripped or 'Confidence:' in stripped):
                    if 'High' in stripped:
                        current_pick["units"] = 1.5
                    elif 'Medium' in stripped:
                        current_pick["units"] = 1.0
                    continue

                # Match outcome
                if current_pick and re.match(r'^\*\s+Outcome:', stripped):
                    outcome_text = re.sub(r'^\*\s+Outcome:\s*', '', stripped)
                    if "**WIN**" in outcome_text:
                        current_pick["outcome"] = "WIN"
                    elif "**LOSS**" in outcome_text:
                        current_pick["outcome"] = "LOSS"
                    elif "**PUSH**" in outcome_text:
                        current_pick["outcome"] = "PUSH"
                    elif "WIN" in outcome_text.upper() and "not a win" not in outcome_text.lower():
                        current_pick["outcome"] = "WIN"
                    elif "PUSH" in outcome_text.upper():
                        current_pick["outcome"] = "PUSH"
                    elif "LOSS" in outcome_text.upper():
                        current_pick["outcome"] = "LOSS"
                    continue

            # Don't forget last pick
            if current_pick and current_pick["outcome"]:
                if current_pick["outcome"] == "WIN":
                    total_units_won += (current_pick["odds"] - 1) * current_pick["units"]
                elif current_pick["outcome"] == "LOSS":
                    total_units_lost += current_pick["units"]

        except Exception:
            continue

    net_units = total_units_won - total_units_lost
    return {
        "wins": total_wins,
        "losses": total_losses,
        "units_won": total_units_won,
        "units_lost": total_units_lost,
        "net_units": net_units
    }


def parse_yesterday_results(sport_key):
    """Parse yesterday's results file for a sport and extract summary."""
    results_dir = os.path.join("bot_results", sport_key)
    results_files = sorted(glob(os.path.join(results_dir, f"{sport_key}_daily_results_*.txt")))

    if not results_files:
        return None

    # Get the most recent results file
    latest_results_file = max(results_files, key=os.path.getctime)

    try:
        content = read_file(latest_results_file)

        # Extract date from filename
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', os.path.basename(latest_results_file))
        results_date = date_match.group(1) if date_match else "Unknown"

        # Parse wins and losses from the summary
        wins = 0
        losses = 0

        # Look for "Total Wins: X" and "Total Losses: Y"
        win_match = re.search(r'\*\*Total Wins:\s*(\d+)\*\*', content)
        loss_match = re.search(r'\*\*Total Losses:\s*(\d+)\*\*', content)

        if win_match:
            wins = int(win_match.group(1))
        if loss_match:
            losses = int(loss_match.group(1))

        # Extract individual picks with their outcomes, units, and odds
        picks = []
        lines = content.strip().splitlines()
        current_pick = None

        for line in lines:
            stripped = line.strip()

            # Match numbered pick lines like "1. **Washington Capitals ML vs Utah @ 1.83**"
            pick_match = re.match(r'^\d+\.\s+\*\*(.+?)\*\*', stripped)
            if pick_match:
                if current_pick:
                    picks.append(current_pick)

                bet_text = pick_match.group(1)
                # Extract odds from bet text (e.g., "@ 1.83" or "@1.94")
                odds_match = re.search(r'@\s*(\d+\.?\d*)', bet_text)
                odds = float(odds_match.group(1)) if odds_match else 1.0

                current_pick = {
                    "bet": bet_text,
                    "result": None,
                    "outcome": None,
                    "units": 1.0,  # Default to 1 unit
                    "confidence": None,
                    "odds": odds
                }
                continue

            # Extract confidence level and units from confidence line
            if current_pick and ('Confidence Level:' in stripped or 'Confidence:' in stripped):
                # Extract units (1u or 1.5u)
                units_match = re.search(r'Units?:\s*(\d+\.?\d*)u', stripped, re.IGNORECASE)
                if units_match:
                    current_pick["units"] = float(units_match.group(1))

                # Extract confidence level
                if 'High' in stripped:
                    current_pick["confidence"] = "High"
                    current_pick["units"] = 1.5  # High confidence = 1.5 units
                elif 'Medium' in stripped:
                    current_pick["confidence"] = "Medium"
                    current_pick["units"] = 1.0  # Medium confidence = 1 unit
                continue

            # Match actual result lines (with * bullet)
            if current_pick and re.match(r'^\*\s+Actual Result:', stripped):
                current_pick["result"] = re.sub(r'^\*\s+Actual Result:\s*', '', stripped)
                continue

            # Match outcome lines (WIN/LOSS/PUSH) (with * bullet)
            if current_pick and re.match(r'^\*\s+Outcome:', stripped):
                outcome_text = re.sub(r'^\*\s+Outcome:\s*', '', stripped)
                # Check for **WIN**, **LOSS**, or **PUSH** (bolded outcomes are the actual results)
                if "**WIN**" in outcome_text:
                    current_pick["outcome"] = "WIN"
                elif "**LOSS**" in outcome_text:
                    current_pick["outcome"] = "LOSS"
                elif "**PUSH**" in outcome_text:
                    current_pick["outcome"] = "PUSH"
                # Fallback to uppercase check only if bolded version not found
                elif "WIN" in outcome_text.upper() and "**LOSS**" not in outcome_text:
                    # Make sure it's actually indicating a win and not "not a win"
                    if "not a win" not in outcome_text.lower():
                        current_pick["outcome"] = "WIN"
                elif "PUSH" in outcome_text.upper():
                    current_pick["outcome"] = "PUSH"
                elif "LOSS" in outcome_text.upper():
                    current_pick["outcome"] = "LOSS"
                continue

        # Don't forget the last pick
        if current_pick:
            picks.append(current_pick)

        # Calculate total units won/lost based on odds
        # Win = profit only (odds - 1) * units
        # Loss = -units
        units_won = sum((pick["odds"] - 1) * pick["units"] for pick in picks if pick["outcome"] == "WIN")
        units_lost = sum(pick["units"] for pick in picks if pick["outcome"] == "LOSS")
        net_units = units_won - units_lost

        return {
            "date": results_date,
            "wins": wins,
            "losses": losses,
            "picks": picks,
            "units_won": units_won,
            "units_lost": units_lost,
            "net_units": net_units
        }
    except Exception as e:
        print(f"Error parsing results for {sport_key}: {e}")
        return None


def format_compact_stats_banner(nhl_results, nba_results, nba_record, nhl_record):
    """Format yesterday's results in a compact grid of square tiles."""
    md = ""

    # Add yesterday's results if available
    if (nhl_results and nhl_results.get("picks")) or (nba_results and nba_results.get("picks")):
        yesterday_date = None
        if nhl_results and nhl_results.get("date"):
            yesterday_date = nhl_results["date"]
        elif nba_results and nba_results.get("date"):
            yesterday_date = nba_results.get("date")

        nice_date = format_date_nice(yesterday_date) if yesterday_date else "Yesterday"

        md += "<div class='yesterday-section'>\n"

        if nhl_results and nhl_results.get("picks"):
            md += "<h3 style='color: #dc2626; margin-top: 0; margin-bottom: 15px; font-size: 1.2em; font-weight: 700;'>🏒 NHL Results</h3>\n\n"
            md += "<div class='results-grid'>\n"

            for i, pick in enumerate(nhl_results["picks"], 1):
                if pick["outcome"] == "WIN":
                    outcome_emoji = "✅"
                    tile_class = "result-tile result-tile-win"
                elif pick["outcome"] == "PUSH":
                    outcome_emoji = "↔️"
                    tile_class = "result-tile result-tile-push"
                else:  # LOSS
                    outcome_emoji = "❌"
                    tile_class = "result-tile result-tile-loss"

                # Shorten bet text for compact display
                bet_short = pick['bet']
                # Remove odds from display to save space
                bet_short = re.sub(r'\s*@\s*\d+\.?\d*', '', bet_short)
                # Truncate long team names if needed
                if len(bet_short) > 50:
                    bet_short = bet_short[:47] + "..."

                md += f"<div class='{tile_class}'>\n"
                md += f"<div class='result-tile-emoji'>{outcome_emoji}</div>\n"
                md += f"<div class='result-tile-bet'>{bet_short}</div>\n"
                md += "</div>\n"

            md += "</div>\n\n"

        if nba_results and nba_results.get("picks"):
            md += "<h3 style='color: #ea580c; margin-top: 25px; margin-bottom: 15px; font-size: 1.2em; font-weight: 700;'>🏀 NBA Results</h3>\n\n"
            md += "<div class='results-grid'>\n"

            for i, pick in enumerate(nba_results["picks"], 1):
                if pick["outcome"] == "WIN":
                    outcome_emoji = "✅"
                    tile_class = "result-tile result-tile-win"
                elif pick["outcome"] == "PUSH":
                    outcome_emoji = "↔️"
                    tile_class = "result-tile result-tile-push"
                else:  # LOSS
                    outcome_emoji = "❌"
                    tile_class = "result-tile result-tile-loss"

                # Shorten bet text for compact display
                bet_short = pick['bet']
                # Remove odds from display to save space
                bet_short = re.sub(r'\s*@\s*\d+\.?\d*', '', bet_short)
                # Truncate long team names if needed
                if len(bet_short) > 50:
                    bet_short = bet_short[:47] + "..."

                md += f"<div class='{tile_class}'>\n"
                md += f"<div class='result-tile-emoji'>{outcome_emoji}</div>\n"
                md += f"<div class='result-tile-bet'>{bet_short}</div>\n"
                md += "</div>\n"

            md += "</div>\n\n"

        md += "</div>\n\n"

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

    # Render picks as modern card-style layout
    md += "<div class='featured-grid'>\n\n"

    for pick in picks:
        header = pick["header"]
        body_lines = pick["body"]

        # Extract the sport emoji for the card accent
        if "NHL" in header:
            sport_badge_class = "badge-nhl"
            sport_label = "NHL"
        elif "NBA" in header:
            sport_badge_class = "badge-nba"
            sport_label = "NBA"
        else:
            sport_badge_class = "badge-featured"
            sport_label = "Featured"

        # Extract the bet line
        bet_line = header
        for tag in ["🎯 PICK #1 – NHL 🏒", "🎯 PICK #2 – NBA 🏀",
                     "🎯 PICK #1 – NBA 🏀", "🎯 PICK #2 – NHL 🏒",
                     "🎯 PICK #1 –", "🎯 PICK #2 –"]:
            if bet_line.startswith(tag):
                bet_line = bet_line[len(tag):].strip()
                break

        # Determine pick number
        pick_num = "1" if "#1" in header else "2"

        # Parse confidence and description
        confidence_text = ""
        description_text = ""
        odds_value = None
        for line in body_lines:
            if "Confidence Level:" in line or "Confidence:" in line:
                confidence_text = line
            else:
                description_text += " " + line
                # Try to extract odds from the description
                if not odds_value:
                    # Look for patterns like "@ 1.77" or "at 1.91"
                    odds_match = re.search(r'[@at]\s*(\d+\.\d+)', line)
                    if odds_match:
                        odds_value = odds_match.group(1)

        # Add odds to bet line if found and not already present
        if odds_value and '@' not in bet_line:
            bet_line = f"{bet_line} @ {odds_value}"

        # Create card
        md += "<div class='pick-card'>\n"
        md += f"<div class='pick-badge {sport_badge_class}'>PICK #{pick_num} — {sport_label}</div>\n"
        md += f"<div class='pick-title'>{bet_line}</div>\n"

        # Add confidence and meta info
        if confidence_text:
            # Extract confidence level
            conf_level = "MEDIUM"
            if "High" in confidence_text:
                conf_level = "HIGH"
            elif "Low" in confidence_text:
                conf_level = "LOW"

            confidence_badge_html = f"<span class='confidence-{conf_level.lower()}'>{conf_level}</span>"
            md += f"<div class='pick-meta'>{confidence_badge_html} {confidence_text}</div>\n"

        if description_text:
            md += f"<div class='pick-description'>{description_text.strip()}</div>\n"

        md += "</div>\n\n"

    md += "</div>\n\n"

    return md


def get_confidence_badge(text):
    """Return a colored badge for confidence level."""
    text_upper = text.upper()
    if "HIGH" in text_upper:
        return "<span style='display: inline-block; background: #28a745; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.75em; font-weight: bold; margin-right: 8px;'>HIGH</span>"
    elif "MEDIUM" in text_upper:
        return "<span style='display: inline-block; background: #ffc107; color: #333; padding: 2px 8px; border-radius: 10px; font-size: 0.75em; font-weight: bold; margin-right: 8px;'>MEDIUM</span>"
    elif "LOW" in text_upper:
        return "<span style='display: inline-block; background: #6c757d; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.75em; font-weight: bold; margin-right: 8px;'>LOW</span>"
    return ""


def update_latest_predictions():
    predictions_dir = "predictions"
    sports_config = [
        {"key": "nhl", "name": "NHL", "emoji": "🏒"},
        {"key": "nba", "name": "NBA", "emoji": "🏀"},
    ]
    output_md = "docs/index.md"
    output_html = "docs/index.html"  # Add HTML output for Vercel
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
    content = ""

    # ── Add HTML head with title and meta tags ──
    content += "<!DOCTYPE html>\n"
    content += "<html lang='en'>\n"
    content += "<head>\n"
    content += "<meta charset='UTF-8'>\n"
    content += "<meta name='viewport' content='width=device-width, initial-scale=1.0'>\n"
    content += "<title>Parieur Discipliné - AI Betting Predictions</title>\n"
    content += "<meta name='description' content='AI-powered sports betting predictions for NHL and NBA. Daily picks with analysis and edge calculation.'>\n"
    content += "<link rel='icon' type='image/png' href='parieur_discipline.png'>\n"
    content += "</head>\n"
    content += "<body>\n\n"

    # ── Sports Blog CSS ──
    content += "<style>\n"
    content += "* { margin: 0; padding: 0; box-sizing: border-box; }\n"
    content += "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #1a1a1a; background: #f5f7fa; }\n"
    content += ".main-content { max-width: 100% !important; padding: 0 !important; }\n"
    content += ".blog-container { width: 100%; margin: 0; background: white; }\n"
    content += ".hero-section { background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%); color: white; padding: 50px 40px; text-align: center; position: relative; overflow: hidden; }\n"
    content += ".hero-section::before { content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: url('data:image/svg+xml,%3Csvg width=\"60\" height=\"60\" xmlns=\"http://www.w3.org/2000/svg\"%3E%3Cpath d=\"M0 0h60v60H0z\" fill=\"none\"/%3E%3Cpath d=\"M30 0l30 30-30 30L0 30z\" fill=\"%23ffffff\" fill-opacity=\".03\"/%3E%3C/svg%3E'); opacity: 0.3; }\n"
    content += ".hero-content { position: relative; z-index: 1; }\n"
    content += ".hero-logo { width: 170px; height: 170px; border-radius: 50%; margin: 0 auto 20px auto; display: block; border: 4px solid rgba(255,255,255,0.3); box-shadow: 0 4px 15px rgba(0,0,0,0.2); }\n"
    content += ".blog-title { font-size: 3em; font-weight: 800; margin-bottom: 15px; letter-spacing: -1px; text-shadow: 0 2px 10px rgba(0,0,0,0.2); }\n"
    content += ".blog-subtitle { font-size: 1.3em; opacity: 0.95; margin-bottom: 10px; font-weight: 300; }\n"
    content += ".blog-date { font-size: 1.1em; opacity: 0.85; font-weight: 500; }\n"
    content += ".blog-update-time { font-size: 0.9em; opacity: 0.75; margin-top: 10px; }\n"
    content += ".content-wrapper { padding: 0 60px 40px 60px; max-width: 1600px; margin: 0 auto; }\n"
    content += ".stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 20px; margin: -40px auto 40px auto; padding: 0 60px; max-width: 1600px; position: relative; z-index: 10; }\n"
    content += ".stat-card { background: white; border-radius: 12px; padding: 25px 20px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.08); transition: transform 0.2s, box-shadow 0.2s; border: 1px solid #e8ecf1; }\n"
    content += ".stat-card:hover { transform: translateY(-5px); box-shadow: 0 8px 25px rgba(0,0,0,0.12); }\n"
    content += ".stat-label { font-size: 0.8em; color: #6b7280; text-transform: uppercase; font-weight: 700; letter-spacing: 1px; margin-bottom: 10px; }\n"
    content += ".stat-value { font-size: 2.5em; font-weight: 800; margin-bottom: 8px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }\n"
    content += ".stat-record { font-size: 0.95em; color: #4b5563; font-weight: 500; }\n"
    content += ".nav-tabs { display: flex; gap: 10px; margin: 30px 0; padding: 10px; background: #f9fafb; border-radius: 12px; flex-wrap: wrap; }\n"
    content += ".nav-tab { flex: 1; min-width: 120px; padding: 12px 20px; background: white; border: 2px solid #e5e7eb; border-radius: 8px; text-decoration: none; text-align: center; font-weight: 600; font-size: 0.95em; transition: all 0.2s; color: #374151; }\n"
    content += ".nav-tab:hover { border-color: #667eea; color: #667eea; transform: translateY(-2px); box-shadow: 0 4px 10px rgba(102,126,234,0.1); }\n"
    content += ".section-header { margin: 50px 0 30px 0; padding-bottom: 15px; border-bottom: 3px solid #e5e7eb; }\n"
    content += ".section-title { font-size: 2.2em; font-weight: 800; color: #111827; display: flex; align-items: center; gap: 12px; }\n"
    content += ".section-subtitle { font-size: 0.95em; color: #6b7280; margin-top: 8px; font-weight: 400; }\n"
    content += ".featured-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 30px; margin: 25px 0; }\n"
    content += ".pick-card { background: linear-gradient(135deg, #f9fafb 0%, #ffffff 100%); border-radius: 12px; padding: 25px; border: 2px solid #e5e7eb; transition: all 0.3s; }\n"
    content += ".pick-card:hover { border-color: #667eea; box-shadow: 0 8px 25px rgba(102,126,234,0.15); transform: translateY(-3px); }\n"
    content += ".pick-badge { display: inline-block; padding: 6px 12px; border-radius: 6px; font-size: 0.75em; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px; }\n"
    content += ".badge-nhl { background: #fee2e2; color: #dc2626; }\n"
    content += ".badge-nba { background: #fed7aa; color: #ea580c; }\n"
    content += ".badge-featured { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }\n"
    content += ".pick-title { font-size: 1.25em; font-weight: 700; color: #111827; margin-bottom: 15px; line-height: 1.4; }\n"
    content += ".pick-meta { display: inline-block; padding: 8px 14px; background: #f3f4f6; border-radius: 8px; font-size: 0.85em; margin-bottom: 12px; }\n"
    content += ".confidence-high { display: inline-block; background: #10b981; color: white; padding: 4px 10px; border-radius: 5px; font-size: 0.75em; font-weight: 700; margin-right: 8px; }\n"
    content += ".confidence-medium { display: inline-block; background: #f59e0b; color: white; padding: 4px 10px; border-radius: 5px; font-size: 0.75em; font-weight: 700; margin-right: 8px; }\n"
    content += ".pick-description { color: #4b5563; line-height: 1.7; font-size: 0.95em; }\n"
    content += ".yesterday-section { background: #f9fafb; border-radius: 12px; padding: 30px; margin: 40px 0; border: 1px solid #e5e7eb; }\n"
    content += ".result-card { background: white; border-radius: 10px; padding: 20px; margin-bottom: 15px; border-left: 5px solid #e5e7eb; transition: all 0.2s; }\n"
    content += ".result-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }\n"
    content += ".result-win { border-left-color: #10b981; background: linear-gradient(90deg, #ecfdf5 0%, #ffffff 100%); }\n"
    content += ".result-loss { border-left-color: #ef4444; background: linear-gradient(90deg, #fef2f2 0%, #ffffff 100%); }\n"
    content += ".result-push { border-left-color: #f59e0b; background: linear-gradient(90deg, #fffbeb 0%, #ffffff 100%); }\n"
    content += ".results-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; margin-bottom: 20px; }\n"
    content += ".result-tile { background: white; border-radius: 8px; padding: 15px; text-align: center; border: 2px solid #e5e7eb; transition: all 0.2s; min-height: 100px; display: flex; flex-direction: column; justify-content: center; align-items: center; }\n"
    content += ".result-tile:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }\n"
    content += ".result-tile-win { border-color: #10b981; background: linear-gradient(135deg, #ecfdf5 0%, #ffffff 100%); }\n"
    content += ".result-tile-loss { border-color: #ef4444; background: linear-gradient(135deg, #fef2f2 0%, #ffffff 100%); }\n"
    content += ".result-tile-push { border-color: #f59e0b; background: linear-gradient(135deg, #fffbeb 0%, #ffffff 100%); }\n"
    content += ".result-tile-emoji { font-size: 2em; margin-bottom: 8px; }\n"
    content += ".result-tile-bet { font-size: 0.85em; color: #374151; font-weight: 500; line-height: 1.3; }\n"
    content += ".result-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }\n"
    content += ".result-badge { padding: 4px 10px; border-radius: 5px; font-size: 0.75em; font-weight: 700; text-transform: uppercase; }\n"
    content += ".badge-win { background: #10b981; color: white; }\n"
    content += ".badge-loss { background: #ef4444; color: white; }\n"
    content += ".badge-push { background: #f59e0b; color: white; }\n"
    content += ".result-title { font-weight: 600; color: #111827; font-size: 1.05em; }\n"
    content += ".result-score { color: #6b7280; font-size: 0.9em; padding-left: 50px; }\n"
    content += "#back-to-top { position: fixed; bottom: 30px; right: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 14px 18px; border-radius: 50%; box-shadow: 0 4px 20px rgba(102,126,234,0.4); cursor: pointer; font-size: 1.3em; display: none; z-index: 1000; border: none; transition: all 0.3s; }\n"
    content += "#back-to-top:hover { transform: translateY(-5px); box-shadow: 0 6px 30px rgba(102,126,234,0.6); }\n"
    content += "@media (max-width: 768px) { .content-wrapper { padding: 0 20px 30px 20px; } .stats-grid { margin: -30px 15px 30px 15px; grid-template-columns: 1fr; gap: 10px; max-width: 100%; padding: 0 15px; } .stat-card { padding: 15px 12px; } .stat-label { font-size: 0.75em; } .stat-value { font-size: 2.2em; } .stat-record { font-size: 0.9em; } .blog-title { font-size: 1.8em; } .blog-subtitle { font-size: 1em; } .blog-date { font-size: 0.95em; } .blog-update-time { font-size: 0.8em; } .hero-logo { width: 90px; height: 90px; margin-bottom: 15px; } .section-title { font-size: 1.5em; } .section-subtitle { font-size: 0.85em; } .featured-grid { grid-template-columns: 1fr; gap: 15px; } .pick-card { padding: 20px; } .pick-title { font-size: 1.1em; } .pick-badge { font-size: 0.7em; padding: 5px 10px; } .pick-meta { font-size: 0.8em; padding: 6px 12px; } .pick-description { font-size: 0.9em; } .hero-section { padding: 30px 20px; } .nav-tabs { gap: 8px; padding: 8px; } .nav-tab { padding: 10px 12px; font-size: 0.85em; min-width: 100px; } .result-card { padding: 15px; } .result-title { font-size: 0.95em; } .result-score { font-size: 0.85em; padding-left: 40px; } .results-grid { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px; } .result-tile { min-height: 90px; padding: 12px; } .result-tile-emoji { font-size: 1.8em; } .result-tile-bet { font-size: 0.8em; } .yesterday-section { padding: 20px; } #back-to-top { bottom: 20px; right: 20px; padding: 12px 16px; font-size: 1.1em; } }\n"
    content += "</style>\n\n"

    content += "<div class='blog-container'>\n\n"

    # ── Hero Section ──
    content += "<div class='hero-section'>\n"
    content += "<div class='hero-content'>\n"
    content += "<img src='parieur_discipline.png' alt='Parieur Discipliné' class='hero-logo'>\n"
    content += "<div class='blog-title'>🎯 Parieur Discipliné</div>\n"
    content += "<div class='blog-subtitle'>AI-Powered NHL & NBA Betting Predictions</div>\n"
    content += f"<div class='blog-date'>{nice_date}</div>\n"
    content += "<div class='blog-update-time'>📡 Updated daily at 12:00 PM ET</div>\n"
    content += "</div>\n"
    content += "</div>\n\n"

    # ── Quick Stats Row ──
    nhl_yesterday = parse_yesterday_results("nhl")
    nba_yesterday = parse_yesterday_results("nba")

    # Calculate yesterday's stats including units
    yesterday_total_w = (nhl_yesterday["wins"] if nhl_yesterday else 0) + (nba_yesterday["wins"] if nba_yesterday else 0)
    yesterday_total_l = (nhl_yesterday["losses"] if nhl_yesterday else 0) + (nba_yesterday["losses"] if nba_yesterday else 0)
    yesterday_wr = f"{(yesterday_total_w / (yesterday_total_w + yesterday_total_l) * 100):.0f}%" if (yesterday_total_w + yesterday_total_l) > 0 else "N/A"

    # Calculate yesterday's units
    yesterday_units_won = (nhl_yesterday.get("units_won", 0) if nhl_yesterday else 0) + (nba_yesterday.get("units_won", 0) if nba_yesterday else 0)
    yesterday_units_lost = (nhl_yesterday.get("units_lost", 0) if nhl_yesterday else 0) + (nba_yesterday.get("units_lost", 0) if nba_yesterday else 0)
    yesterday_net_units = yesterday_units_won - yesterday_units_lost
    yesterday_units_display = f"+{yesterday_net_units:.1f}u" if yesterday_net_units >= 0 else f"{yesterday_net_units:.1f}u"

    # Calculate last 7 days stats including units
    nhl_last7 = parse_last_n_days_results("nhl", 7)
    nba_last7 = parse_last_n_days_results("nba", 7)
    last7_total_w = nhl_last7["wins"] + nba_last7["wins"]
    last7_total_l = nhl_last7["losses"] + nba_last7["losses"]
    last7_wr = f"{(last7_total_w / (last7_total_w + last7_total_l) * 100):.0f}%" if (last7_total_w + last7_total_l) > 0 else "N/A"

    # Calculate last week's units
    last7_net_units = nhl_last7["net_units"] + nba_last7["net_units"]
    last7_units_display = f"+{last7_net_units:.1f}u" if last7_net_units >= 0 else f"{last7_net_units:.1f}u"

    # Calculate season stats including units
    nhl_all = parse_all_results("nhl")
    nba_all = parse_all_results("nba")
    overall_total_w = nhl_all["wins"] + nba_all["wins"]
    overall_total_l = nhl_all["losses"] + nba_all["losses"]
    overall_wr = f"{(overall_total_w / (overall_total_w + overall_total_l) * 100):.0f}%" if (overall_total_w + overall_total_l) > 0 else "N/A"

    # Calculate season units
    season_net_units = nhl_all["net_units"] + nba_all["net_units"]
    season_units_display = f"+{season_net_units:.1f}u" if season_net_units >= 0 else f"{season_net_units:.1f}u"

    content += "<div class='stats-grid'>\n"

    # Yesterday's Win Rate Card with Units
    content += "<div class='stat-card'>\n"
    content += "<div class='stat-label'>Yesterday</div>\n"
    content += f"<div class='stat-value'>{yesterday_wr}</div>\n"
    content += f"<div class='stat-record'>{yesterday_total_w}W - {yesterday_total_l}L</div>\n"
    content += f"<div class='stat-record' style='margin-top: 5px; color: {'#10b981' if yesterday_net_units >= 0 else '#ef4444'}; font-weight: 600;'>{yesterday_units_display}</div>\n"
    content += "</div>\n"

    # Last 7 Days Win Rate Card with Units
    content += "<div class='stat-card'>\n"
    content += "<div class='stat-label'>Last Week</div>\n"
    content += f"<div class='stat-value'>{last7_wr}</div>\n"
    content += f"<div class='stat-record'>{last7_total_w}W - {last7_total_l}L</div>\n"
    content += f"<div class='stat-record' style='margin-top: 5px; color: {'#10b981' if last7_net_units >= 0 else '#ef4444'}; font-weight: 600;'>{last7_units_display}</div>\n"
    content += "</div>\n"

    # Season Win Rate Card with Units
    content += "<div class='stat-card'>\n"
    content += "<div class='stat-label'>Season</div>\n"
    content += f"<div class='stat-value'>{overall_wr}</div>\n"
    content += f"<div class='stat-record'>{overall_total_w}W - {overall_total_l}L</div>\n"
    content += f"<div class='stat-record' style='margin-top: 5px; color: {'#10b981' if season_net_units >= 0 else '#ef4444'}; font-weight: 600;'>{season_units_display}</div>\n"
    content += "</div>\n"

    # NHL Record Card with Units
    nhl_wr = f"{(nhl_all['wins'] / (nhl_all['wins'] + nhl_all['losses']) * 100):.0f}%" if (nhl_all['wins'] + nhl_all['losses']) > 0 else "N/A"
    nhl_units_display = f"+{nhl_all['net_units']:.1f}u" if nhl_all['net_units'] >= 0 else f"{nhl_all['net_units']:.1f}u"
    content += "<div class='stat-card'>\n"
    content += "<div class='stat-label'>🏒 NHL</div>\n"
    content += f"<div class='stat-value'>{nhl_wr}</div>\n"
    content += f"<div class='stat-record'>{nhl_all['wins']}W - {nhl_all['losses']}L</div>\n"
    content += f"<div class='stat-record' style='margin-top: 5px; color: {'#10b981' if nhl_all['net_units'] >= 0 else '#ef4444'}; font-weight: 600;'>{nhl_units_display}</div>\n"
    content += "</div>\n"

    # NBA Record Card with Units
    nba_wr = f"{(nba_all['wins'] / (nba_all['wins'] + nba_all['losses']) * 100):.0f}%" if (nba_all['wins'] + nba_all['losses']) > 0 else "N/A"
    nba_units_display = f"+{nba_all['net_units']:.1f}u" if nba_all['net_units'] >= 0 else f"{nba_all['net_units']:.1f}u"
    content += "<div class='stat-card'>\n"
    content += "<div class='stat-label'>🏀 NBA</div>\n"
    content += f"<div class='stat-value'>{nba_wr}</div>\n"
    content += f"<div class='stat-record'>{nba_all['wins']}W - {nba_all['losses']}L</div>\n"
    content += f"<div class='stat-record' style='margin-top: 5px; color: {'#10b981' if nba_all['net_units'] >= 0 else '#ef4444'}; font-weight: 600;'>{nba_units_display}</div>\n"
    content += "</div>\n"

    content += "</div>\n\n"

    # ── Content wrapper starts here ──
    content += "<div class='content-wrapper'>\n\n"

    # ── Navigation Tabs ──
    content += "<div class='nav-tabs'>\n"
    content += "<a href='#featured-picks' class='nav-tab'>🔥 Featured Picks</a>\n"
    content += "<a href='#nhl-predictions' class='nav-tab'>🏒 NHL</a>\n"
    content += "<a href='#nba-predictions' class='nav-tab'>🏀 NBA</a>\n"
    content += "<a href='#yesterday-results' class='nav-tab'>📋 Yesterday</a>\n"
    content += "</div>\n\n"

    # ── Dual Bet of the Day (Featured Picks) ──
    if os.path.exists(dual_bet_path):
        dual_content = read_file(dual_bet_path).strip()
        if dual_content:
            content += "<div id='featured-picks'>\n"
            content += "<div class='section-header'>\n"
            content += "<div class='section-title'>🔥 Featured Picks of the Day</div>\n"
            content += "<div class='section-subtitle'>Our top AI-selected plays with the highest edge</div>\n"
            content += "</div>\n"
            content += format_dual_bet(dual_content)
            content += "</div>\n\n"

    # ── Yesterday's Results ──
    content += "<div id='yesterday-results'>\n"
    content += "<div class='section-header'>\n"
    content += "<div class='section-title'>📋 Yesterday's Results</div>\n"
    content += f"<div class='section-subtitle'>Performance breakdown for {format_date_nice(overall_latest_date)}</div>\n"
    content += "</div>\n"
    stats_banner = format_compact_stats_banner(nhl_yesterday, nba_yesterday, nba_record, nhl_record)
    content += stats_banner
    content += "</div>\n\n"

    # ── Sport sections ──
    for cfg in sports_config:
        sport = cfg["key"]
        name = cfg["name"]
        emoji = cfg["emoji"]

        content += f"<div id='{sport}-predictions'>\n"
        content += "<div class='section-header'>\n"
        content += f"<div class='section-title'>{emoji} {name} Predictions</div>\n"
        content += f"<div class='section-subtitle'>Today's {name} picks with full analysis</div>\n"
        content += "</div>\n\n"

        latest_file = sport_files.get(sport)
        if latest_file:
            raw = read_file(latest_file)
            content += build_sport_section(raw, sport, name, emoji, records[sport])
        else:
            content += f"<p style='color: #6b7280; font-style: italic;'>No {name} predictions available today.</p>\n\n"

        content += "</div>\n\n"

    # ── Close content wrapper ──
    content += "</div>\n\n"

    # ── Close blog container ──
    content += "</div>\n\n"

    # ── Back to Top Button with JavaScript ──
    content += "<button id='back-to-top' onclick='window.scrollTo({top: 0, behavior: \"smooth\"})'>↑</button>\n\n"
    content += "<script>\n"
    content += "window.addEventListener('scroll', function() {\n"
    content += "  var btn = document.getElementById('back-to-top');\n"
    content += "  if (window.pageYOffset > 300) { btn.style.display = 'block'; }\n"
    content += "  else { btn.style.display = 'none'; }\n"
    content += "});\n"
    content += "</script>\n\n"

    # Add Vercel Analytics and Speed Insights
    content += "<script defer src='/_vercel/insights/script.js'></script>\n"
    content += "<script defer src='/_vercel/speed-insights/script.js'></script>\n\n"

    # Close HTML tags
    content += "</body>\n"
    content += "</html>\n\n"


    with open(output_md, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Updated {output_md}")

    # Also write HTML version for Vercel
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Updated {output_html}")


if __name__ == "__main__":
    update_latest_predictions()
