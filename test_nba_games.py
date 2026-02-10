from data.nba_games import get_nba_games_today, get_nba_games_yesterday

games = get_nba_games_today()
games_yesterday = get_nba_games_yesterday()

if not games_yesterday:
    print("No NBA games yesterday")
else:
    print("Yesterday's NBA games:")
    for g in games_yesterday:
        print(f"{g['away']} {g['away_score']} @ {g['home']} {g['home_score']}")

print()

if not games:
    print("No NBA games today")
else:
    print("Todays's NBA games:")
    for g in games:
        print(f"{g['away']} @ {g['home']}")
