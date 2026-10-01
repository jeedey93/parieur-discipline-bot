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
    print("❌ Missing GOOGLE_API_KEY")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
tz = ZoneInfo("America/Toronto")

WEEKLY_SNAPSHOT_FILE = "data/pool_weekly_snapshot.json"


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
  2. Break down their roster reality: name their best player and call out what position group is dragging them.
  3. Close with a sharp prediction or a dig about where they're headed.

Rules:
- Friendly banter only, no mean-spirited attacks.
- Be specific — use the actual player names and stats provided.
- No emojis. No hashtags. No bullet points. Plain prose only.
- Do not add quotes around your response.

Team: {team_name} (managed by {owner})
Current rank: #{rank} {rank_note}
Total pool points: {total_pts}
Best player: {best_player}
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


# ── Main ───────────────────────────────────────────────────────────────────────

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
        if should_generate:
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

    print(f"✅ Pool standings updated. Rank snapshot saved for {today}.")


if __name__ == "__main__":
    main()
