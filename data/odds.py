import requests
import os
import requests
import os
from dotenv import load_dotenv

# Load your .env file
load_dotenv()

API_KEY = os.getenv("ODDS_API_KEY")

def get_odds():
    """
    Fetch NHL odds using The Odds API.
    Returns a list of games with bookmakers and markets.
    """
    url = "https://api.the-odds-api.com/v4/sports/icehockey_nhl/odds"

    params = {
        "apiKey": API_KEY,
        "regions": "us",          # which sportsbook regions to pull
        "markets": "h2h,totals",  # moneyline & totals
        "oddsFormat": "decimal"
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()  # raise error if API fails
    data = response.json()

    return data

# Example mapping (add all teams as needed)
TEAM_NAME_MAP = {
    "anaheim": "Anaheim Ducks",
    "arizona": "Arizona Coyotes",
    "boston": "Boston Bruins",
    "buffalo": "Buffalo Sabres",
    "calgary": "Calgary Flames",
    "carolina": "Carolina Hurricanes",
    "chicago": "Chicago Blackhawks",
    "colorado": "Colorado Avalanche",
    "columbus": "Columbus Blue Jackets",
    "dallas": "Dallas Stars",
    "detroit": "Detroit Red Wings",
    "edmonton": "Edmonton Oilers",
    "florida": "Florida Panthers",
    "losangeles": "Los Angeles Kings",
    "minnesota": "Minnesota Wild",
    "montreal": "Montreal Canadiens",
    "nashville": "Nashville Predators",
    "newjersey": "New Jersey Devils",
    "nyislanders": "New York Islanders",
    "nyrangers": "New York Rangers",
    "ottawa": "Ottawa Senators",
    "philadelphia": "Philadelphia Flyers",
    "pittsburgh": "Pittsburgh Penguins",
    "sanJose": "San Jose Sharks",
    "seattle": "Seattle Kraken",
    "stlouis": "St. Louis Blues",
    "tampabay": "Tampa Bay Lightning",
    "toronto": "Toronto Maple Leafs",
    "utah": "Utah Hockey Club",
    "vancouver": "Vancouver Canucks",
    "vegas": "Vegas Golden Knights",
    "washington": "Washington Capitals",
    "winnipeg": "Winnipeg Jets"
}

def normalize(name):
    return name.lower().replace('.', '').replace(' ', '')

def match_odds_to_games(games, odds_data):
    matched_games = []

    for game in games:
        home_city = normalize(game["home"])
        away_city = normalize(game["away"])
        home = TEAM_NAME_MAP.get(home_city, game["home"])
        away = TEAM_NAME_MAP.get(away_city, game["away"])
        start_time = game["start_time"]
        home_odds = None
        away_odds = None
        over_under = None

        for odds_game in odds_data:
            if (normalize(odds_game["home_team"]) == normalize(home) and
                normalize(odds_game["away_team"]) == normalize(away)):
                bookmaker = odds_game["bookmakers"][0]
                for market in bookmaker["markets"]:
                    if market["key"] == "h2h":
                        for outcome in market["outcomes"]:
                            if normalize(outcome["name"]) == normalize(home):
                                home_odds = outcome["price"]
                            elif normalize(outcome["name"]) == normalize(away):
                                away_odds = outcome["price"]
                    elif market["key"] == "totals":
                        over_under = market["outcomes"][0].get("point")
                break

        if home_odds is not None and away_odds is not None:
            matched_games.append({
                "game_id": game["game_id"],
                "home": home,
                "away": away,
                "start_time": start_time,
                "home_odds": home_odds,
                "away_odds": away_odds,
                "over_under": over_under
            })

    return matched_games
