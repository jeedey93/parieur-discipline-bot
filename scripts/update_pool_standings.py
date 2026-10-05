#!/usr/bin/env python3
"""
Update pool standings metadata daily:
  - rank_previous: rank from yesterday's snapshot
  - weekly_pts: points earned since last Monday
  - scouting_report: Gemini-generated one-liner per team

Run after scrape_nhl_stats.py so player stats are fresh.
"""

import os
import sys
import time
import json
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

import google.genai as genai
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
    sys.exit(1)
if not GOOGLE_API_KEY:
    print("⚠️  Missing GOOGLE_API_KEY — scouting reports will be skipped, history snapshot will still run")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
tz = ZoneInfo("America/Toronto")

WEEKLY_SNAPSHOT_FILE = "data/pool_weekly_snapshot.json"
HISTORY_FILE = "docs/data/pool_history.json"
POOL_SUMMARY_FILE = "docs/data/pool_weekly_summary.json"


# ── Scoring ────────────────────────────────────────────────────────────────────

def score_team(roster, player_map):
    f_pts = sum((player_map[s].get("points", 0) or 0)
                for s in roster.get("F", []) if s in player_map)
    d_pts = sum((player_map[s].get("goals", 0) or 0) * 2 +
                (player_map[s].get("assists", 0) or 0)
                for s in roster.get("D", []) if s in player_map)
    g_pts = sum((player_map[s].get("wins", 0) or 0) * 2 +
                (player_map[s].get("ot_losses", 0) or 0) +
                (player_map[s].get("shutouts", 0) or 0) * 3
                for s in roster.get("G", []) if s in player_map)
    return f_pts + d_pts + g_pts


# ── Weekly snapshot ────────────────────────────────────────────────────────────

def last_monday():
    today = date.today()
    return today - timedelta(days=today.weekday())  # Monday = 0


def load_weekly_snapshot():
    if os.path.exists(WEEKLY_SNAPSHOT_FILE):
        with open(WEEKLY_SNAPSHOT_FILE) as f:
            return json.load(f)
    return {}


def save_weekly_snapshot(snapshot: dict):
    os.makedirs(os.path.dirname(WEEKLY_SNAPSHOT_FILE), exist_ok=True)
    with open(WEEKLY_SNAPSHOT_FILE, "w") as f:
        json.dump(snapshot, f, indent=2)


# ── Gemini scouting report ─────────────────────────────────────────────────────

def gemini_scouting_report(team_name: str, owner: str, roster_summary: str,
                           total_pts: int, rank: int, prev_rank: int | None,
                           best_player: str, weak_pos: str) -> str:
    client = genai.Client(api_key=GOOGLE_API_KEY)

    rank_note = ""
    if prev_rank and prev_rank != rank:
        diff = prev_rank - rank
        rank_note = f"(moved up {diff} spot{'s' if diff != 1 else ''} from #{prev_rank})" if diff > 0 \
                    else f"(slipped {abs(diff)} spot{'s' if abs(diff) != 1 else ''} from #{prev_rank})"

    prompt = f"""You are a sharp, witty hockey pool analyst — TSN panel energy meets locker-room trash talk.

Write a scouting report of exactly 2-3 sentences for this fantasy pool team.
Structure:
  1. Open with a riff on the team name "{team_name}" or a jab at the manager {owner} — make it personal and fun.
  2. Break down their roster reality using ONLY the actual stats provided — name their best player and call out what position group is dragging them. If stats are low because the season just started, say so and speculate on potential instead of fabricating.
  3. Close with a sharp prediction or a dig about where they're headed.

Rules:
- Friendly banter only, no mean-spirited attacks.
- Only reference stats that are actually in the data — never invent numbers or claim a player is struggling/excelling without evidence in the stats.
- No emojis. No hashtags. No bullet points. Plain prose only.
- Do not add quotes around your response.

Team: {team_name} (managed by {owner})
Current rank: #{rank} {rank_note}
Total pool points: {total_pts}
Best player so far: {best_player}
Weakest position group: {weak_pos}
Roster breakdown:
{roster_summary}

Scouting report:"""

    models = [
        "models/gemini-2.5-flash",
        "models/gemini-2.5-flash-lite",
        "models/gemini-3.8-flash",
        "models/gemini-3.1-flash-lite",
    ]
    for model in models:
        for attempt in range(3):
            try:
                chat = client.chats.create(model=model)
                response = chat.send_message(prompt)
                text = response.candidates[0].content.parts[0].text.strip()
                # Strip surrounding quotes if Gemini added them
                text = text.strip('"').strip("'")
                return text
            except genai.errors.ServerError as e:
                if "503" in str(e) or "UNAVAILABLE" in str(e):
                    if attempt < 2:
                        time.sleep(15)
                    else:
                        break
                else:
                    raise
            except genai.errors.ClientError as e:
                if "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e):
                    break
                else:
                    raise
    return ""


