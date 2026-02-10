import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from data.odds import get_nba_odds
from datetime import date

load_dotenv()

def analyze_results(results_text):
    api_key = os.environ["GOOGLE_API_KEY"]
    client = genai.Client(api_key=api_key)
    prompt = (
        "You are a disciplined NBA betting analyst.\n"
        "Your job is to:\n"
        "- Ignore coin-flip games\n"
        "- Highlight only +EV spots\n"
        "- Rank plays by confidence\n"
        "- Explain in 1–2 sentences per play\n"
        f"\nAnalyze the following NBA betting results:\n{results_text}"
    )
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=types.Part.from_text(text=prompt),
    )
    return response.candidates[0].content.parts[0].text

today_str = date.today().isoformat()
predictions_folder = os.path.join("predictions", "nba")
os.makedirs(predictions_folder, exist_ok=True)
filename = os.path.join(predictions_folder, f"nba_daily_predictions_{today_str}.txt")

odds = get_nba_odds()
predictions_text = ""

with open(filename, "w") as f:
    f.write(f"Date: {today_str}\n\n")
    if not odds:
        f.write("No NBA games today\n")
        print("No NBA games today")
    else:
        for game in odds:
            home_odds = None
            away_odds = None
            ou = None
            ou_over_odds = None
            ou_under_odds = None
            for market in game['bookmakers'][0]['markets']:
                if market['key'] == 'h2h':
                    for outcome in market['outcomes']:
                        if outcome['name'] == game['home_team']:
                            home_odds = outcome['price']
                        elif outcome['name'] == game['away_team']:
                            away_odds = outcome['price']
                elif market['key'] == 'totals':
                    for outcome in market['outcomes']:
                        if outcome['name'] == 'Over':
                            ou = outcome['point']
                            ou_over_odds = outcome['price']
                        elif outcome['name'] == 'Under':
                            ou_under_odds = outcome['price']
            line = (
                f"{game['home_team']} vs {game['away_team']}\n"
                f"Home odds: {home_odds}, Away odds: {away_odds}, "
                f"O/U: {ou} (Over odds: {ou_over_odds}, Under odds: {ou_under_odds})\n"
                "------\n"
            )
            f.write(line)
            predictions_text += line

        print("NBA Matchups and Odds:")
        print(predictions_text)

        if predictions_text:
            summary = analyze_results(predictions_text)
            f.write("\nAI Analysis Summary:\n")
            f.write(summary + "\n")
            print("\nAI Analysis Summary:")
            print(summary)

print(f"Saved NBA daily predictions to {filename}")
