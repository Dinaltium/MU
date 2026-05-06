"""
app/api/websocket.py
WebSocket manager for real-time notifications and SOS alerts.
"""
from __future__ import annotations

import logging
from typing import Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from app.core.security import decode_token

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # user_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected to WebSocket")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected from WebSocket")

    async def send_to_user(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)

    async def broadcast_sos(self, doctor_user_ids: list[str], sos_data: dict):
        """Broadcasts SOS alert only to assigned doctors."""
        for doctor_id in doctor_user_ids:
            if doctor_id in self.active_connections:
                await self.active_connections[doctor_id].send_json({
                    "type": "sos_alert",
                    "data": sos_data
                })

manager = ConnectionManager()
router = APIRouter()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    token: str = Query(...)
):
    try:
        # Validate token
        payload = decode_token(token)
        if payload.get("sub") != user_id:
            await websocket.close(code=1008) # Policy Violation
            return

        await manager.connect(user_id, websocket)
        
        while True:
            # Keep connection alive and listen for any client messages if needed
            data = await websocket.receive_text()
            # Handle incoming ping or other messages
            
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(user_id)
        await websocket.close()
