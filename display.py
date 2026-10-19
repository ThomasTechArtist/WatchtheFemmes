"""Race-day aware display model, independent of TRMNL and network access."""
from datetime import date, datetime, timezone
import json
from pathlib import Path


def load_calendar():
    entries = json.loads(Path(__file__).with_name('calendar.json').read_text())
    for entry in entries:
        if date.fromisoformat(entry['end']) < date.fromisoformat(entry['start']):
            raise ValueError('Race end precedes start')
        if date.fromisoformat(entry['start']).year != entry['edition']:
            raise ValueError('Race date and edition mismatch')
    return sorted(entries, key=lambda e: e['start'])


def build_display(payload, calendar=None, today=None):
    today = today or datetime.now(timezone.utc).date()
    calendar = load_calendar() if calendar is None else calendar
    forthcoming = sorted([e for e in calendar if date.fromisoformat(e['end']) >= today], key=lambda e: e['start'])
    active = next((e for e in forthcoming if date.fromisoformat(e['start']) <= today <= date.fromisoformat(e['end'])), None)
    upcoming = [dict(e, days_to_go=(date.fromisoformat(e['start']) - today).days,
                     date_label=date.fromisoformat(e['start']).strftime('%d %b') + ' – ' + date.fromisoformat(e['end']).strftime('%d %b %Y'))
                for e in forthcoming[:3]]
    focus = None
    if active:
        # Never show last year's GC as the standings of a currently running race.
        focus = next((r for r in payload['races'] if r['key'] == active['key'] and r.get('edition') == active['edition'] and r.get('standings')), None)
    return {'mode': 'race' if active else 'calendar', 'upcoming': upcoming,
            'active_race': active, 'focus': focus, 'calendar_verified_at': min((e['verified_at'] for e in forthcoming), default=None)}


def refresh_due(payload, now=None, calendar=None):
    now = now or datetime.now(timezone.utc)
    model = build_display(payload or {'races': []}, calendar=calendar, today=now.date())
    last = (payload or {}).get('checked_at')
    if not last:
        return True
    try:
        elapsed = (now - datetime.fromisoformat(last)).total_seconds()
    except (ValueError, TypeError):
        return True
    return elapsed >= (25 * 60 if model['mode'] == 'race' else 23 * 3600)


if __name__ == '__main__':
    import sys
    path = Path('data/latest.json')
    payload = json.loads(path.read_text()) if path.exists() else None
    print('true' if '--force' in sys.argv or refresh_due(payload) else 'false')
