from datetime import datetime, timedelta
from typing import List, Dict, Optional
from icalendar import Calendar, Event as ICalEvent, vText, vDDDTypes
from dateutil import parser
import json
import csv
from io import StringIO


def export_events_to_ical(events: List[Dict]) -> str:
    cal = Calendar()
    cal.add('prodid', '-//Vocal Calendar//EN')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('method', 'PUBLISH')

    for event in events:
        cal_event = ICalEvent()

        cal_event.add('uid', event.get('id', ''))
        cal_event.add('dtstamp', datetime.now())
        cal_event.add('dtstart', _parse_datetime(event.get('start_time')))
        cal_event.add('dtend', _parse_datetime(event.get('end_time')))
        cal_event.add('summary', vText(event.get('title', '')))

        if event.get('description'):
            cal_event.add('description', vText(event.get('description')))

        if event.get('location'):
            cal_event.add('location', vText(event.get('location')))

        if event.get('priority'):
            cal_event.add('priority', int(event.get('priority', 0)))

        if event.get('recurrence_rule'):
            cal_event.add('rrule', vText(event.get('recurrence_rule')))

        cal_event.add('created', _parse_datetime(event.get('created_at', datetime.now())))
        cal_event.add('last-modified', _parse_datetime(event.get('updated_at', datetime.now())))

        cal.add_component(cal_event)

    return cal.to_ical().decode('utf-8')


def import_events_from_ical(ical_content: str) -> List[Dict]:
    events = []
    cal = Calendar.from_ical(ical_content)

    for component in cal.walk('VEVENT'):
        event = {
            'id': str(component.get('uid', '')),
            'title': str(component.get('summary', '')),
            'description': str(component.get('description', '')) if component.get('description') else None,
            'location': str(component.get('location', '')) if component.get('location') else None,
            'start_time': _format_datetime(_parse_ical_datetime(component.get('dtstart'))),
            'end_time': _format_datetime(_parse_ical_datetime(component.get('dtend'))),
            'is_all_day': False,
            'priority': component.get('priority', 0) if component.get('priority') else 0,
            'recurrence_rule': str(component.get('rrule', '')) if component.get('rrule') else None,
        }

        if 'DTSTART;VALUE=DATE' in component:
            event['is_all_day'] = True

        events.append(event)

    return events


def export_events_to_json(events: List[Dict], include_metadata: bool = True) -> str:
    export_data = {
        'version': '1.0',
        'exported_at': datetime.now().isoformat(),
        'event_count': len(events),
        'events': events,
    }

    if include_metadata:
        export_data['metadata'] = {
            'app': 'Vocal Calendar',
            'timezone': 'Asia/Shanghai',
        }

    return json.dumps(export_data, ensure_ascii=False, indent=2)


def import_events_from_json(json_content: str) -> List[Dict]:
    data = json.loads(json_content)

    if 'events' in data:
        return data['events']

    if isinstance(data, list):
        return data

    raise ValueError("Invalid JSON format for events import")


def export_events_to_csv(events: List[Dict]) -> str:
    if not events:
        return ""

    output = StringIO()
    fieldnames = [
        'id', 'title', 'description', 'start_time', 'end_time',
        'is_all_day', 'location', 'priority', 'category_id', 'recurrence_rule'
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()

    for event in events:
        row = {
            'id': event.get('id', ''),
            'title': event.get('title', ''),
            'description': event.get('description', ''),
            'start_time': event.get('start_time', ''),
            'end_time': event.get('end_time', ''),
            'is_all_day': event.get('is_all_day', False),
            'location': event.get('location', ''),
            'priority': event.get('priority', 0),
            'category_id': event.get('category_id', ''),
            'recurrence_rule': event.get('recurrence_rule', ''),
        }
        writer.writerow(row)

    return output.getvalue()


def import_events_from_csv(csv_content: str) -> List[Dict]:
    events = []
    reader = csv.DictReader(StringIO(csv_content))

    for row in reader:
        event = {
            'title': row.get('title', ''),
            'description': row.get('description', '') or None,
            'start_time': row.get('start_time', ''),
            'end_time': row.get('end_time', ''),
            'is_all_day': row.get('is_all_day', '').lower() in ['true', '1', 'yes'],
            'location': row.get('location', '') or None,
            'priority': int(row.get('priority', 0)) if row.get('priority') else 0,
            'category_id': row.get('category_id', '') or None,
            'recurrence_rule': row.get('recurrence_rule', '') or None,
        }
        events.append(event)

    return events


def create_backup_data(
    user_id: str,
    user_email: str,
    events: List[Dict],
    categories: List[Dict]
) -> Dict:
    return {
        'backup_version': '1.0',
        'created_at': datetime.now().isoformat(),
        'user_id': user_id,
        'user_email': user_email,
        'data': {
            'events': events,
            'categories': categories,
            'event_count': len(events),
            'category_count': len(categories),
        },
        'metadata': {
            'app': 'Vocal Calendar',
            'version': '1.0.0',
            'timezone': 'Asia/Shanghai',
        },
    }


def export_backup_to_json(backup_data: Dict) -> str:
    return json.dumps(backup_data, ensure_ascii=False, indent=2)


def import_backup_from_json(json_content: str) -> Dict:
    data = json.loads(json_content)

    if 'backup_version' not in data:
        raise ValueError("Invalid backup format: missing version")

    if 'data' not in data:
        raise ValueError("Invalid backup format: missing data section")

    return data


def _parse_datetime(date_str: Optional[str]) -> datetime:
    if not date_str:
        return datetime.now()

    if isinstance(date_str, datetime):
        return date_str

    try:
        return parser.parse(str(date_str))
    except Exception:
        return datetime.now()


def _format_datetime(dt: Optional[datetime]) -> str:
    if not dt:
        return datetime.now().isoformat()

    if isinstance(dt, datetime):
        return dt.isoformat()

    return str(dt)


def _parse_ical_datetime(dt_value) -> datetime:
    if isinstance(dt_value, datetime):
        return dt_value

    if hasattr(dt_value, 'dt'):
        dt = dt_value.dt
        if isinstance(dt, datetime):
            return dt
        return parser.parse(str(dt))

    return parser.parse(str(dt_value))
