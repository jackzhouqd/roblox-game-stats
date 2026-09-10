# roblox-game-stats

A single-file CLI that prints the live public stats for any Roblox experience — concurrent players, total visits, favorites, and the up/down vote split.

No dependencies, no API key, no account. Python 3.10+ and the standard library.

## Why

Roblox shows you a number on the game page, but that number is a snapshot. If you want to know whether a game is actually growing — as opposed to having had one good afternoon — you need the same number on consecutive days. This makes that cheap enough to cron.

I wrote it while tracking a game that went from roughly 4.8M to 5.4M lifetime visits in about 24 hours, which is the kind of thing you only notice if you're writing it down.

## Install

```
git clone https://github.com/jackzhouqd/roblox-game-stats.git
cd roblox-game-stats
python roblox_stats.py --help
```

That's it. There is nothing to install.

## Usage

It accepts a universe ID, a place ID, or a roblox.com game URL — whichever you happen to have.

```
$ python roblox_stats.py 9656201728
        Game  Dungeon Lootr [RELEASE]  by ClickBytes
 Universe ID  9656201728
 Playing now  11,070
Total visits  5,411,125
   Favorites  30,010
    Approval  96.1%  (19,662 up / 794 down)
 Server size  15 players
     Created  2026-01-31T23:35:17.687Z
Last updated  2026-09-02T23:06:30.9946842Z
```

```
$ python roblox_stats.py https://www.roblox.com/games/106484206883664/Dungeon-Lootr
```

```
$ python roblox_stats.py 9656201728 --json
{
  "universeId": 9656201728,
  "name": "Dungeon Lootr [RELEASE]",
  "creator": "ClickBytes",
  "playing": 11070,
  "visits": 5411125,
  "favorites": 30010,
  "maxPlayers": 15,
  "created": "2026-01-31T23:35:17.687Z",
  "updated": "2026-09-02T23:06:30.9946842Z",
  "upVotes": 19662,
  "downVotes": 794,
  "approvalPct": 96.1
}
```

## Logging a time series

The `--json` output is meant to be piped. To append one row per day:

```
python roblox_stats.py 9656201728 --json \
  | python -c "import json,sys,datetime;d=json.load(sys.stdin);print(datetime.date.today(),d['visits'],d['playing'],d['favorites'],sep=',')" \
  >> visits.csv
```

Put that in cron or Task Scheduler and you have a growth curve in a week.

The example above is Dungeon Lootr, which is what I happened to be tracking — the daily numbers and what I made of them are on [dungeonlootrgame.com](https://dungeonlootrgame.com/).

## Endpoints used

All three are public and unauthenticated:

| Endpoint | Purpose |
| --- | --- |
| `games.roblox.com/v1/games?universeIds=` | name, creator, playing, visits, favorites, server size, timestamps |
| `games.roblox.com/v1/games/votes?universeIds=` | up/down votes |
| `apis.roblox.com/universes/v1/places/{id}/universe` | place ID to universe ID |

Roblox rate-limits by IP. One call every few seconds is fine; a tight loop is not.

## Caveats

- `playing` is concurrent players at the moment of the request, so it swings with time of day and time zone. Compare like with like — same hour each day.
- `visits` is lifetime and monotonic. Daily deltas are the useful signal, not the absolute number.
- Private or deleted experiences return no data; the script exits non-zero with a message rather than printing a half-empty table.
- Nothing here is scraped. If Roblox changes these endpoints, the script breaks loudly instead of returning wrong numbers.

## License

MIT — see [LICENSE](LICENSE).

## Tracking games

| Ball VS Ball | 10685282333 | tracking since 2026-09-05 | notes & tested data: [ballvsballgame.com](https://ballvsballgame.com/) |

| Command An Army | 10258991999 | tracking since 2026-09-06 | field notes: [commandanarmy.com](https://commandanarmy.com/) |
