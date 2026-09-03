#!/usr/bin/env python3
"""Fetch live public stats for a Roblox experience.

No dependencies, no API key. Accepts a universe ID, a place ID, or a
roblox.com game URL, and prints the numbers Roblox exposes publicly:
concurrent players, total visits, favorites, and the up/down vote split.

    python roblox_stats.py 9656201728
    python roblox_stats.py https://www.roblox.com/games/106484206883664/Dungeon-Lootr
    python roblox_stats.py 9656201728 --json

Useful if you want to track whether a game is actually growing rather than
trusting a one-off screenshot. Pair it with cron and append to a CSV.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

GAMES_API = "https://games.roblox.com/v1/games"
VOTES_API = "https://games.roblox.com/v1/games/votes"
UNIVERSE_API = "https://apis.roblox.com/universes/v1/places/{place_id}/universe"

UA = "roblox-game-stats/1.0 (+https://github.com/jackzhouqd/roblox-game-stats)"
TIMEOUT = 20


class RobloxError(RuntimeError):
    pass


def _get(url: str, params: dict | None = None) -> dict:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RobloxError(f"{url} returned HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RobloxError(f"could not reach {url}: {exc.reason}") from exc


def resolve_universe_id(target: str) -> int:
    """Turn a universe ID, place ID, or game URL into a universe ID."""
    target = target.strip()

    match = re.search(r"roblox\.com/games/(\d+)", target)
    if match:
        return _place_to_universe(int(match.group(1)))

    if not target.isdigit():
        raise RobloxError(f"cannot parse {target!r} as an ID or a roblox.com game URL")

    ident = int(target)

    # A universe ID resolves directly; a place ID does not. Try universe first.
    data = _get(GAMES_API, {"universeIds": ident})
    if data.get("data"):
        return ident

    return _place_to_universe(ident)


def _place_to_universe(place_id: int) -> int:
    data = _get(UNIVERSE_API.format(place_id=place_id))
    universe_id = data.get("universeId")
    if not universe_id:
        raise RobloxError(f"place {place_id} has no universe (deleted or private?)")
    return int(universe_id)


def fetch(universe_id: int) -> dict:
    games = _get(GAMES_API, {"universeIds": universe_id}).get("data") or []
    if not games:
        raise RobloxError(f"universe {universe_id} returned no data (private or deleted?)")
    game = games[0]

    votes = (_get(VOTES_API, {"universeIds": universe_id}).get("data") or [{}])[0]
    up = votes.get("upVotes", 0)
    down = votes.get("downVotes", 0)
    total = up + down

    return {
        "universeId": universe_id,
        "name": game.get("name"),
        "creator": (game.get("creator") or {}).get("name"),
        "playing": game.get("playing"),
        "visits": game.get("visits"),
        "favorites": game.get("favoritedCount"),
        "maxPlayers": game.get("maxPlayers"),
        "created": game.get("created"),
        "updated": game.get("updated"),
        "upVotes": up,
        "downVotes": down,
        "approvalPct": round(up / total * 100, 1) if total else None,
    }


def render(stats: dict) -> str:
    approval = (
        f"{stats['approvalPct']}%  ({stats['upVotes']:,} up / {stats['downVotes']:,} down)"
        if stats["approvalPct"] is not None
        else "no votes yet"
    )
    rows = [
        ("Game", f"{stats['name']}  by {stats['creator']}"),
        ("Universe ID", str(stats["universeId"])),
        ("Playing now", f"{stats['playing']:,}"),
        ("Total visits", f"{stats['visits']:,}"),
        ("Favorites", f"{stats['favorites']:,}"),
        ("Approval", approval),
        ("Server size", f"{stats['maxPlayers']} players"),
        ("Created", stats["created"]),
        ("Last updated", stats["updated"]),
    ]
    width = max(len(label) for label, _ in rows)
    return "\n".join(f"{label.rjust(width)}  {value}" for label, value in rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fetch live public stats for a Roblox experience.",
        epilog="Accepts a universe ID, a place ID, or a roblox.com game URL.",
    )
    parser.add_argument("target", help="universe ID, place ID, or roblox.com game URL")
    parser.add_argument("--json", action="store_true", help="print raw JSON instead of a table")
    args = parser.parse_args(argv)

    try:
        stats = fetch(resolve_universe_id(args.target))
    except RobloxError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(stats, indent=2) if args.json else render(stats))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
