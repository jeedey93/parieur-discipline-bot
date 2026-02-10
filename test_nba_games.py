from data.nba_games import get_nba_games_today

games = get_nba_games_today()

if not games:
    print("No NBA games today")
else:
    for g in games:
        print(f"{g['away']} @ {g['home']}")
