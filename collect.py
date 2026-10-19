"""Collect public women's Grand Tour GC tables. No credentials required."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

SOURCES = {
    "tour": ("Tour de France Femmes", "https://www.letourfemmes.fr/en/rankings"),
    "giro": ("Giro d'Italia Women", "https://www.giroditaliawomen.it/en/rankings/"),
    "vuelta": ("La Vuelta Femenina", "https://www.lavueltafemenina.es/en/rankings"),
}


def text(node):
    if node is None:
        raise ValueError("Required source field missing")
    return node.get_text(" ", strip=True)


def parse_standings(key, html):
    soup = BeautifulSoup(html, "html.parser")
    title = text(soup.title)
    expected = {"tour": "Tour de France Femmes", "giro": "Giro d'Italia Women", "vuelta": "La Vuelta Femenina"}[key]
    if expected.casefold() not in title.casefold():
        raise ValueError("Unexpected page identity; refusing unrelated results")
    if key == "giro":
        edition = re.search(r"\b(20\d{2})\b", title)
        section = soup.select_one('[data-category="tab-classifica-CLGEN"]')
        if section is None:
            raise ValueError("Giro general classification section missing")
        rows = []
        for row in section.select(".line-table")[:5]:
            rows.append({
                "rank": int(text(row.select_one(".position"))),
                "rider": text(row.select_one(".name")) + " " + text(row.select_one(".surname")),
                "team": text(row.select_one(".team")),
                "time": text(row.select_one(".tempo")),
                "gap": text(row.select_one(".distacco")),
            })
        stage = None
    else:
        heading = next((text(h) for h in soup.select("h1,h2,h3") if re.search(r"20\d{2}\s+Rankings\s*-\s*Stage\s+\d+", text(h))), "")
        edition = re.search(r"\b(20\d{2})\b", heading)
        stage_match = re.search(r"Stage\s+(\d+)", heading)
        stage = int(stage_match[1]) if stage_match else None
        table = soup.select_one("table.rankingTable")
        if table is None:
            raise ValueError("ASO standings table missing")
        headers = [text(h).casefold() for h in table.select("thead th")]
        required = ["rank", "rider", "team", "times", "gap"]
        if any(h not in headers for h in required):
            raise ValueError("Standings column layout changed")
        rows = []
        for row in table.select("tbody tr"):
            cells = row.find_all("td", recursive=False)
            if not cells:
                continue
            # Tour repeats rank in a second, mobile-only cell without a header.
            cells = [c for c in cells if not {"hidden--md", "hidden--lg"}.issubset(set(c.get("class", [])))]
            if len(cells) != len(headers):
                raise ValueError("Standings row does not match header")
            fields = dict(zip(headers, map(text, cells)))
            rows.append({"rank": int(fields["rank"]), "rider": fields["rider"], "team": fields["team"], "time": fields["times"], "gap": fields["gap"]})
            if len(rows) == 5:
                break
    if edition is None:
        raise ValueError("Race edition cannot be determined")
    if [r["rank"] for r in rows] != list(range(1, 6)):
        raise ValueError("Expected five consecutive GC positions")
    if any(not r["rider"] or not r["team"] or not r["time"] or not r["gap"] for r in rows):
        raise ValueError("Incomplete standings")
    return {"key": key, "name": SOURCES[key][0], "source_url": SOURCES[key][1], "edition": int(edition[1]), "stage": stage, "status": "Latest published GC", "standings": rows}


def fetch_race(key):
    request = Request(SOURCES[key][1], headers={"User-Agent": "WatchTheFemmes/0.1 (+https://github.com/ThomasTechArtist/WatchtheFemmes)"})
    with urlopen(request, timeout=30) as response:
        html = response.read(4_000_001)
        if len(html) > 4_000_000:
            raise ValueError("Source exceeds size limit")
        html = html.decode(response.headers.get_content_charset() or "utf-8")
    return parse_standings(key, html)


def collect(previous=None, fetcher=fetch_race, now=None):
    now = now or datetime.now(timezone.utc).isoformat()
    old = {race["key"]: race for race in (previous or {}).get("races", [])}
    def one(key):
        try:
            return dict(fetcher(key), checked_at=now, last_success_at=now, stale=False)
        except Exception as exc:
            if key in old:
                return dict(old[key], checked_at=now, stale=True, error=str(exc))
            return {"key": key, "name": SOURCES[key][0], "source_url": SOURCES[key][1], "checked_at": now, "stale": True, "error": str(exc), "standings": []}
    with ThreadPoolExecutor(max_workers=3) as executor:
        races = list(executor.map(one, SOURCES))
    return {"name": "Watch the Femmes", "schema_version": 1, "checked_at": now, "races": races}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="data/latest.json")
    args = parser.parse_args()
    target = Path(args.output)
    previous = json.loads(target.read_text()) if target.exists() else None
    result = collect(previous)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    temp.replace(target)
    for race in result["races"]:
        print(f"{race['name']}: {'STALE / UNAVAILABLE' if race['stale'] else 'OK'}; {len(race['standings'])} riders")
    if any(r["stale"] for r in result["races"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
