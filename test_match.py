import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

from data.nhl_games import get_games_today
from data.odds import get_odds, match_odds_to_games

def analyze_results(results_text):
    api_key = os.environ["GOOGLE_API_KEY"]
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",  # Use the full model name
        contents=types.Part.from_text(
            text=f"Analyze the following NHL betting results and give a short summary:\n{results_text}"
        ),
    )
    return response.candidates[0].content.parts[0].text

# Pull your hardcoded date games
games = get_games_today()

if not games:
    print("No NHL Games today")
else:
    odds_data = get_odds()
    matched = match_odds_to_games(games, odds_data)

    results_text = ""
    for g in matched:
        line = (
            f"{g['away']} @ {g['home']}\n"
            f"Home odds: {g['home_odds']}, Away odds: {g['away_odds']}, O/U: {g['over_under']}\n"
            "------\n"
        )
        print(line, end="")
        results_text += line

    if results_text:
        summary = analyze_results(results_text)
        print("\nAI Analysis Summary:")
        print(summary)
