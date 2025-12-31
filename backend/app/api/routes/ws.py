import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.schemas.session import AlertsResponse
from app.services.sessions.manager import session_manager

router = APIRouter()


@router.websocket("/ws/sessions/{session_id}")
async def session_events(websocket: WebSocket, session_id: str) -> None:
    await websocket.accept()
    last_alert_count = 0
    last_status_count = 0
    try:
        while True:
            await asyncio.sleep(1)
            status_events = await session_manager.status_events(session_id)
            if len(status_events) > last_status_count:
                for event in status_events[last_status_count:]:
                    await websocket.send_json({"type": "status", "payload": event.model_dump()})
                last_status_count = len(status_events)

            alerts: AlertsResponse = await session_manager.get_alerts(session_id)
            if len(alerts.alerts) > last_alert_count:
                for alert in alerts.alerts[last_alert_count:]:
                    await websocket.send_json({"type": "alert", "payload": alert.model_dump()})
                last_alert_count = len(alerts.alerts)
    except WebSocketDisconnect:
        return
