import requests
from datetime import date

def get_nba_games_today():
    today = date.today().isoformat()
    url = f"https://www.balldontlie.io/api/v1/games?dates[]={today}"
    print("Fetching:", url)  # Debug: see the URL

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 404:
            return []
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return []

    games = []
    for game in data.get("data", []):
        games.append({
            "game_id": game["id"],
            "away": game["visitor_team"]["full_name"],
            "home": game["home_team"]["full_name"],
            "start_time": game["date"]
        })

    return games