def build_roster_summary(roster: dict, player_map: dict) -> str:
    lines = []
    pos_labels = {"F": "Forwards", "D": "Defence", "G": "Goalies"}
    for pos, label in pos_labels.items():
        slugs = roster.get(pos, [])
        players = []
        for s in slugs:
            p = player_map.get(s)
            if p:
                name = p.get("player_name", s)
                if pos == "G":
                    pts = (p.get("wins", 0) or 0) * 2 + (p.get("ot_losses", 0) or 0) + (p.get("shutouts", 0) or 0) * 3
                elif pos == "D":
                    pts = (p.get("goals", 0) or 0) * 2 + (p.get("assists", 0) or 0)
                else:
                    pts = p.get("points", 0) or 0
                players.append(f"{name} ({pts}pts)")
        if players:
            lines.append(f"{label}: {', '.join(players)}")
    return "\n".join(lines)


def best_player_and_weak_pos(roster: dict, player_map: dict) -> tuple[str, str]:
    pos_totals = {"F": 0, "D": 0, "G": 0}
    best_name, best_pts = "Unknown", -1
    for pos in ("F", "D", "G"):
        for s in roster.get(pos, []):
            p = player_map.get(s)
            if not p:
                continue
            if pos == "G":
                pts = (p.get("wins", 0) or 0) * 2 + (p.get("ot_losses", 0) or 0) + (p.get("shutouts", 0) or 0) * 3
            elif pos == "D":
                pts = (p.get("goals", 0) or 0) * 2 + (p.get("assists", 0) or 0)
            else:
                pts = p.get("points", 0) or 0
            pos_totals[pos] += pts
            if pts > best_pts:
                best_pts = pts
                best_name = p.get("player_name", s)
    labels = {"F": "Forwards", "D": "Defence", "G": "Goalies"}
    weak_pos = labels[min(pos_totals, key=pos_totals.get)]
    return best_name, weak_pos


def gemini_pool_summary(standings_snapshot: str, week_date: str) -> str:
    client = genai.Client(api_key=GOOGLE_API_KEY)
    prompt = f"""You are a witty, sharp hockey pool analyst — TSN panel energy meets locker-room banter.

Write a weekly pool summary of 3-4 sentences for a fantasy hockey pool.
Structure:
  1. Open with the overall state of the pool — who's on top, how tight is it?
  2. Call out the biggest mover or shaker this week — who climbed, who fell, and why (based on their pts).
  3. Any drama at the top or bottom worth noting?
  4. Close with a spicy prediction or observation for the week ahead.

Rules:
- Reference team names and manager names directly — make it personal.
- Light banter and friendly trash talk welcome. Keep it fun, not mean.
- No emojis. No bullet points. Plain prose only. No quotes around the response.
- Write as if you're reading it live on a broadcast.

Week of: {week_date}
Current standings (rank, team, manager, pts, change from last week):
{standings_snapshot}

Weekly pool summary:"""

    models = [
        "models/gemini-2.5-flash",
        "models/gemini-2.5-flash-lite",
        "models/gemini-3.8-flash",
        "models/gemini-3.1-flash-lite",
    ]
    for model in models:
        for attempt in range(3):
            try:
                chat = client.chats.create(model=model)
                response = chat.send_message(prompt)
                text = response.candidates[0].content.parts[0].text.strip().strip('"').strip("'")
                return text
            except genai.errors.ServerError as e:
                if "503" in str(e) or "UNAVAILABLE" in str(e):
                    if attempt < 2:
                        time.sleep(15)
                    else:
                        break
                else:
                    raise
            except genai.errors.ClientError as e:
                if "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e):
                    break
                else:
                    raise
    return ""


