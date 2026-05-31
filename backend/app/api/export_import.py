from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Path
from fastapi.responses import Response, JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.event_service import EventService
from app.services.category_service import CategoryService
from app.services.export_import_service import ExportImportService
from typing import Optional


router = APIRouter(prefix="/api/export-import", tags=["export-import"])


@router.get("/events")
async def export_events(
    format: str = Query(..., regex="^(ical|json|csv)$"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    event_service = EventService(db)
    events = event_service.get_user_events(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        category_id=category_id
    )

    export_service = ExportImportService()

    if format == "ical":
        content = export_service.export_events_to_ical([e.to_dict() for e in events])
        return Response(
            content=content,
            media_type="text/calendar",
            headers={"Content-Disposition": "attachment; filename=events.ics"}
        )

    elif format == "json":
        content = export_service.export_events_to_json([e.to_dict() for e in events])
        return JSONResponse(content={"data": content})

    elif format == "csv":
        content = export_service.export_events_to_csv([e.to_dict() for e in events])
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=events.csv"}
        )


@router.post("/events")
async def import_events(
    file: UploadFile = File(...),
    format: str = Query(..., regex="^(ical|json|csv)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    content = await file.read()

    try:
        content_str = content.decode('utf-8')
    except UnicodeDecodeError:
        content_str = content.decode('gbk')

    export_service = ExportImportService()

    try:
        if format == "ical":
            events = export_service.import_events_from_ical(content_str)
        elif format == "json":
            events = export_service.import_events_from_json(content_str)
        elif format == "csv":
            events = export_service.import_events_from_csv(content_str)
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")

        event_service = EventService(db)
        created_events = []

        for event_data in events:
            event_data['user_id'] = current_user.id
            event = event_service.create_event(event_data)
            created_events.append(event)

        return {
            "message": f"Successfully imported {len(created_events)} events",
            "imported_count": len(created_events),
            "events": [e.to_dict() for e in created_events]
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")


@router.get("/backup")
async def export_backup(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    event_service = EventService(db)
    category_service = CategoryService(db)

    events = event_service.get_user_events(user_id=current_user.id)
    categories = category_service.get_user_categories(user_id=current_user.id)

    export_service = ExportImportService()
    backup_data = export_service.create_backup_data(
        user_id=current_user.id,
        user_email=current_user.email,
        events=[e.to_dict() for e in events],
        categories=[c.to_dict() for c in categories]
    )

    content = export_service.export_backup_to_json(backup_data)

    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=vocal-calendar-backup-{current_user.id}.json"
        }
    )


@router.post("/backup")
async def import_backup(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    content = await file.read()

    try:
        content_str = content.decode('utf-8')
    except UnicodeDecodeError:
        content_str = content.decode('gbk')

    export_service = ExportImportService()

    try:
        backup_data = export_service.import_backup_from_json(content_str)

        event_service = EventService(db)
        category_service = CategoryService(db)

        imported_categories = 0
        imported_events = 0

        if 'data' in backup_data and 'categories' in backup_data['data']:
            for category_data in backup_data['data']['categories']:
                category_data['user_id'] = current_user.id
                try:
                    category_service.create_category(category_data)
                    imported_categories += 1
                except Exception:
                    pass

        if 'data' in backup_data and 'events' in backup_data['data']:
            for event_data in backup_data['data']['events']:
                event_data['user_id'] = current_user.id
                try:
                    event_service.create_event(event_data)
                    imported_events += 1
                except Exception:
                    pass

        return {
            "message": "Backup restored successfully",
            "imported_categories": imported_categories,
            "imported_events": imported_events,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Backup restore failed: {str(e)}")


@router.get("/template/{format}")
async def download_template(
    format: str = Path(..., regex="^(json|csv)$")
):
    export_service = ExportImportService()

    if format == "json":
        template = export_service.export_events_to_json([
            {
                "title": "示例事件",
                "description": "这是一个示例事件",
                "start_time": "2026-06-01T10:00:00",
                "end_time": "2026-06-01T11:00:00",
                "is_all_day": False,
                "location": "办公室",
                "priority": 2,
            }
        ])
        return JSONResponse(content={"data": template})

    elif format == "csv":
        template = export_service.export_events_to_csv([
            {
                "title": "示例事件",
                "description": "这是一个示例事件",
                "start_time": "2026-06-01T10:00:00",
                "end_time": "2026-06-01T11:00:00",
                "is_all_day": False,
                "location": "办公室",
                "priority": 2,
            }
        ])
        return Response(
            content=template,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=events-template.csv"}
        )
