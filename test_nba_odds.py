import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from data.odds import get_nba_odds
from datetime import date

load_dotenv()

odds = get_nba_odds()
results_text = ""

if not odds:
    print("No NBA games today")
else:
    for game in odds:
        home_odds = None
        away_odds = None
        ou = None
        ou_over_odds = None
        ou_under_odds = None
        # spreads
        spread_home_points = None
        spread_home_price = None
        spread_away_points = None
        spread_away_price = None

        bookmakers = game.get('bookmakers', [])
        if bookmakers:
            markets = bookmakers[0].get('markets', [])
            for market in markets:
                key = market.get('key')
                outcomes = market.get('outcomes', []) or []
                if key == 'h2h':
                    for outcome in outcomes:
                        if outcome.get('name') == game.get('home_team'):
                            home_odds = outcome.get('price')
                        elif outcome.get('name') == game.get('away_team'):
                            away_odds = outcome.get('price')
                elif key == 'totals':
                    for outcome in outcomes:
                        if outcome.get('name') == 'Over':
                            ou = outcome.get('point')
                            ou_over_odds = outcome.get('price')
                        elif outcome.get('name') == 'Under':
                            ou_under_odds = outcome.get('price')
                elif key == 'spreads':
                    for outcome in outcomes:
                        name = outcome.get('name')
                        if name == game.get('home_team'):
                            spread_home_points = outcome.get('point')
                            spread_home_price = outcome.get('price')
                        elif name == game.get('away_team'):
                            spread_away_points = outcome.get('point')
                            spread_away_price = outcome.get('price')

        line = (
            f"{game.get('home_team')} vs {game.get('away_team')}\n"
            f"Home odds: {home_odds}, Away odds: {away_odds}, "
            f"O/U: {ou} (Over odds: {ou_over_odds}, Under odds: {ou_under_odds})\n"
            f"Spreads: Home {spread_home_points} ({spread_home_price}), Away {spread_away_points} ({spread_away_price})\n"
            "------\n"
        )
        results_text += line

    print("NBA Matchups and Odds:")
    print(results_text)
