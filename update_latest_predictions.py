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

        # Detect a bet line (starts with ** and has @ for odds)
        if line.startswith('**') and '@' in line and 'BET OF THE DAY' not in line:
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

    # Bet line - large and bold
    html += f"<div style='font-size: 1.3em; font-weight: bold; color: #222; margin-bottom: 15px; line-height: 1.3;'>{pick['bet']}</div>\n\n"

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
    """Parse last N days of results for a sport and return combined record."""
    results_dir = os.path.join("bot_results", sport_key)
    results_files = sorted(glob(os.path.join(results_dir, f"{sport_key}_daily_results_*.txt")))

    if not results_files:
        return {"wins": 0, "losses": 0}

    # Get last N files
    recent_files = results_files[-days:] if len(results_files) >= days else results_files

    total_wins = 0
    total_losses = 0

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
        except Exception:
            continue

    return {"wins": total_wins, "losses": total_losses}


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

        # Extract individual picks with their outcomes
        picks = []
        lines = content.strip().splitlines()
        current_pick = None

        for line in lines:
            stripped = line.strip()

            # Match numbered pick lines like "1. **Washington Capitals ML..." or "1.  **Washington Capitals ML..."
            pick_match = re.match(r'^\d+\.\s+\*\*(.+?)\*\*', stripped)
            if pick_match:
                if current_pick:
                    picks.append(current_pick)
                current_pick = {
                    "bet": pick_match.group(1),
                    "result": None,
                    "outcome": None
                }
                continue

            # Match actual result lines (with * bullet)
            if current_pick and re.match(r'^\*\s+Actual Result:', stripped):
                current_pick["result"] = re.sub(r'^\*\s+Actual Result:\s*', '', stripped)
                continue

            # Match outcome lines (WIN/LOSS) (with * bullet)
            if current_pick and re.match(r'^\*\s+Outcome:', stripped):
                outcome_text = re.sub(r'^\*\s+Outcome:\s*', '', stripped)
                # Check for **WIN** or **LOSS** (bolded outcomes are the actual results)
                if "**WIN**" in outcome_text:
                    current_pick["outcome"] = "WIN"
                elif "**LOSS**" in outcome_text:
                    current_pick["outcome"] = "LOSS"
                # Fallback to uppercase check only if bolded version not found
                elif "WIN" in outcome_text.upper() and "**LOSS**" not in outcome_text:
                    # Make sure it's actually indicating a win and not "not a win"
                    if "not a win" not in outcome_text.lower():
                        current_pick["outcome"] = "WIN"
                elif "LOSS" in outcome_text.upper():
                    current_pick["outcome"] = "LOSS"
                continue

        # Don't forget the last pick
        if current_pick:
            picks.append(current_pick)

        return {
            "date": results_date,
            "wins": wins,
            "losses": losses,
            "picks": picks
        }
    except Exception as e:
        print(f"Error parsing results for {sport_key}: {e}")
        return None


