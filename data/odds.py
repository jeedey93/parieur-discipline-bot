import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz

# Load your .env file
load_dotenv()

API_KEY = os.getenv("ODDS_API_KEY")

def get_nhl_odds():
    """Fetch NHL odds using The Odds API."""
    url = "https://api.the-odds-api.com/v4/sports/icehockey_nhl/odds"

    eastern = pytz.timezone("America/Toronto")
    now = datetime.now(eastern)

    start_local = eastern.localize(datetime(now.year, now.month, now.day))
    end_local = start_local + timedelta(days=1)

    # Convert to UTC ISO strings with Z suffix
    start_utc = start_local.astimezone(pytz.utc).isoformat().replace("+00:00", "Z")
    end_utc = end_local.astimezone(pytz.utc).isoformat().replace("+00:00", "Z")

    params = {
        "apiKey": API_KEY,
        "regions": "us",
        "markets": "h2h,totals",
        "oddsFormat": "decimal",
        "dateFormat": "iso",
        "commenceTimeFrom": start_utc,
        "commenceTimeTo": end_utc,
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()

def get_nba_odds():
    """Fetch NBA odds using The Odds API."""
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"

    eastern = pytz.timezone("America/Toronto")
    now = datetime.now(eastern)

    start_local = eastern.localize(datetime(now.year, now.month, now.day))
    end_local = start_local + timedelta(days=1)

    # Convert to UTC ISO strings with Z suffix
    start_utc = start_local.astimezone(pytz.utc).isoformat().replace("+00:00", "Z")
    end_utc = end_local.astimezone(pytz.utc).isoformat().replace("+00:00", "Z")

    params = {
        "apiKey": API_KEY,
        "regions": "us",
        "markets": "h2h,spreads,totals",
        "oddsFormat": "decimal",
        "dateFormat": "iso",
        "commenceTimeFrom": start_utc,
        "commenceTimeTo": end_utc,
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()

NHL_TEAM_NAME_MAP = {
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

NBA_TEAM_NAME_MAP = {
    "atlanta": "Atlanta Hawks",
    "boston": "Boston Celtics",
    "brooklyn": "Brooklyn Nets",
    "charlotte": "Charlotte Hornets",
    "chicago": "Chicago Bulls",
    "cleveland": "Cleveland Cavaliers",
    "dallas": "Dallas Mavericks",
    "denver": "Denver Nuggets",
    "detroit": "Detroit Pistons",
    "goldenstate": "Golden State Warriors",
    "houston": "Houston Rockets",
    "indiana": "Indiana Pacers",
    "lac": "LA Clippers",
    "lal": "Los Angeles Lakers",
    "memphis": "Memphis Grizzlies",
    "miami": "Miami Heat",
    "milwaukee": "Milwaukee Bucks",
    "minnesota": "Minnesota Timberwolves",
    "neworleans": "New Orleans Pelicans",
    "newyork": "New York Knicks",
    "oklahomacity": "Oklahoma City Thunder",
    "orlando": "Orlando Magic",
    "philadelphia": "Philadelphia 76ers",
    "phoenix": "Phoenix Suns",
    "portland": "Portland Trail Blazers",
    "sacramento": "Sacramento Kings",
    "sanantonio": "San Antonio Spurs",
    "toronto": "Toronto Raptors",
    "utah": "Utah Jazz",
    "washington": "Washington Wizards"
}

def normalize(name):
    return name.lower().replace('.', '').replace(' ', '')

def match_odds_to_games(games, odds_data, team_name_map):
    matched_games = []
    for game in games:
        home_city = normalize(game["home"])
        away_city = normalize(game["away"])
        home = team_name_map.get(home_city, game["home"])
        away = team_name_map.get(away_city, game["away"])
        start_time = game["start_time"]
        home_odds = None
        away_odds = None
        over_under = None
        bookmakers_odds = []

        for odds_game in odds_data:
            if (normalize(odds_game["home_team"]) == normalize(home) and
                    normalize(odds_game["away_team"]) == normalize(away)):
                for bookmaker in odds_game["bookmakers"]:
                    bookmaker_entry = {
                        "title": bookmaker["title"],
                        "markets": []
                    }
                    for market in bookmaker["markets"]:
                        market_entry = {
                            "key": market["key"],
                            "outcomes": market["outcomes"]
                        }
                        bookmaker_entry["markets"].append(market_entry)
                        # For summary odds (first bookmaker only, for backward compatibility)
                        if home_odds is None and market["key"] == "h2h":
                            for outcome in market["outcomes"]:
                                if normalize(outcome["name"]) == normalize(home):
                                    home_odds = outcome["price"]
                                elif normalize(outcome["name"]) == normalize(away):
                                    away_odds = outcome["price"]
                        if over_under is None and market["key"] == "totals":
                            over_under = market["outcomes"][0].get("point")
                    bookmakers_odds.append(bookmaker_entry)
                break

        if home_odds is not None and away_odds is not None:
            matched_games.append({
                "game_id": game["game_id"],
                "home": home,
                "away": away,
                "start_time": start_time,
                "home_odds": home_odds,
                "away_odds": away_odds,
                "over_under": over_under,
                "bookmakers_odds": bookmakers_odds
            })

    return matched_games

def match_nba_odds_to_games(games, odds_data, team_name_map=NBA_TEAM_NAME_MAP):
    """
    Match The Odds API NBA odds to your games list and summarize moneyline, totals, and spreads.
    - Scans all bookmakers to find moneyline (h2h), totals (point), and spreads (home/away points & prices).
    - For spreads, chooses the most common point per side; if tie or unavailable, picks the first seen.
    - Also returns a per-bookmaker snapshot in `bookmakers_odds` for downstream analysis.
    """
    def _tally_spread(spread_records):
        # spread_records: list of dicts {point, price}
        if not spread_records:
            return None, None
        # Count points frequency
        from collections import Counter
        points = [r["point"] for r in spread_records if r.get("point") is not None]
        if not points:
            # fallback first
            first = spread_records[0]
            return first.get("point"), first.get("price")
        most_common_point, _ = Counter(points).most_common(1)[0]
        # pick best price among records with that point (highest decimal price)
        candidates = [r for r in spread_records if r.get("point") == most_common_point and r.get("price") is not None]
        if not candidates:
            return most_common_point, None
        best = max(candidates, key=lambda r: r.get("price", 0))
        return most_common_point, best.get("price")

    matched_games = []

    for game in games:
        home_city = normalize(game["home"]) if isinstance(game.get("home"), str) else game.get("home")
        away_city = normalize(game["away"]) if isinstance(game.get("away"), str) else game.get("away")
        home = team_name_map.get(home_city, game.get("home"))
        away = team_name_map.get(away_city, game.get("away"))
        start_time = game.get("commence_time") or game.get("start_time")

        home_odds = None
        away_odds = None
        over_under = None

        # collect spreads across all bookmakers
        spread_home_records = []  # list of {point, price}
        spread_away_records = []

        bookmakers_odds = []

        for odds_game in odds_data:
            if (normalize(odds_game.get("home_team", "")) == normalize(home) and
                normalize(odds_game.get("away_team", "")) == normalize(away)):

                for bookmaker in odds_game.get("bookmakers", []):
                    bm_snapshot = {"title": bookmaker.get("title"), "markets": []}

                    for market in bookmaker.get("markets", []):
                        mkey = market.get("key")
                        outcomes = market.get("outcomes", []) or []
                        bm_snapshot["markets"].append({"key": mkey, "outcomes": outcomes})

                        if mkey == "h2h":
                            # moneyline summary (first seen)
                            if home_odds is None or away_odds is None:
                                for o in outcomes:
                                    name = o.get("name", "")
                                    price = o.get("price")
                                    if price is None:
                                        continue
                                    if normalize(name) == normalize(home):
                                        home_odds = price
                                    elif normalize(name) == normalize(away):
                                        away_odds = price

                        elif mkey == "totals":
                            if over_under is None and outcomes:
                                over_under = outcomes[0].get("point")

                        elif mkey == "spreads":
                            for o in outcomes:
                                name = o.get("name", "")
                                price = o.get("price")
                                point = o.get("point")
                                if normalize(name) == normalize(home):
                                    spread_home_records.append({"point": point, "price": price})
                                elif normalize(name) == normalize(away):
                                    spread_away_records.append({"point": point, "price": price})

                    bookmakers_odds.append(bm_snapshot)
                break

        spread_home_points, spread_home_price = _tally_spread(spread_home_records)
        spread_away_points, spread_away_price = _tally_spread(spread_away_records)

        if home_odds is not None and away_odds is not None:
            matched_games.append({
                "game_id": game.get("game_id") or odds_game.get("id"),
                "home": home,
                "away": away,
                "start_time": start_time,
                "home_odds": home_odds,
                "away_odds": away_odds,
                "over_under": over_under,
                "spread_home_points": spread_home_points,
                "spread_home_price": spread_home_price,
                "spread_away_points": spread_away_points,
                "spread_away_price": spread_away_price,
                "bookmakers_odds": bookmakers_odds,
            })

    return matched_games
