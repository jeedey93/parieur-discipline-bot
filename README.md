<p align="center">
  <img src="images/parieur_discipline.png" alt="Project Logo" width="250"/>
</p>

<p align="center">
  <b>Meet le Parieur Discipliné:</b>  
  <i>Le Parieur Discipliné is the disciplined bettor—focused on smart, consistent, and value-driven bets. This project is inspired by Parieur Discipliné’s approach: using data, AI, and strict criteria to identify the best opportunities each day.</i>
</p>


# NHL & NBA Best Bet Bot

A Python tool for analyzing NHL and NBA games, matching odds, and generating disciplined betting analysis using Google Gemini AI. The bot highlights +EV spots, ranks plays by confidence, and explains each pick.

## Features

- Fetches daily NHL and NBA games and odds (The Odds API)
- Supports multi-bookmaker markets: moneyline (h2h), totals (O/U), and spreads
- Analyzes results using Google Gemini
- "Bet of the Day" extraction and optional image generation
- Writes daily predictions and results

## Requirements

- macOS or Linux (Windows works too)
- Python 3.10+ (3.13 supported)
- The Odds API key
- Google Gemini API key

## Recommended Setup (venv)

Use a project-local virtual environment so installs don’t collide with your system Python.

```bash
# from project root
python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` in the repo root:

```bash
GOOGLE_API_KEY=your_google_api_key
ODDS_API_KEY=your_the_odds_api_key
```

These are read by scripts via `python-dotenv`.

## Usage

Run daily predictions (inside venv):

```bash
python nhl_predictions_daily_run.py
python nba_predictions_daily_run.py
```

Run daily results (scores) summary:

```bash
python nhl_results_daily_run.py
python nba_results_daily_run.py
```

## Daily Automation (GitHub Actions)

- The workflow checks out the repo, sets up Python, installs dependencies from `requirements.txt`, writes `.env` from repo secrets, runs daily scripts, and commits changes (predictions/results/images/LATEST_PREDICTIONS.md).

## Example Output

```
NBA Matchups and Odds:
New York Knicks vs Indiana Pacers
Home odds: 1.83, Away odds: 2.02, O/U: 223.5
Spreads: Home -2.5 (1.91), Away +2.5 (1.91)
------
...

AI Analysis Summary:
- Plays listed from High Confidence to Leans, with fan-friendly reasoning.
- Bet of the Day: <TEAM or MARKET> vs <OPPONENT> @ <ODDS>
```

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License

MIT License