def format_compact_stats_banner(nhl_results, nba_results, nba_record, nhl_record):
    """Format a compact stats banner with collapsible yesterday's details."""
    md = ""

    # Add collapsible detailed yesterday's results if available
    if (nhl_results and nhl_results.get("picks")) or (nba_results and nba_results.get("picks")):
        yesterday_date = None
        if nhl_results and nhl_results.get("date"):
            yesterday_date = nhl_results["date"]
        elif nba_results and nba_results.get("date"):
            yesterday_date = nba_results.get("date")

        nice_date = format_date_nice(yesterday_date) if yesterday_date else "Yesterday"

        md += "<details style='margin: 20px 0; border: 2px solid #e0e0e0; border-radius: 8px; overflow: hidden;'>\n"
        md += f"<summary style='cursor:pointer; padding: 15px; background: #f8f9fa; font-weight: bold; color: #667eea; font-size: 1.1em;'><span style='font-size:1.2em;'>📋</span> View Yesterday's Detailed Results ({nice_date})</summary>\n\n"
        md += "<div style='padding: 20px; background: white;'>\n\n"

        if nhl_results and nhl_results.get("picks"):
            md += "<h3 style='color: #E74C3C; margin-top: 0; margin-bottom: 15px; display: flex; align-items: center; gap: 8px;'><span>🏒</span> NHL Results</h3>\n\n"

            for i, pick in enumerate(nhl_results["picks"], 1):
                outcome_emoji = "✅" if pick["outcome"] == "WIN" else "❌"
                outcome_color = "#28a745" if pick["outcome"] == "WIN" else "#dc3545"
                outcome_bg = "#28a74515" if pick["outcome"] == "WIN" else "#dc354515"
                outcome_text = "WIN" if pick["outcome"] == "WIN" else "LOSS"

                md += f"<div style='background: {outcome_bg}; border-left: 4px solid {outcome_color}; padding: 15px; border-radius: 6px; margin-bottom: 12px;'>\n"
                md += f"<div style='display: flex; align-items: center; gap: 10px; margin-bottom: 8px;'>\n"
                md += f"<span style='font-size: 1.5em;'>{outcome_emoji}</span>\n"
                md += f"<span style='display: inline-block; background: {outcome_color}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 0.75em; font-weight: bold;'>{outcome_text}</span>\n"
                md += f"<span style='font-weight: bold; color: #333;'>{pick['bet']}</span>\n"
                md += f"</div>\n"
                if pick.get("result"):
                    md += f"<div style='color: #666; font-size: 0.9em; padding-left: 45px;'>{pick['result']}</div>\n"
                md += f"</div>\n\n"

        if nba_results and nba_results.get("picks"):
            md += "<h3 style='color: #E67E22; margin-bottom: 15px; display: flex; align-items: center; gap: 8px;'><span>🏀</span> NBA Results</h3>\n\n"

            for i, pick in enumerate(nba_results["picks"], 1):
                outcome_emoji = "✅" if pick["outcome"] == "WIN" else "❌"
                outcome_color = "#28a745" if pick["outcome"] == "WIN" else "#dc3545"
                outcome_bg = "#28a74515" if pick["outcome"] == "WIN" else "#dc354515"
                outcome_text = "WIN" if pick["outcome"] == "WIN" else "LOSS"

                md += f"<div style='background: {outcome_bg}; border-left: 4px solid {outcome_color}; padding: 15px; border-radius: 6px; margin-bottom: 12px;'>\n"
                md += f"<div style='display: flex; align-items: center; gap: 10px; margin-bottom: 8px;'>\n"
                md += f"<span style='font-size: 1.5em;'>{outcome_emoji}</span>\n"
                md += f"<span style='display: inline-block; background: {outcome_color}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 0.75em; font-weight: bold;'>{outcome_text}</span>\n"
                md += f"<span style='font-weight: bold; color: #333;'>{pick['bet']}</span>\n"
                md += f"</div>\n"
                if pick.get("result"):
                    md += f"<div style='color: #666; font-size: 0.9em; padding-left: 45px;'>{pick['result']}</div>\n"
                md += f"</div>\n\n"

        md += "</div>\n\n"
        md += "</details>\n\n"

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
    md += "<div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;'>\n\n"

    for pick in picks:
        header = pick["header"]
        body_lines = pick["body"]

        # Extract the sport emoji for the card accent
        if "NHL" in header:
            sport_accent = "🏒"
            sport_color = "#E74C3C"
        elif "NBA" in header:
            sport_accent = "🏀"
            sport_color = "#E67E22"
        else:
            sport_accent = "🎯"
            sport_color = "#667eea"

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
        sport_label = "NHL" if "NHL" in header else "NBA"

        # Parse confidence and description
        confidence_text = ""
        description_text = ""
        for line in body_lines:
            if "Confidence Level:" in line or "Confidence:" in line:
                confidence_text = line
            else:
                description_text += " " + line

        # Create card
        md += f"<div style='background: linear-gradient(135deg, {sport_color}15 0%, {sport_color}05 100%); border-left: 4px solid {sport_color}; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>\n\n"
        md += f"<div style='font-size: 0.9em; color: {sport_color}; font-weight: bold; margin-bottom: 10px;'>{sport_accent} PICK #{pick_num} — {sport_label}</div>\n\n"
        md += f"<div style='font-size: 1.2em; font-weight: bold; color: #333; margin-bottom: 15px;'>{bet_line}</div>\n\n"

        # Add confidence bar with badge
        if confidence_text:
            confidence_badge = get_confidence_badge(confidence_text)
            md += f"<div style='background: #f8f9fa; padding: 10px 15px; border-radius: 6px; font-size: 0.9em; margin-bottom: 15px;'>{confidence_badge} {confidence_text}</div>\n\n"

        if description_text:
            md += f"<div style='color: #666; line-height: 1.6;'>{description_text.strip()}</div>\n\n"
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

    # ── Add max-width wrapper and back-to-top button ──
    content += "<style>\n"
    content += ".content-wrapper { max-width: 1200px; margin: 0 auto; }\n"
    content += "#back-to-top { position: fixed; bottom: 30px; right: 30px; background: #667eea; color: white; padding: 12px 16px; border-radius: 50%; box-shadow: 0 4px 12px rgba(0,0,0,0.2); cursor: pointer; font-size: 1.2em; display: none; z-index: 1000; border: none; }\n"
    content += "#back-to-top:hover { background: #5568d3; transform: translateY(-2px); transition: all 0.3s; }\n"
    content += "@media (max-width: 768px) { .content-wrapper { padding: 0 15px; } #back-to-top { bottom: 20px; right: 20px; padding: 10px 14px; } }\n"
    content += "</style>\n\n"

    content += "<div class='content-wrapper'>\n\n"

    # ── Hero Header with Today's Date ──
    content += f"<div style='text-align: center; padding: 30px 0; border-bottom: 3px solid #667eea;'>\n"
    content += f"<h1 style='font-size: 2.5em; margin: 0; color: #667eea;'>📰 Daily Picks</h1>\n"
    content += f"<p style='font-size: 1.4em; color: #666; margin: 10px 0;'>{nice_date}</p>\n"
    content += f"<p style='font-size: 0.9em; color: #999; margin-top: 8px;'>🕐 Updated daily at 12:00 PM (Noon) with the latest picks</p>\n"
    content += f"</div>\n\n"

    # ── Quick Navigation Menu ──
    content += "<div style='background: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px 20px; margin: 20px 0; text-align: center;'>\n"
    content += "<div style='font-size: 0.9em; color: #666; margin-bottom: 8px;'>⚡ Quick Navigation</div>\n"
    content += "<div style='display: flex; flex-wrap: wrap; justify-content: center; gap: 10px;'>\n"
    content += "<a href='#featured-picks' style='background: white; border: 1px solid #ddd; padding: 8px 16px; border-radius: 20px; text-decoration: none; color: #667eea; font-weight: 600; font-size: 0.9em;'>🔥 Featured Picks</a>\n"
    content += "<a href='#nhl-predictions' style='background: white; border: 1px solid #ddd; padding: 8px 16px; border-radius: 20px; text-decoration: none; color: #E74C3C; font-weight: 600; font-size: 0.9em;'>🏒 NHL</a>\n"
    content += "<a href='#nba-predictions' style='background: white; border: 1px solid #ddd; padding: 8px 16px; border-radius: 20px; text-decoration: none; color: #E67E22; font-weight: 600; font-size: 0.9em;'>🏀 NBA</a>\n"
    content += "<a href='#yesterday-results' style='background: white; border: 1px solid #ddd; padding: 8px 16px; border-radius: 20px; text-decoration: none; color: #666; font-weight: 600; font-size: 0.9em;'>📋 Yesterday</a>\n"
    content += "</div>\n"
    content += "</div>\n\n"

    # ── Quick Stats Row ──
    nhl_yesterday = parse_yesterday_results("nhl")
    nba_yesterday = parse_yesterday_results("nba")

    # Calculate yesterday's stats
    yesterday_total_w = (nhl_yesterday["wins"] if nhl_yesterday else 0) + (nba_yesterday["wins"] if nba_yesterday else 0)
    yesterday_total_l = (nhl_yesterday["losses"] if nhl_yesterday else 0) + (nba_yesterday["losses"] if nba_yesterday else 0)
    yesterday_wr = f"{(yesterday_total_w / (yesterday_total_w + yesterday_total_l) * 100):.0f}%" if (yesterday_total_w + yesterday_total_l) > 0 else "N/A"

    # Calculate last 5 days stats
    nhl_last5 = parse_last_n_days_results("nhl", 5)
    nba_last5 = parse_last_n_days_results("nba", 5)
    last5_total_w = nhl_last5["wins"] + nba_last5["wins"]
    last5_total_l = nhl_last5["losses"] + nba_last5["losses"]
    last5_wr = f"{(last5_total_w / (last5_total_w + last5_total_l) * 100):.0f}%" if (last5_total_w + last5_total_l) > 0 else "N/A"

    # Calculate season stats
    overall_total_w = nhl_record["wins"] + nba_record["wins"]
    overall_total_l = nhl_record["losses"] + nba_record["losses"]
    overall_wr = f"{(overall_total_w / (overall_total_w + overall_total_l) * 100):.0f}%" if (overall_total_w + overall_total_l) > 0 else "N/A"

    content += "<div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin: 30px 0;'>\n\n"

    # Yesterday's Win Rate Card
    content += "<div style='background: white; border: 2px solid #e0e0e0; border-radius: 8px; padding: 20px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>\n"
    content += "<div style='font-size: 0.85em; color: #999; text-transform: uppercase; font-weight: bold; margin-bottom: 8px;'>Yesterday</div>\n"
    content += f"<div style='font-size: 2em; font-weight: bold; color: #667eea; margin-bottom: 5px;'>{yesterday_wr}</div>\n"
    content += f"<div style='font-size: 0.9em; color: #666;'>{yesterday_total_w}W - {yesterday_total_l}L</div>\n"
    content += "</div>\n\n"

    # Last 5 Days Win Rate Card
    content += "<div style='background: white; border: 2px solid #e0e0e0; border-radius: 8px; padding: 20px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>\n"
    content += "<div style='font-size: 0.85em; color: #999; text-transform: uppercase; font-weight: bold; margin-bottom: 8px;'>Last 5 Days</div>\n"
    content += f"<div style='font-size: 2em; font-weight: bold; color: #667eea; margin-bottom: 5px;'>{last5_wr}</div>\n"
    content += f"<div style='font-size: 0.9em; color: #666;'>{last5_total_w}W - {last5_total_l}L</div>\n"
    content += "</div>\n\n"

    # Season Win Rate Card
    content += "<div style='background: white; border: 2px solid #e0e0e0; border-radius: 8px; padding: 20px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>\n"
    content += "<div style='font-size: 0.85em; color: #999; text-transform: uppercase; font-weight: bold; margin-bottom: 8px;'>Season</div>\n"
    content += f"<div style='font-size: 2em; font-weight: bold; color: #667eea; margin-bottom: 5px;'>{overall_wr}</div>\n"
    content += f"<div style='font-size: 0.9em; color: #666;'>{overall_total_w}W - {overall_total_l}L</div>\n"
    content += "</div>\n\n"

    # NHL Record Card
    nhl_wr = f"{(nhl_record['wins'] / (nhl_record['wins'] + nhl_record['losses']) * 100):.0f}%" if (nhl_record['wins'] + nhl_record['losses']) > 0 else "N/A"
    content += "<div style='background: white; border: 2px solid #e0e0e0; border-radius: 8px; padding: 20px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>\n"
    content += "<div style='font-size: 0.85em; color: #999; text-transform: uppercase; font-weight: bold; margin-bottom: 8px;'>🏒 NHL</div>\n"
    content += f"<div style='font-size: 2em; font-weight: bold; color: #E74C3C; margin-bottom: 5px;'>{nhl_wr}</div>\n"
    content += f"<div style='font-size: 0.9em; color: #666;'>{nhl_record['wins']}W - {nhl_record['losses']}L</div>\n"
    content += "</div>\n\n"

    # NBA Record Card
    nba_wr = f"{(nba_record['wins'] / (nba_record['wins'] + nba_record['losses']) * 100):.0f}%" if (nba_record['wins'] + nba_record['losses']) > 0 else "N/A"
    content += "<div style='background: white; border: 2px solid #e0e0e0; border-radius: 8px; padding: 20px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>\n"
    content += "<div style='font-size: 0.85em; color: #999; text-transform: uppercase; font-weight: bold; margin-bottom: 8px;'>🏀 NBA</div>\n"
    content += f"<div style='font-size: 2em; font-weight: bold; color: #E67E22; margin-bottom: 5px;'>{nba_wr}</div>\n"
    content += f"<div style='font-size: 0.9em; color: #666;'>{nba_record['wins']}W - {nba_record['losses']}L</div>\n"
    content += "</div>\n\n"

    content += "</div>\n\n"

    # ── Dual Bet of the Day (Featured Picks) ──
    if os.path.exists(dual_bet_path):
        dual_content = read_file(dual_bet_path).strip()
        if dual_content:
            content += "<div id='featured-picks' style='margin: 30px 0;'>\n"
            content += "<h2 style='font-size: 2em; color: #333; border-left: 5px solid #667eea; padding-left: 15px; margin-bottom: 20px;'>🔥 Featured Picks of the Day</h2>\n"
            content += format_dual_bet(dual_content)
            content += "</div>\n\n"
            content += "<hr style='border: none; border-top: 2px solid #f0f0f0; margin: 40px 0;'>\n\n"

    # ── Compact Stats Banner (Yesterday + Season Performance) ──
    stats_banner = format_compact_stats_banner(nhl_yesterday, nba_yesterday, nba_record, nhl_record)
    content += "<div id='yesterday-results'>\n"
    content += stats_banner
    content += "</div>\n\n"
    content += "<hr style='border: none; border-top: 2px solid #f0f0f0; margin: 40px 0;'>\n\n"

    # ── Sport sections ──
    for cfg in sports_config:
        sport = cfg["key"]
        name = cfg["name"]
        emoji = cfg["emoji"]

        content += f"<div id='{sport}-predictions' style='margin: 40px 0;'>\n"
        content += f"<h2 style='font-size: 2em; color: #333; border-left: 5px solid #667eea; padding-left: 15px; margin-bottom: 20px;'>{emoji} {name} Predictions</h2>\n\n"

        latest_file = sport_files.get(sport)
        if latest_file:
            raw = read_file(latest_file)
            content += build_sport_section(raw, sport, name, emoji, records[sport])
        else:
            content += f"> ℹ️ No {name} predictions available today.\n\n"

        content += "</div>\n\n"

        # Add divider between sports
        if sport != sports_config[-1]["key"]:
            content += "<hr style='border: none; border-top: 2px solid #f0f0f0; margin: 40px 0;'>\n\n"

    # ── Close content wrapper ──
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


    with open(output_md, "w") as f:
        f.write(content)
    print(f"✅ Updated {output_md}")


if __name__ == "__main__":
    update_latest_predictions()
