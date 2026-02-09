from dotenv import load_dotenv
load_dotenv()

from data.nhl_games import get_games_today
from data.odds import get_odds, match_odds_to_games
from datetime import date
import os

# Pull your hardcoded date games
games = get_games_today()

# Fetch odds
odds_data = get_odds()

# Match them
matched = match_odds_to_games(games, odds_data)

# Save into results folder
today_str = date.today().isoformat()
results_folder = "results"
os.makedirs(results_folder, exist_ok=True)
filename = os.path.join(results_folder, f"daily_results_{today_str}.txt")

with open(filename, "w") as f:
    f.write(f"Date: {today_str}\n\n")

    if not matched:
        f.write("No NHL games today\n")
    else:
        for g in matched:
            f.write(f"{g['away']} @ {g['home']}\n")
            f.write(f"Home odds: {g['home_odds']}, Away odds: {g['away_odds']}, O/U: {g['over_under']}\n")
            f.write("------\n")

print(f"Saved daily results to {filename}")
