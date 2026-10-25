"""
Compare morning (7am) and afternoon (3pm) predictions for a given sport.
Usage: python scripts/compare_predictions.py --sport nhl|nba
"""
import argparse
import os
import sys
import time
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from google import genai
import re

load_dotenv()


def ensure_confidence_line(text):
    play_header_pattern = re.compile(r"^(\*\*.+?(vs|ML|over|under|\+|-).+?\*\*)$", re.MULTILINE)
    confidence_pattern = re.compile(r"Confidence Level: .+?Units: .+?Win Probability: .+?%", re.IGNORECASE)
    lines = text.split('\n')
    output_lines = []
    i = 0
    while i < len(lines):
        output_lines.append(lines[i])
        if play_header_pattern.match(lines[i]):
            found_conf = any(
                confidence_pattern.search(lines[i + j])
                for j in range(1, 6) if i + j < len(lines)
            )
            if not found_conf:
                output_lines.append("Confidence Level: [Unknown] Units: [Unknown] | Win Probability: [Unknown]%")
        i += 1
    return '\n'.join(output_lines)


def compare_predictions(morning_file, noon_file, output_file, prompt_path, injuries_text=None):
    api_key = os.environ["GOOGLE_API_KEY"]
    client = genai.Client(api_key=api_key)

    try:
        with open(morning_file, "r", encoding="utf-8") as f:
            morning_predictions = f.read()
    except FileNotFoundError:
        print(f"Morning predictions file not found: {morning_file}")
        return

    try:
        with open(noon_file, "r", encoding="utf-8") as f:
            noon_predictions = f.read()
    except FileNotFoundError:
        print(f"Noon predictions file not found: {noon_file}")
        return

    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    prompt = prompt_template.format(
        morning_predictions=morning_predictions,
        noon_predictions=noon_predictions,
    )

    if injuries_text:
        prompt += f"\n\n---\nINJURY / ABSENCE CONTEXT (fetched at 3pm):\n{injuries_text}\nUse this to adjust confidence and reasoning for any plays from the morning report."

    models_to_try = [
        "models/gemini-2.5-flash",
        "models/gemini-3.8-flash",
        "models/gemini-2.5-flash-lite",
        "models/gemini-2.5-pro",
    ]
    retry_waits = [30, 60]

    for model in models_to_try:
        max_retries = len(retry_waits) + 1
        for attempt in range(max_retries):
            try:
                print(f"🤖 Trying {model}...")
                chat = client.chats.create(model=model)
                response = chat.send_message(prompt)
                result = response.candidates[0].content.parts[0].text.strip()
                result = ensure_confidence_line(result)

                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(result)

                print(f"✅ Combined analysis saved to: {output_file}")
                print("\n" + result)
                return result

            except genai.errors.ServerError as e:
                if "503" in str(e) or "UNAVAILABLE" in str(e):
                    if attempt < max_retries - 1:
                        wait_time = retry_waits[attempt]
                        print(f"⚠️ {model} 503 error. Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                    else:
                        print(f"⚠️ {model} still unavailable, trying next model...")
                        break
                else:
                    raise
            except genai.errors.ClientError as e:
                if "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e):
                    print(f"⚠️ {model} quota exceeded, trying next model...")
                    break
                else:
                    raise

    print("❌ All Gemini models unavailable. Cancelling workflow.")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sport", required=True, choices=["nhl", "nba"], help="Sport to compare")
    args = parser.parse_args()
    sport = args.sport

    today_str = date.today().isoformat()
    predictions_folder = os.path.join("data", "predictions", sport)
    daily_runs_folder = os.path.join(predictions_folder, "daily_runs")
    prompt_path = os.path.join("prompts", "compare_prompt.txt")

    morning_file = os.path.join(daily_runs_folder, f"{sport}_daily_predictions_{today_str}_7am.txt")
    noon_file = os.path.join(daily_runs_folder, f"{sport}_daily_predictions_{today_str}_3pm.txt")
    output_file = os.path.join(predictions_folder, f"{sport}_daily_predictions_{today_str}.txt")

    if not os.path.exists(morning_file):
        print(f"⚠️  Morning predictions file not found: {morning_file}")
        return

    if not os.path.exists(noon_file):
        print(f"⚠️  Noon predictions file not found: {noon_file}")
        return

    if os.path.exists(output_file):
        print(f"⚠️  Combined predictions file already exists: {output_file}")
        print("Skipping comparison to avoid overwriting existing file.")
        return

    print(f"Comparing {sport.upper()} predictions from {today_str}...")
    print(f"Morning file: {morning_file}")
    print(f"Noon file: {noon_file}")

    # NHL-only: if noon has no qualified plays, enrich with live injuries
    injuries_text = None
    if sport == "nhl":
        with open(noon_file, "r", encoding="utf-8") as f:
            noon_content = f.read()
        if "no qualified plays" in noon_content.lower():
            print("ℹ️  Noon has no qualified plays — fetching injuries to enrich 7am picks...")
            try:
                from scripts.scrape_nhl_absences import scrape_nhl_absences_by_team
                absences = scrape_nhl_absences_by_team()
                if absences:
                    injuries_text = "NHL Player Absences by Team:\n"
                    for team, players in absences.items():
                        injuries_text += f"{team}:\n"
                        for player in players:
                            injuries_text += f"  - {player}\n"
                    print(f"✅ Fetched injuries for {len(absences)} teams")
                else:
                    print("⚠️  No injury data available")
            except Exception as e:
                print(f"⚠️  Could not fetch injuries: {e}")

    compare_predictions(morning_file, noon_file, output_file, prompt_path, injuries_text=injuries_text)


if __name__ == "__main__":
    main()
