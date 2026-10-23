import requests
from datetime import date, timedelta
import pytz

_TZ = pytz.timezone("America/New_York")

# ESPN abbreviation → full team name (matches NBA_TEAM_LOGOS keys)
_ESPN_ABBR_TO_NAME = {
    "ATL": "Atlanta Hawks",
    "BOS": "Boston Celtics",
    "BKN": "Brooklyn Nets",
    "CHA": "Charlotte Hornets",
    "CHI": "Chicago Bulls",
    "CLE": "Cleveland Cavaliers",
    "DAL": "Dallas Mavericks",
    "DEN": "Denver Nuggets",
    "DET": "Detroit Pistons",
    "GSW": "Golden State Warriors",
    "GS":  "Golden State Warriors",
    "HOU": "Houston Rockets",
    "IND": "Indiana Pacers",
    "LAC": "Los Angeles Clippers",
    "LAL": "Los Angeles Lakers",
    "MEM": "Memphis Grizzlies",
    "MIA": "Miami Heat",
    "MIL": "Milwaukee Bucks",
    "MIN": "Minnesota Timberwolves",
    "NOP": "New Orleans Pelicans",
    "NO":  "New Orleans Pelicans",
    "NY":  "New York Knicks",
    "NYK": "New York Knicks",
    "OKC": "Oklahoma City Thunder",
    "ORL": "Orlando Magic",
    "PHI": "Philadelphia 76ers",
    "PHX": "Phoenix Suns",
    "POR": "Portland Trail Blazers",
    "SAC": "Sacramento Kings",
    "SAS": "San Antonio Spurs",
    "SA":  "San Antonio Spurs",
    "TOR": "Toronto Raptors",
    "UTA": "Utah Jazz",
    "UTAH": "Utah Jazz",
    "WAS": "Washington Wizards",
}


def _fetch_espn_scoreboard(date_str):
    """Fetch games from the free ESPN scoreboard API for a given YYYYMMDD date string."""
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date_str}"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    data = response.json()

    games = []
    for event in data.get("events", []):
        competition = event.get("competitions", [{}])[0]
        competitors = competition.get("competitors", [])
        home = next((c for c in competitors if c.get("homeAway") == "home"), {})
        away = next((c for c in competitors if c.get("homeAway") == "away"), {})

        home_abbr = home.get("team", {}).get("abbreviation", "")
        away_abbr = away.get("team", {}).get("abbreviation", "")
        home_name = _ESPN_ABBR_TO_NAME.get(home_abbr, home.get("team", {}).get("displayName", home_abbr))
        away_name = _ESPN_ABBR_TO_NAME.get(away_abbr, away.get("team", {}).get("displayName", away_abbr))

        status = competition.get("status", {})
        completed = status.get("type", {}).get("completed", False)
        home_score = home.get("score")
        away_score = away.get("score")

        games.append({
            "game_id": event.get("id"),
            "home": home_name,
            "away": away_name,
            "commence_time": event.get("date"),
            "home_score": int(home_score) if home_score is not None else None,
            "away_score": int(away_score) if away_score is not None else None,
            "completed": completed,
            "status_text": status.get("type", {}).get("shortDetail", ""),
        })
    return games


def get_nba_games_today():
    today_str = date.today().strftime("%Y%m%d")
    return _fetch_espn_scoreboard(today_str)


def get_nba_games_yesterday():
    yesterday_str = (date.today() - timedelta(days=1)).strftime("%Y%m%d")
    return _fetch_espn_scoreboard(yesterday_str)


def get_nba_games_by_days_from(days_from):
    """Kept for backward compatibility — returns today + yesterday combined."""
    games = []
    for delta in range(days_from):
        d = (date.today() - timedelta(days=delta)).strftime("%Y%m%d")
        games.extend(_fetch_espn_scoreboard(d))
    return games
