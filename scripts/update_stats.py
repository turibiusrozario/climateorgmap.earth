#!/usr/bin/env python3
"""Write stats.json from maps.json: one health check and one set of counts per live map.

Health: "up" (site and data feed respond), "degraded" (site up, feed down, snapshot used),
"down" (site unreachable). If no data source answers, the previous counts are kept.
"""
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = "climateorgmap-stats/1.0 (+https://climateorgmap.earth)"


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch(url, tries=3, timeout=60, as_json=False):
    """Return (http_status_or_None, parsed_body_or_None)."""
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read()
                return r.status, (json.loads(body) if as_json else body)
        except urllib.error.HTTPError as e:
            status = e.code
        except Exception:
            status = None
        if i < tries - 1:
            time.sleep(5 * (i + 1))
    return status, None


def count(feed):
    """Counts from a map feed. Item ids are deduplicated across orgs and coalitions."""
    orgs = feed["organizations"]
    coalitions = feed.get("coalitions", [])

    def items(key):
        seen = {}
        for owner in orgs + coalitions:
            for it in owner.get(key) or []:
                seen[it.get("id") or id(it)] = it
        return len(seen)

    activity = [o["last_activity"] for o in orgs + coalitions if o.get("last_activity")]
    return {
        "organizations": len(orgs),
        "coalitions": len(coalitions),
        "events": items("events"),
        "projects": items("projects"),
        "actions": items("actions"),
        "last_updated": max(activity) if activity else None,
    }


def valid(feed):
    return isinstance(feed, dict) and isinstance(feed.get("organizations"), list) and len(feed["organizations"]) > 0


def check(m, previous):
    t = now()
    site_status, _ = fetch(m["url"], tries=2, timeout=20)
    site_ok = site_status is not None and 200 <= site_status < 400
    out = {"checked_at": t, "site": {"ok": site_ok, "http": site_status}}

    feed = data = None
    if m.get("feed"):
        _, feed = fetch(m["feed"], as_json=True)
        out["feed"] = {"ok": valid(feed)}
    if not valid(feed) and m.get("data"):
        _, data = fetch(m["data"], as_json=True)
        out["snapshot"] = {"ok": valid(data)}

    if valid(feed):
        out["source"] = "feed"
        out.update(count(feed))
        out["feed_generated_at"] = feed.get("generated_at")
    elif valid(data):
        out["source"] = "snapshot"
        out.update(count(data))
        out["feed_generated_at"] = data.get("generated_at")
    elif previous:
        out["source"] = "previous"
        for k in ("organizations", "coalitions", "events", "projects", "actions", "last_updated", "feed_generated_at"):
            out[k] = previous.get(k)
        out["counts_as_of"] = previous.get("counts_as_of") or previous.get("checked_at")
    else:
        out["source"] = None

    if out["source"] in ("feed", "snapshot"):
        out["counts_as_of"] = t

    if not site_ok:
        out["health"] = "down"
    elif out["source"] == "feed" or not m.get("feed"):
        out["health"] = "up"
    else:
        out["health"] = "degraded"
    return out


def main():
    maps = json.loads((ROOT / "maps.json").read_text())
    stats_path = ROOT / "stats.json"
    try:
        old = json.loads(stats_path.read_text()).get("maps", {})
    except (OSError, ValueError):
        old = {}
    result = {"generated_at": now(), "maps": {}}
    for m in maps:
        if m.get("status") != "live":
            continue
        result["maps"][m["id"]] = check(m, old.get(m["id"]))
        print(m["id"], result["maps"][m["id"]]["health"], file=sys.stderr)
    stats_path.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
