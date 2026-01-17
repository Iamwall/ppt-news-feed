"""WebSocket endpoint for real-time Live Pulse updates."""
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.live_pulse_service import live_pulse_notifier


logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for Live Pulse.

    Handles connection lifecycle, domain-based subscriptions,
    and message broadcasting.
    """

    def __init__(self):
        """Initialize connection manager."""
        # domain_id -> List[WebSocket]
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # WebSocket -> domain_id
        self.connection_domains: Dict[WebSocket, str] = {}
        # Global connections (no domain filter)
        self.global_connections: List[WebSocket] = []

    async def connect(
        self,
        websocket: WebSocket,
        domain_id: Optional[str] = None
    ):
        """Accept a new WebSocket connection.

        Args:
            websocket: The WebSocket connection
            domain_id: Domain to subscribe to (None for all)
        """
        await websocket.accept()

        if domain_id:
            if domain_id not in self.active_connections:
                self.active_connections[domain_id] = []
            self.active_connections[domain_id].append(websocket)
            self.connection_domains[websocket] = domain_id
            logger.info(f"WebSocket connected to domain: {domain_id}")
        else:
            self.global_connections.append(websocket)
            logger.info("WebSocket connected (global)")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        # Remove from domain-specific list
        if websocket in self.connection_domains:
            domain_id = self.connection_domains[websocket]
            if domain_id in self.active_connections:
                self.active_connections[domain_id] = [
                    ws for ws in self.active_connections[domain_id]
                    if ws != websocket
                ]
            del self.connection_domains[websocket]
            logger.info(f"WebSocket disconnected from domain: {domain_id}")

        # Remove from global list
        if websocket in self.global_connections:
            self.global_connections.remove(websocket)
            logger.info("WebSocket disconnected (global)")

    async def send_personal_message(
        self,
        message: dict,
        websocket: WebSocket
    ):
        """Send a message to a specific connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.disconnect(websocket)

    async def broadcast_to_domain(
        self,
        domain_id: str,
        message: dict
    ):
        """Broadcast a message to all connections subscribed to a domain."""
        connections = self.active_connections.get(domain_id, [])
        disconnected = []

        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to domain {domain_id}: {e}")
                disconnected.append(connection)

        # Clean up disconnected
        for conn in disconnected:
            self.disconnect(conn)

    async def broadcast_global(self, message: dict):
        """Broadcast a message to all global connections."""
        disconnected = []

        for connection in self.global_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting globally: {e}")
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)

    async def broadcast(
        self,
        message: dict,
        domain_id: Optional[str] = None
    ):
        """Broadcast a message to appropriate connections.

        If domain_id is provided, sends to domain subscribers AND global.
        If domain_id is None, sends only to global subscribers.
        """
        if domain_id:
            await self.broadcast_to_domain(domain_id, message)

        await self.broadcast_global(message)

    def get_connection_count(self, domain_id: Optional[str] = None) -> int:
        """Get number of active connections."""
        if domain_id:
            return len(self.active_connections.get(domain_id, []))
        return len(self.global_connections) + sum(
            len(conns) for conns in self.active_connections.values()
        )


# Global connection manager
manager = ConnectionManager()


# Register with notifier for automatic broadcasts
async def _broadcast_callback(message: dict):
    """Callback for live_pulse_notifier to broadcast messages."""
    await manager.broadcast_global(message)


live_pulse_notifier.subscribe(_broadcast_callback)


@router.websocket("/ws/pulse")
async def websocket_pulse_global(websocket: WebSocket):
    """WebSocket endpoint for global Live Pulse updates.

    Receives all new items regardless of domain.
    """
    await manager.connect(websocket, domain_id=None)

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to Live Pulse (global)",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # Keep connection alive
        while True:
            # Wait for any message from client (ping/pong, commands, etc.)
            data = await websocket.receive_text()

            # Handle ping
            if data == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.websocket("/ws/pulse/{domain_id}")
async def websocket_pulse_domain(
    websocket: WebSocket,
    domain_id: str
):
    """WebSocket endpoint for domain-specific Live Pulse updates.

    Args:
        domain_id: Domain to subscribe to (e.g., "tech", "science")
    """
    await manager.connect(websocket, domain_id=domain_id)

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "domain": domain_id,
            "message": f"Connected to Live Pulse ({domain_id})",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # Keep connection alive
        while True:
            data = await websocket.receive_text()

            if data == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "domain": domain_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error for domain {domain_id}: {e}")
        manager.disconnect(websocket)


@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket connection status."""
    domain_counts = {
        domain: len(conns)
        for domain, conns in manager.active_connections.items()
    }

    return {
        "total_connections": manager.get_connection_count(),
        "global_connections": len(manager.global_connections),
        "domain_connections": domain_counts,
    }


async def broadcast_new_item(paper_data: dict, domain_id: Optional[str] = None):
    """Utility function to broadcast a new item to connected clients.

    Called by fetch service when new papers are added.
    """
    message = {
        "type": "new_item",
        "data": paper_data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await manager.broadcast(message, domain_id)


async def broadcast_breaking_news(paper_data: dict, domain_id: Optional[str] = None):
    """Utility function to broadcast breaking news alert.

    Called when a paper is flagged as breaking news.
    """
    message = {
        "type": "breaking",
        "data": paper_data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await manager.broadcast(message, domain_id)
