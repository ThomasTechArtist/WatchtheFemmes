# Watch the Femmes

Women's professional cycling for a TRMNL e-ink display: Tour de France Femmes, Giro d'Italia Women and La Vuelta Femenina.

## Working version

- Installed private TRMNL plugin: **Watch the Femmes**, instance `511645`.
- Between races: the three confirmed forthcoming Grand Tours, countdowns and latest published GC leaders, with edition labels.
- During a configured race: its top five overall riders, teams and gaps, with stage number when the source supplies one. Prior editions are never presented as the current race.
- GC rider portraits are linked from official organiser image hosts. Tour and Vuelta profiles supply the top five; Giro uses initials until rider portraits are available. Missing portraits show initials, and optional image failures do not hide standings.
- Source failures preserve the last successful results and mark them stale. A feed older than 48 hours displays an overdue notice.
- GitHub Actions publishes public factual JSON. Collection is daily between configured races and approximately every 30 minutes during them. GitHub scheduled jobs can be delayed; this is not second-by-second tracking.
- TRMNL polls the JSON at a maximum frequency of every 30 minutes. Rendering also depends on the device checking in.

The first automatic publication and GitHub CI both passed. Seventeen unit tests cover source parsing, failure preservation, race boundaries, edition isolation and refresh cadence. The actual TRMNL preview was checked for readable layout and real polled data.

## Install or update the screen

```sh
python package_plugin.py
```

In TRMNL, open Plugins > Private Plugin > Import new, then import `dist/watch-the-femmes.zip`. This creates a **new** instance; to update an existing one, replace its Full markup with `src/full.liquid` instead. Avoid importing a duplicate on each edit.

The settings point to:

https://raw.githubusercontent.com/ThomasTechArtist/WatchtheFemmes/main/data/latest.json?v=portraits-2

No TRMNL API key, private webhook, Pi installation or Pi-hole changes are needed. Source and markup are stored here; automatic two-way TRMNL GitHub Sync has not been enabled.

## Run the collector locally

Use Python 3.11 or later:

```sh
python -m venv .venv
# Activate the environment using the command appropriate to your operating system.
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python collect.py
```

Output is `data/latest.json`. An unsuccessful source preserves its last good results with `stale: true` and the original `last_success_at`; a source with no previous results has an empty list. The collector exits nonzero when any source fails. `checked_at` means retrieval time, not when race results changed.

## Calendar dates and sources

`calendar.json` contains the **manually verified** 2027 dates and their official source links, checked on 18 October 2026. They are not re-scraped by the standings collector. Update the file if organisers change dates, and add subsequent seasons; expired dates are not silently repeated next year. Countdown and race-state dates use UTC.

- Giro Women, 29 May–6 June 2027: https://www.rcssportsandevents.it/en/event/giro-ditalia-women/
- Tour de France Femmes, 30 July–7 August 2027: https://www.letourfemmes.fr/en/
- Vuelta Femenina, 3–10 October 2027: https://uci-newsroom.prgloo.com/news/uci-management-committee-met-in-montreal-and-took-several-key-decisions-for-the-2027-season-1

Official standings sources:

- https://www.letourfemmes.fr/en/rankings
- https://www.giroditaliawomen.it/en/rankings/
- https://www.lavueltafemenina.es/en/rankings

These parsers read public HTML, not a guaranteed results API. Source layout changes can break retrieval. Requests are limited to the refresh cadence; access denials must not be evaded. No photographs or organiser branding are copied.

## Scheduled updates

`Update public cycling feed` checks every half-hour whether collection is due. Outside race windows it retrieves standings at most about once per day; during the three configured races it retrieves about twice per hour. Pushes affecting the collector/calendar and manual runs force a refresh. The job publishes only `data/latest.json`, and the commit does not trigger an update loop. It requires the standard GitHub Actions token with repository contents-write permission, scoped by this workflow. No user secrets are stored.

The separate **Check official sources** workflow is a manual diagnostic that produces a downloadable data artifact without changing TRMNL.

## Display rotation

The live rotation is calendar/weather **60 minutes**, Pi-hole **5 minutes**, men's cycling **5 minutes**, Watch the Femmes **5 minutes**. Calendar therefore receives 80% of the configured screen time. The existing appointment-focus markup is unchanged.

## Remaining enhancements

- Jersey leaders and next-stage route details need separately verified adapters.
- Expand the calendar beyond the three women's Grand Tours.
- Automate calendar-date verification and add future seasons.
- Offer per-race selection and optional no-spoiler mode.

Never commit credentials, webhook URLs, exported passwords or private files.
