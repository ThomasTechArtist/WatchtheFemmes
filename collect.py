"""Collect public women's Grand Tour GC tables. No credentials required."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup
from display import build_display, load_calendar

SOURCES = {
    "tour": ("Tour de France Femmes", "https://www.letourfemmes.fr/en/rankings"),
    "giro": ("Giro d'Italia Women", "https://www.giroditaliawomen.it/en/rankings/"),
    "vuelta": ("La Vuelta Femenina", "https://www.lavueltafemenina.es/en/rankings"),
}


def text(node):
    if node is None:
        raise ValueError("Required source field missing")
    return node.get_text(" ", strip=True)


def portrait_url(node):
    """Only use organiser-hosted portraits, never flags or arbitrary page images."""
    if node is None:
        return None
    for value in (node.get('data-src', ''), node.get('src', '')):
        url = value.split('|')[0]
        parts = urlsplit(url)
        if parts.scheme == 'https' and parts.hostname in {'img.aso.fr', 'static2.giroditaliawomen.it'}:
            return url
    return None


def parse_profile_portrait(html, profile_url):
    soup = BeautifulSoup(html, 'html.parser')
    canonical = soup.select_one('link[rel="canonical"]')
    if canonical and urlsplit(canonical.get('href', '')).path.rstrip('/') != urlsplit(profile_url).path.rstrip('/'):
        return None
    main = soup.select('img.riderProfile__img')
    if len(main) == 1 and portrait_url(main[0]):
        return portrait_url(main[0])
    # Team mates also have images on profile pages. Match this rider's link,
    # rather than picking the first photo (which may be a different rider).
    for anchor in soup.select('a[href]'):
        if urlsplit(urljoin(profile_url, anchor['href'])).path.rstrip('/') == urlsplit(profile_url).path.rstrip('/'):
            image = anchor.select_one('img.riderFocus__img')
            if portrait_url(image):
                return portrait_url(image)
    candidates = [i for i in soup.select('img.pageIntroJerseys__img') if not i.find_parent('a')]
    return portrait_url(candidates[0]) if len(candidates) == 1 else None


def fetch_html(url):
    request = Request(url, headers={"User-Agent": "WatchTheFemmes/0.2 (+https://github.com/ThomasTechArtist/WatchtheFemmes)"})
    with urlopen(request, timeout=30) as response:
        html = response.read(4_000_001)
        if len(html) > 4_000_000:
            raise ValueError("Source exceeds size limit")
        return html.decode(response.headers.get_content_charset() or "utf-8")


def enrich_portraits(race, fetcher=fetch_html):
    def enrich(rider):
        if not rider.get('portrait_url') and rider.get('profile_url'):
            try:
                rider['portrait_url'] = parse_profile_portrait(fetcher(rider['profile_url']), rider['profile_url'])
            except Exception:
                # Missing optional photography must not hide valid standings.
                rider['portrait_url'] = None
        parts = rider['rider'].replace('.', '').split()
        rider['initials'] = ''.join(p[0] for p in ([parts[0], parts[-1]] if len(parts) > 1 else parts)).upper()
        return rider
    with ThreadPoolExecutor(max_workers=2) as executor:
        race['standings'] = list(executor.map(enrich, race['standings']))
    return race


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
                "portrait_url": None,
            })
        leader = soup.select_one('a.single-maglia-info[data-tab="tab-classifica-CLGEN"]')
        if rows and leader:
            label = leader.select_one('h5')
            if label and sorted(text(label).casefold().split()) == sorted(rows[0]['rider'].casefold().split()):
                rows[0]['portrait_url'] = portrait_url(leader.select_one('img'))
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
            profile_link = row.select_one('td.runner a[href]')
            profile = urljoin(SOURCES[key][1], profile_link['href']) if profile_link else None
            if profile and (urlsplit(profile).hostname != urlsplit(SOURCES[key][1]).hostname or not urlsplit(profile).path.startswith('/en/rider/')):
                profile = None
            rows.append({"rank": int(fields["rank"]), "rider": fields["rider"], "team": fields["team"], "time": fields["times"], "gap": fields["gap"],
                         "portrait_url": portrait_url(row.select_one('img.rankingTables__row__profile--picture')), 'profile_url': profile})
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
    return enrich_portraits(parse_standings(key, fetch_html(SOURCES[key][1])))


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
    result = {"name": "Watch the Femmes", "schema_version": 1, "checked_at": now, "races": races, "calendar": load_calendar()}
    result['display'] = build_display(result)
    return result


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
