import requests
from datetime import datetime, timezone, date

def is_valid_nba_slug(slug):
    parts = slug.split("-")
    return len(parts) == 6 and parts[0] == "nba"

def fetch_todays_nba_polymarket_odds(target_date=date(2026, 2, 10)):
    url = "https://gamma-api.polymarket.com/events"
    params = {"tag_id": "745", "limit": 100, "closed": "false"}
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    events = response.json()
    nba_events = []
    for e in events:
        if is_valid_nba_slug(e.get("slug", "")) and "start_time" in e:
            try:
                event_date = datetime.fromisoformat(e["start_time"].replace("Z", "+00:00")).date()
                if event_date == target_date:
                    nba_events.append(e)
            except Exception as ex:
                print(f"Error parsing date for event: {e.get('slug', '')}, error: {ex}")
    print(f"NBA events on {target_date}: {len(nba_events)}")
    for event in nba_events:
        question = event.get("question", "N/A")
        start_time = event.get("start_time", "N/A")
        print(f"Market: {question}")
