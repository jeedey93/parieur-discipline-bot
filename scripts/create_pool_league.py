#!/usr/bin/env python3
"""Create the 2026-27 pool league with all 8 teams from the draft spreadsheet."""

import os, re, unicodedata, json, secrets
from dotenv import load_dotenv
load_dotenv()
from supabase import create_client

sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

# ── Teams from draft spreadsheet ──────────────────────────────────────────────
# Format: (team_name, owner, [forwards...], [defence...], [goalies...])
# Players identified from screenshot (skaters only visible — goalies at bottom)

TEAMS_RAW = {
    "Ledoux-1": [
        # Forwards
        "Nikita Kucherov", "Will Smith", "Brandon Hagel", "Michael Misa",
        "Ivar Stenberg", "Chris Kreider", "Tommy Novak", "Jesper Bratt",
        "JJ Peterka", "Taylor Hall", "Brayden Point", "Filip Forsberg",
        # Defence
        "Adam Fox", "Jackson LaCombe", "Sam Rinzel", "Axel Sandin-Pellika",
        "John Marino", "Sam Malinski", "Mackenzie Blackwood",
        # Goalies
        "Jet Greaves", "Logan Cooley", "Justin Hryckowian", "Oliver Kapanen",
        "Oliver Ekman-Larsson", "Victor Hedman", "Dan Vladar",
    ],
    "Lahaie-2": [
        "Beckett Sennecke", "Anton Frondell", "Matvei Michkov", "Gavin McKenna",
        "Mark Scheifele", "Ryan O'reilly", "David Pastrnak", "Morgan Geekie",
        "Kyle Connor", "Arturri Lehkonen", "Sebastian Aho", "Alex Ovechkin",
        "Matthew Schaefer", "Josh Morrissey", "Cole Hutson", "Rasmus Dahlin",
        "Bowen Byram", "Travis Sanheim", "Ukko-Pekka Luukkonen",
        "Jesper Wallstedt", "Viggo Bjorck", "Joel Eriksson Ek", "Lucas Raymond",
        "Alberts Smits", "Logan Mailloux", "Sebastian Cossa",
    ],
    "Myke-3": [
        "Nathan MacKinnon", "Cole Caufield", "Ivan Demidov", "Juraj Slafkovsky",
        "Igor Chernyshov", "James Hagens", "Pavel Zacha", "Evgeni Malkin",
        "Emmitt Finnie", "Alex DeBrincat", "Anthony Mantha", "Nico Hischier",
        "Miro Heiskanen", "Mattias Samuelsson", "Shea Theodore", "Artyom Levshunov",
        "Vince Dunn", "Charle-Edouard D'Astous", "Logan Thompson",
        "Jacob Markstrom", "Mitch Marner", "Jamie Benn", "Morgan Frost",
        "Jamie Drysdale", "Parker Wotherspoon", "Jake Allen",
    ],
    "Roy-4": [
        "Wyatt Johnston", "Tim Stutzle", "Nick Schmaltz", "Clayton Keller",
        "Dylan Guenther", "Matt Boldy", "Quinton Byfield", "Marco Rossi",
        "Maksim Shabanov", "Roman Kantserov", "Dalibor Dvorsky", "Easton Cowan",
        "Zach Werenski", "Cale Makar", "Quinn Hughes", "Brandt Clarke",
        "Mattias Ekholm", "Luca Cagnoni", "Jakub Dobes",
        "Devon Levi", "Bryan Rust", "Anton Lundell", "Aliaksei Protas",
        "John Carlson", "Olen Zellweger", "Akira Schmid",
    ],
    "Oli-5": [
        "Leon Draisaitl", "Jack Eichel", "Artemi Panarin", "Matthew Tkachuk",
        "Jack Hughes", "Rickard Rakell", "Luke Evangelista", "Claude Giroux",
        "Mats Zuccarello", "Jimmy Snuggerud", "Porter Martone", "Ben Kindel",
        "Zeev Buium", "Roman Josi", "Tony Deangelo", "Jakob Chychrun",
        "Brent Burns", "Mason Lohrei", "Scott Wedgewood",
        "Yaroslav Askarov", "Liam Ohgren", "Ryan Nugent-Hopkins", "Mark Stone",
        "Sam Dickinson", "K'Andre Miller", "Pyotr Kochetkov",
    ],
    "Bars-6": [
        "Drake Batherson", "Kirill Marchenko", "Macklin Celebrini", "Ryan Leonard",
        "Martin Necas", "Konsta Helenius", "Victor Eklund", "Jake Guentzel",
        "Matthew Knies", "Matthew Wood", "Ilya Protas", "Jason Robertson",
        "Mikhail Sergachev", "Jake Sanderson", "Zayne Parekh", "Carter Yakemchuk",
        "Charlie McAvoy", "Brandon Montour", "Andrei Vasilevsky",
        "Joel Hofer", "Alex Turcotte", "Adrian Kempe", "Emil Heineman",
        "Thomas Chabot", "David Reinbacher", "Jake Oettinger",
    ],
    "Oil In-7": [
        "Connor Mcdavid", "Calum Ritchie", "Jack Quinn", "Mika Zibanejad",
        "Gabe Perreault", "Vasily Podkolzin", "Sidney Crosby", "Ivan Barbashev",
        "William Nylander", "Danila Yurov", "Noah Ostlund", "Hendrix Lapierre",
        "Evan Bouchard", "Jake Sanderson", "Moritz Seider", "Denton Mateychuk",
        "Filip Hronek", "Tom Willander", "Brandon Bussi",
        "Arturs Silovs", "Sam Reinhart", "Zach Hyman", "Nicholas Robertson",
        "Mike Matheson", "Adam Jiricek", "Stuart Skinner",
    ],
    "JD-8": [
        "Mikko Rantanen", "Robert Thomas", "Nick Suzuki", "Tage Thompson",
        "Vincent Trocheck", "William Eklund", "Dylan Strome", "Jared McCann",
        "John Tavares", "Kent Johnson", "Matvei Gridin", "Fraser Minten",
        "Lane Hutson", "Darren Raddysh", "Philip Broberg", "Shayne Gostisbehere",
        "Ryker Evans", "Tristan Luneau", "Karel Vejmelka",
        "Carter Hart", "Matt Duchene", "Nick Lardis", "Jackson Blake",
        "Ryan Shea", "Morgan Rielly", "Sergei Murashov",
    ],
}

