from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import asyncio
import json
import structlog
from typing import List
from .templates import DASHBOARD_HTML
from ..infra.bus import bus

logger = structlog.get_logger()

app = FastAPI(title="NvsN V8 Dashboard")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                pass

manager = ConnectionManager()

@app.get("/")
async def get():
    return HTMLResponse(DASHBOARD_HTML)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Bridge MessageBus to WebSockets
async def stream_events_to_dashboard():
    # Subscribe to log events
    # In real impl, we'd tap into specific queues.
    # For demo, we simulate a stream or tap into the 'tasks' queue sidecar
    logger.info("Dashboard Stream Started")
    while True:
        # Mock event sourcing for demo visualization
        # Real impl would consume from Redis Pub/Sub
        await asyncio.sleep(1)
