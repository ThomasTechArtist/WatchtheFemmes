# Watch the Femmes

Women's professional cycling for a TRMNL e-ink display: Tour de France Femmes, Giro d'Italia Women and La Vuelta Femenina.

## Status

First milestone: a tested collector of the top five general-classification riders from each race's official website. The collector records the race edition, source URL, retrieval time and failures separately. An old edition is never described as a live race.

**This repository is not yet an installed TRMNL plugin.** Calendar mode, jersey leaders, stage details, TRMNL markup and automatic delivery are the next milestones. The existing home-calendar playlist is unchanged by this repository.

## Run

Use Python 3.11 or later:

```sh
python -m venv .venv
# Activate the environment using the command appropriate to your operating system.
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python collect.py
```

Output is `data/latest.json`. An unsuccessful source preserves its last good results with `stale: true` and the original `last_success_at`; a source with no previous results has an empty list. The collector exits nonzero when any source fails. Do not present `checked_at` as the time the race results changed.

No Pi installation, Pi-hole changes, passwords or TRMNL webhook are required for collection. Never commit credentials, webhook URLs, exported passwords or private files.

## Sources

- Tour de France Femmes: https://www.letourfemmes.fr/en/rankings
- Giro d'Italia Women: https://www.giroditaliawomen.it/en/rankings/
- La Vuelta Femenina: https://www.lavueltafemenina.es/en/rankings
- Calendar candidate: UCI Women's WorldTour calendar; use official organisers to cross-check dates.

The parsers read public HTML, not a promised or documented results API. Changes to the organisers' page layouts can break retrieval. Keep requests modest; stop on access denials rather than trying to evade them. The JSON contains extracted factual standings, not copies of source pages, photographs or branding.

## Next milestones

1. Verify upcoming race dates and their editions; create a calendar feed with source links. Dates absent from official sources remain unknown.
2. Add race-state selection: upcoming, in progress, completed. Only label a race live or final when the source supports it.
3. Build full-screen TRMNL markup with upcoming races between events and top five GC during events. Add jersey leaders and stage information after separate source tests.
4. Test rendered previews and source failures before installing the private plugin.
5. Set up daily retrieval between races and 30-minute retrieval during races. Choose TRMNL polling of public JSON or GitHub Actions plus a secret webhook after testing. No external sender is currently scheduled.
6. Keep the home calendar dominant. Proposed rotation: calendar 30m, Pi-hole 5m, men's cycling 5m, calendar 30m, Watch the Femmes 5m (80% calendar). This proposal has not been applied.

CI runs parser tests only. The **Check official sources** workflow can be run manually to collect current data into a downloadable artifact. It does not publish data or change TRMNL.