# ── Main ───────────────────────────────────────────────────────────────────────

def playerPoolScore_py(p: dict, pos: str) -> int:
    """Compute pool points for a single player row given their position."""
    pos = pos.upper()
    if pos == "G":
        return (p.get("wins") or 0) * 2 + (p.get("ot_losses") or 0) + (p.get("shutouts") or 0) * 3
    if pos == "D":
        return (p.get("goals") or 0) * 2 + (p.get("assists") or 0)
    return (p.get("points") or 0)


def main():
    print("🏒 Updating pool standings metadata...")

    # Fetch all submissions
    subs_res = supabase.table("pool_2027_submissions").select(
        "id,name,team_name,roster,cap_used,rank_previous,scouting_report"
    ).execute()
    submissions = subs_res.data
    if not submissions:
        print("No submissions found.")
        return

    # Fetch all players
    players_res = supabase.table("nhl_players").select(
        "puckpedia_slug,player_name,position,goals,assists,points,wins,ot_losses,shutouts,games_played"
    ).limit(1000).execute()
    player_map = {p["puckpedia_slug"]: p for p in players_res.data}

    # Score everyone and build current ranking (by total pts)
    scored = []
    for sub in submissions:
        roster = sub.get("roster") or {}
        total = score_team(roster, player_map)
        scored.append({**sub, "total": total})
    scored.sort(key=lambda x: -x["total"])

    current_ranks = {s["id"]: i + 1 for i, s in enumerate(scored)}
    today = date.today()
    monday = last_monday()

    # ── Weekly snapshot ──────────────────────────────────────────────────────
    snapshot = load_weekly_snapshot()
    snapshot_date_str = snapshot.get("date", "")
    snapshot_monday = monday.isoformat()

    if snapshot_date_str != snapshot_monday:
        # New week — save current totals as baseline and reset weekly_pts to 0
        print(f"📅 New week starting {snapshot_monday} — resetting weekly snapshot")
        new_snapshot = {"date": snapshot_monday, "totals": {s["id"]: s["total"] for s in scored}}
        save_weekly_snapshot(new_snapshot)
        snapshot = new_snapshot

    baseline = snapshot.get("totals", {})

    # ── Rank snapshot (previous rank stored daily) ───────────────────────────
    # Load yesterday's ranks from a simple JSON sidecar
    rank_snapshot_file = "data/pool_rank_snapshot.json"
    prev_ranks = {}
    if os.path.exists(rank_snapshot_file):
        with open(rank_snapshot_file) as f:
            prev_ranks = json.load(f).get("ranks", {})

    # ── Update each submission ───────────────────────────────────────────────
    print(f"📊 Updating {len(scored)} submissions...")

    for i, sub in enumerate(scored):
        sid = sub["id"]
        rank = current_ranks[sid]
        prev_rank = prev_ranks.get(sid)
        weekly_pts = sub["total"] - baseline.get(sid, sub["total"])

        existing_report = sub.get("scouting_report") or ""
        should_generate = (not existing_report) or (today.weekday() == 0)

        report = existing_report
        if should_generate and GOOGLE_API_KEY:
            print(f"  ✍️  Generating scouting report for {sub.get('team_name') or sub['name']} (#{rank})...")
            roster = sub.get("roster") or {}
            roster_summary = build_roster_summary(roster, player_map)
            best_player, weak_pos = best_player_and_weak_pos(roster, player_map)
            try:
                report = gemini_scouting_report(
                    team_name=sub.get("team_name") or sub["name"],
                    owner=sub["name"],
                    roster_summary=roster_summary,
                    total_pts=sub["total"],
                    rank=rank,
                    prev_rank=prev_rank,
                    best_player=best_player,
                    weak_pos=weak_pos,
                )
            except Exception as e:
                print(f"    ⚠️  Gemini failed for {sub.get('team_name') or sub['name']}: {e}")
                report = existing_report
            time.sleep(2)

        update_data = {
            "rank_previous": prev_rank,
            "weekly_pts": max(0, weekly_pts),
            "rank_snapshot_date": today.isoformat(),
        }
        if report:
            update_data["scouting_report"] = report

        supabase.table("pool_2027_submissions").update(update_data).eq("id", sid).execute()
        direction = ""
        if prev_rank and prev_rank != rank:
            direction = f" (was #{prev_rank})"
        print(f"  #{rank}{direction} {sub.get('team_name') or sub['name']} — {sub['total']}pts, +{max(0,weekly_pts)} this week")

    # Save today's ranks for tomorrow's comparison
    new_rank_snapshot = {"date": today.isoformat(), "ranks": current_ranks}
    with open(rank_snapshot_file, "w") as f:
        json.dump(new_rank_snapshot, f, indent=2)

    # ── Append to history file ───────────────────────────────────────────────
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            history = json.load(f)

    today_str = today.isoformat()

    # Build per-player pool pts snapshot: slug → pts today
    player_pts_snapshot = {}
    for s in scored:
        roster = s.get("roster") or {}
        for pos in ("F", "D", "G"):
            for slug in (roster.get(pos) or []):
                if slug and slug not in player_pts_snapshot:
                    p = player_map.get(slug)
                    if p:
                        player_pts_snapshot[slug] = playerPoolScore_py(p, pos)

    # Replace today's entry if already present (idempotent re-runs)
    history = [h for h in history if h["date"] != today_str]
    history.append({
        "date": today_str,
        "teams": [
            {
                "id": s["id"],
                "name": s["name"],
                "team_name": s.get("team_name") or s["name"],
                "total": s["total"],
                "rank": current_ranks[s["id"]],
            }
            for s in scored
        ],
        "player_pts": player_pts_snapshot,
    })
    history.sort(key=lambda h: h["date"])
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

    # ── Weekly pool summary (generate on Mondays or if missing) ─────────────
    existing_summary = {}
    if os.path.exists(POOL_SUMMARY_FILE):
        with open(POOL_SUMMARY_FILE) as f:
            existing_summary = json.load(f)

    should_generate_summary = ((not existing_summary.get("text")) or (today.weekday() == 0)) and bool(GOOGLE_API_KEY)
    if should_generate_summary:
        print("✍️  Generating weekly pool summary...")
        # Build standings snapshot string for the prompt
        lines = []
        for s in scored:
            rank = current_ranks[s["id"]]
            prev = prev_ranks.get(s["id"])
            change = ""
            if prev and prev != rank:
                diff = prev - rank
                change = f"↑{diff}" if diff > 0 else f"↓{abs(diff)}"
            weekly = s["total"] - baseline.get(s["id"], s["total"])
            lines.append(f"#{rank} {s.get('team_name') or s['name']} ({s['name']}) — {s['total']}pts, +{max(0,weekly)} this week {change}".strip())
        standings_snapshot = "\n".join(lines)
        week_label = monday.strftime("%B %d, %Y")
        try:
            summary_text = gemini_pool_summary(standings_snapshot, week_label)
        except Exception as e:
            print(f"  ⚠️  Pool summary failed: {e}")
            summary_text = existing_summary.get("text", "")

        if summary_text:
            summary_data = {
                "text": summary_text,
                "week": monday.isoformat(),
                "generated_at": today.isoformat(),
            }
            with open(POOL_SUMMARY_FILE, "w") as f:
                json.dump(summary_data, f, indent=2)
            print("✅ Pool summary saved.")

    print(f"✅ Pool standings updated. History now has {len(history)} day(s).")

    # ── Yesterday's pool pts per player (nhl_player_id → pts) ───────────────
    try:
        import urllib.request
        yesterday_str = (today - timedelta(days=1)).isoformat()
        YDAY_FILE = "docs/data/player_yesterday_pts.json"

        # Collect all unique nhl_player_ids across all pool rosters
        all_leagues = supabase.table("pool_rosters").select("league_code,data").execute().data
        all_slugs = set()
        for row in all_leagues:
            for team in (row.get("data") or {}).get("teams", []):
                for pos in ("F", "D", "G"):
                    all_slugs.update(s for s in (team.get("roster") or {}).get(pos, []) if s)

        # Build slug → (nhl_player_id, position) from player_map
        slug_to_id = {}
        for slug, p in player_map.items():
            if slug in all_slugs and p.get("nhl_player_id"):
                slug_to_id[slug] = (p["nhl_player_id"], (p.get("position") or "F"))

        def score_game_for_pool(g: dict, pos: str) -> int:
            pos = pos.upper()
            if pos == "G":
                decision = (g.get("decision") or "").upper()
                so = 1 if g.get("shutouts") or g.get("shots_against", 1) and not g.get("goals_against") else 0
                wins = 1 if decision == "W" else 0
                return wins * 2 + so * 3
            if pos == "D":
                return (g.get("goals") or 0) * 2 + (g.get("assists") or 0)
            return (g.get("points") or 0) or ((g.get("goals") or 0) + (g.get("assists") or 0))

        yday_pts = {}  # nhl_player_id (str) → pool pts
        season = "20262027"
        for slug, (pid, pos) in slug_to_id.items():
            try:
                url = f"https://api-web.nhle.com/v1/player/{pid}/game-log/{season}/2"
                with urllib.request.urlopen(url, timeout=8) as r:
                    data_gl = json.loads(r.read())
                games = data_gl.get("gameLog") or []
                pts = sum(score_game_for_pool(g, pos) for g in games
                          if (g.get("gameDate") or "")[:10] == yesterday_str)
                if pts > 0:
                    yday_pts[str(pid)] = pts
            except Exception:
                pass

        os.makedirs(os.path.dirname(YDAY_FILE), exist_ok=True)
        with open(YDAY_FILE, "w") as f:
            json.dump({"date": yesterday_str, "pts": yday_pts}, f)
        print(f"📊  Yesterday pts: {len(yday_pts)} players scored")
    except Exception as e:
        print(f"  ⚠️  Yesterday pts fetch failed: {e}")

    # ── NHL today's games (for pool standings page badge) ────────────────────
    try:
        import urllib.request
        NHL_TODAY_FILE = "docs/data/nhl_today.json"
        with urllib.request.urlopen("https://api-web.nhle.com/v1/schedule/now", timeout=10) as r:
            sched = json.loads(r.read())
        matchups = {}  # abbrev → opponent abbrev
        games = []
        for week_day in sched.get("gameWeek", []):
            if week_day.get("date") == today_str:
                for g in week_day.get("games", []):
                    away = g.get("awayTeam", {}).get("abbrev")
                    home = g.get("homeTeam", {}).get("abbrev")
                    if away and home:
                        matchups[away] = home
                        matchups[home] = away
                        games.append({"away": away, "home": home})
                break
        os.makedirs(os.path.dirname(NHL_TODAY_FILE), exist_ok=True)
        with open(NHL_TODAY_FILE, "w") as f:
            json.dump({"date": today_str, "matchups": matchups, "games": games}, f)
        print(f"🏒  NHL today: {len(games)} games, {len(matchups)} teams playing")
    except Exception as e:
        print(f"  ⚠️  NHL today schedule fetch failed: {e}")


if __name__ == "__main__":
    main()
