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
        "### ROLE\n"
        "You are an elite NBA Betting Analyst and Strategic Consultant. Your goal is to identify \"mispriced\" opportunities by blending cross-bookmaker odds analysis with advanced basketball situational theory.\n"
        "### ANALYSIS FRAMEWORK\n"
        "For each game in the provided data, execute the following three-step process:\n"
        "1. MARKET DISCREPANCY: Identify the \"best price\" available for a Side, Total, or Moneyline. Highlight where one bookmaker is a significant outlier compared to the consensus.\n"
        "2. SITUATIONAL EDGE: Evaluate the game based on:\n"
        "   - Schedule Fatigue: (e.g., Back-to-backs, 3-in-4 nights, or the \"post-road trip home opener\").\n"
        "   - Matchup Efficiency: How team Offensive/Defensive ratings and Pace interact (e.g., a fast-paced offense against a tired defense).\n"
        "   - Expected Value (EV): Only recommend plays where your qualitative analysis aligns with a quantitative price advantage.\n"
        "3. CONTRARIAN CHECK: Note if the value lies with the \"Sharp\" side (moving lines despite low public betting volume) or \"Public\" side.\n"
        "### CONSTRAINTS & OUTPUT\n"
        "- IGNORE: Games with spreads < 2 or \"coin-flip\" moneylines unless there is a massive Total (O/U) discrepancy.\n"
        "- RANKING: List plays from \"High Confidence\" to \"Leans.\"\n"
        "- FORMAT: Provide 2 sentences per play:\n"
        "    - Sentence 1: The numerical edge (Odds/Line variance).\n"
        "    - Sentence 2: Your strategic \"read\" on why the market is wrong (Fatigue, Matchup, or Sentiment).\n"
        "### DATA TO ANALYZE\n"
        f"{results_text}"
    )
    try:
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=types.Part.from_text(text=prompt),
        )
        return response.candidates[0].content.parts[0].text
    except genai.errors.ClientError as e:
        if "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e):
            return "AI analysis skipped: Gemini API quota exceeded."
        else:
            raise

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
        print(odds)

        if predictions_text:
            summary = analyze_results(odds)
            f.write("\nAI Analysis Summary:\n")
            f.write(summary + "\n")
            print("\nAI Analysis Summary:")
            print(summary)

print(f"Saved NBA daily predictions to {filename}")
