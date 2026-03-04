import os
# Try to load environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # If dotenv is not installed, skip loading .env

# Path to the index.md file
INDEX_MD_PATH = "docs/index.md"
PREDICTIONS_DIR = "predictions"

# New: Path to latest predictions markdown
LATEST_PREDICTIONS_MD = "docs/index.md"  # Adjust if needed

def extract_bet_of_the_day(section_lines):
    """Extracts the Bet of the Day bet and justification from a section.

    Handles format like:
        🏆 **BET OF THE DAY**
        **Washington Capitals ML vs Utah Mammoth @ 1.83**
        Confidence Level: Medium, Units: 1u, Win Probability: 60%
        The Capitals are well-rested and have shown strong form...
        *Changes: ...*
    """
    bet = None
    justification_lines = []
    for i, line in enumerate(section_lines):
        stripped = line.strip()
        # Find the BET OF THE DAY header
        if '🏆' in stripped and 'BET OF THE DAY' in stripped.upper():
            # Find the bet line (next non-empty line, usually bolded)
            for j in range(i+1, len(section_lines)):
                bet_line = section_lines[j].strip()
                if bet_line:
                    # Remove bold markdown if present
                    bet = bet_line.strip('*').strip()
                    # Collect justification: all meaningful lines after the bet
                    # until we hit "Other Recommended Plays", a section break (---),
                    # or another header
                    for k in range(j+1, len(section_lines)):
                        jline = section_lines[k].strip()
                        # Stop at section boundaries
                        if jline.startswith('**Other Recommended Plays') or \
                           jline == '---' or \
                           jline.startswith('## ') or \
                           jline.startswith('### ') or \
                           jline.startswith('🏆'):
                            break
                        if jline:
                            # Skip lines that start with *Change (change notes)
                            if jline.startswith('*Change') or jline.startswith('*Changes'):
                                continue
                            justification_lines.append(jline)
                    break
            break

    # Join all justification lines into one text
    justification = ' '.join(justification_lines).strip() if justification_lines else None
    return bet, justification

def get_sections_from_index():
    with open(INDEX_MD_PATH, 'r') as f:
        lines = f.readlines()

    nhl_section = []
    nba_section = []
    in_nhl = False
    in_nba = False
    for line in lines:
        stripped = line.strip()
        # Match headings like "## 🏒 NHL Predictions" or "## NHL"
        if stripped.startswith('## ') and 'NHL' in stripped:
            in_nhl = True
            in_nba = False
            continue
        if stripped.startswith('## ') and 'NBA' in stripped:
            in_nba = True
            in_nhl = False
            continue
        # Stop at other ## headers (e.g., "## 📈 Overall Performance")
        if stripped.startswith('## ') and 'NHL' not in stripped and 'NBA' not in stripped:
            if in_nhl:
                in_nhl = False
            if in_nba:
                in_nba = False
        if in_nhl:
            nhl_section.append(line)
        if in_nba:
            nba_section.append(line)
    return nhl_section, nba_section

def build_gemini_prompt(nhl_bet, nhl_just, nba_bet, nba_just):
    """Builds the dual bet of the day prompt from a template file."""
    prompt_path = os.path.join("prompts", "bet_of_the_day.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        template = f.read()
    return template.format(
        nhl_bet=nhl_bet,
        nhl_just=nhl_just,
        nba_bet=nba_bet,
        nba_just=nba_just
    ).strip()


def save_to_file(content):
    """Save the content to a txt file in the predictions folder."""
    if not os.path.exists(PREDICTIONS_DIR):
        os.makedirs(PREDICTIONS_DIR)

    filename = "dual_bet_of_the_day.txt"
    filepath = os.path.join(PREDICTIONS_DIR, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ Saved to: {filepath}")

def main():
    nhl_section, nba_section = get_sections_from_index()
    nhl_bet, nhl_just = extract_bet_of_the_day(nhl_section)
    nba_bet, nba_just = extract_bet_of_the_day(nba_section)
    if not (nhl_bet and nba_bet):
        print("Could not find both Bet of the Day entries.")
        return
    # Build output in the requested format (keep text as-is, no translation)
    output = build_gemini_prompt(nhl_bet, nhl_just, nba_bet, nba_just)
    print(output)
    save_to_file(output)

if __name__ == "__main__":
    main()
