import os
import re
from google import genai
# Try to load environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # If dotenv is not installed, skip loading .env

# Path to the index.md file
INDEX_MD_PATH = "docs/index.md"
PREDICTIONS_DIR = "predictions"

def extract_bet_of_the_day(section_lines):
    """Extracts the Bet of the Day bet and justification from a section."""
    bet = None
    justification = None
    for i, line in enumerate(section_lines):
        if line.strip().startswith('🏆 BET OF THE DAY'):
            # The bet is the next non-empty line
            for j in range(i+1, len(section_lines)):
                if section_lines[j].strip():
                    bet = section_lines[j].strip()
                    # The justification is the next non-empty line after the bet
                    for k in range(j+1, len(section_lines)):
                        if section_lines[k].strip():
                            justification = section_lines[k].strip()
                            return bet, justification
    return bet, justification

def get_bets_from_index():
    with open(INDEX_MD_PATH, 'r') as f:
        lines = f.readlines()

    nhl_section = []
    nba_section = []
    in_nhl = False
    in_nba = False
    for line in lines:
        if line.strip().startswith('## NHL'):
            in_nhl = True
            in_nba = False
            continue
        if line.strip().startswith('## NBA'):
            in_nba = True
            in_nhl = False
            continue
        if in_nhl:
            nhl_section.append(line)
        if in_nba:
            nba_section.append(line)

    nhl_bet, nhl_just = extract_bet_of_the_day(nhl_section)
    nba_bet, nba_just = extract_bet_of_the_day(nba_section)
    return nhl_bet, nhl_just, nba_bet, nba_just

def build_gemini_prompt(nhl_bet, nhl_just, nba_bet, nba_just):
    prompt = f"""
🔥 DUAL BET OF THE DAY 🤖📊 Deux ligues. Même discipline. Même standard. On reste structurés.
⸻
🎯 PICK #1 – NHL 🏒 {nhl_bet}
{nhl_just}
⸻
🎯 PICK #2 – NBA 🏀 {nba_bet}
{nba_just}
⸻
Deux sports. Une seule approche.
On suit la value. On protège le bankroll. Discipline > émotion. 🎯
"""
    return prompt.strip()

def call_gemini_translate(client, text):
    """Call Gemini to translate the given text to French and return only the translation."""
    prompt_text = f"Traduis ce texte en français, sans rien ajouter d'autre :\n{text}"
    try:
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt_text,
        )
        return response.text.strip()
    except Exception as e:
        if "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e):
            return "AI analysis skipped: Gemini API quota exceeded."
        else:
            raise

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
    nhl_bet, nhl_just, nba_bet, nba_just = get_bets_from_index()
    if not (nhl_bet and nba_bet):
        print("Could not find both Bet of the Day entries.")
        return
    # Set up Gemini model
    api_key = os.environ["GOOGLE_API_KEY"]
    client = genai.Client(api_key=api_key)
    # Translate justifications to French using Gemini
    nhl_just_fr = call_gemini_translate(client, nhl_just) if nhl_just else None
    nba_just_fr = call_gemini_translate(client, nba_just) if nba_just else None
    prompt = build_gemini_prompt(nhl_bet, nhl_just_fr, nba_bet, nba_just_fr)

    # Print to console
    print(prompt)

    # Save to file
    save_to_file(prompt)

if __name__ == "__main__":
    main()
