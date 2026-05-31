from typing import List, Dict, Optional
from app.utils.export_import import (
    export_events_to_ical,
    import_events_from_ical,
    export_events_to_json,
    import_events_from_json,
    export_events_to_csv,
    import_events_from_csv,
    create_backup_data,
    export_backup_to_json,
    import_backup_from_json
)


class ExportImportService:
    def export_events_to_ical(self, events: List[Dict]) -> str:
        return export_events_to_ical(events)

    def import_events_from_ical(self, content: str) -> List[Dict]:
        return import_events_from_ical(content)

    def export_events_to_json(self, events: List[Dict]) -> str:
        return export_events_to_json(events)

    def import_events_from_json(self, content: str) -> List[Dict]:
        return import_events_from_json(content)

    def export_events_to_csv(self, events: List[Dict]) -> str:
        return export_events_to_csv(events)

    def import_events_from_csv(self, content: str) -> List[Dict]:
        return import_events_from_csv(content)

    def create_backup_data(
        self,
        user_id: str,
        user_email: str,
        events: List[Dict],
        categories: List[Dict]
    ) -> Dict:
        return create_backup_data(user_id, user_email, events, categories)

    def export_backup_to_json(self, backup_data: Dict) -> str:
        return export_backup_to_json(backup_data)

    def import_backup_from_json(self, content: str) -> Dict:
        return import_backup_from_json(content)