# ── Build name → slug lookup ──────────────────────────────────────────────────
def normalize(name):
    nfkd = unicodedata.normalize('NFKD', name)
    ascii_str = ''.join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r'\s+', ' ', ascii_str).strip().lower()

players = sb.table('nhl_players').select('puckpedia_slug,player_name,position').limit(2000).execute().data
name_map = {}
for p in players:
    raw = p['player_name'] or ''
    if ',' in raw:
        last, first = raw.split(',', 1)
        full = f'{first.strip()} {last.strip()}'
    else:
        full = raw
    name_map[normalize(full)] = p['puckpedia_slug']

# ── Resolve player names to slugs ─────────────────────────────────────────────
def resolve(name):
    slug = name_map.get(normalize(name))
    if not slug:
        # Try last-name match as fallback
        last = normalize(name).split()[-1]
        slug = next((v for k, v in name_map.items() if k.split()[-1] == last), None)
    return slug

# ── Create league ─────────────────────────────────────────────────────────────
LEAGUE_CODE = "P27A"
LEAGUE_NAME = "Pool 2026-27"
ACCESS_TOKEN = secrets.token_urlsafe(18)

# Check if already exists
existing = sb.table('pool_leagues').select('code').eq('code', LEAGUE_CODE).execute().data
if existing:
    print(f"League {LEAGUE_CODE} already exists — deleting and recreating")
    sb.table('pool_rosters').delete().eq('league_code', LEAGUE_CODE).execute()
    sb.table('pool_settings').delete().eq('league_code', LEAGUE_CODE).execute()
    sb.table('pool_leagues').delete().eq('code', LEAGUE_CODE).execute()

sb.table('pool_leagues').insert({
    'code': LEAGUE_CODE,
    'name': LEAGUE_NAME,
    'access_token': ACCESS_TOKEN,
}).execute()
print(f"✅ Created league: {LEAGUE_NAME} ({LEAGUE_CODE})")
print(f"   Access token: {ACCESS_TOKEN}")

# ── Default scoring settings ──────────────────────────────────────────────────
sb.table('pool_settings').upsert({
    'league_code': LEAGUE_CODE,
    'f_points': 1,
    'd_goals': 2,
    'd_assists': 1,
    'g_wins': 2,
    'g_shutouts': 3,
    'max_trades_per_team': 3,
}, on_conflict='league_code').execute()
print("✅ Scoring settings saved")

# ── Build roster data ─────────────────────────────────────────────────────────
# From the spreadsheet: last 7 rows per team appear to be goalies/bench
# First 19 rows are skaters (12F + 7D roughly), last 7 are goalies
# Looking at the image more carefully:
# Each team has ~26 players total, last ~7 rows appear lighter (bench/goalies)
# We'll put the last 2 as goalies, next 7 as defence, rest as forwards
# based on known positions in the DB

# Active roster limits: 12F, 6D, 2G — overflow goes to bench
F_LIMIT, D_LIMIT, G_LIMIT = 12, 6, 2

teams = []
unresolved = []

for team_name, player_names in TEAMS_RAW.items():
    forwards, defence, goalies, bench = [], [], [], []
    for name in player_names:
        slug = resolve(name)
        if not slug:
            unresolved.append((team_name, name))
            continue
        # Look up position
        p = next((x for x in players if x['puckpedia_slug'] == slug), None)
        pos = (p.get('position') or '').upper() if p else ''
        if 'G' in pos:
            if len(goalies) < G_LIMIT:
                goalies.append(slug)
            else:
                bench.append(slug)
        elif pos == 'D' or 'D' in pos:
            if len(defence) < D_LIMIT:
                defence.append(slug)
            else:
                bench.append(slug)
        else:
            if len(forwards) < F_LIMIT:
                forwards.append(slug)
            else:
                bench.append(slug)

    teams.append({
        'id': team_name,
        'name': team_name,
        'roster': {'F': forwards, 'D': defence, 'G': goalies, 'B': bench},
        'acquisitions': {},
    })
    print(f"  {team_name}: {len(forwards)}F {len(defence)}D {len(goalies)}G {len(bench)}B")

if unresolved:
    print(f"\n⚠️  Unresolved ({len(unresolved)}):")
    for team, name in unresolved:
        print(f"  {team}: {name}")

roster_data = {'teams': teams, 'activeTeamId': teams[0]['id']}
sb.table('pool_rosters').upsert({
    'league_code': LEAGUE_CODE,
    'data': roster_data,
}, on_conflict='league_code').execute()
print(f"\n✅ Roster saved — {len(teams)} teams")
print(f"\n🔗 League URL: /pool/settings.html?league={LEAGUE_CODE}")
