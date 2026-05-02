from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import suppress

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []
        self.sse_connections: dict[int, asyncio.Queue[dict]] = {}
        self._next_sse_id = 0

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_json(self, websocket: WebSocket, message: dict) -> None:
        await websocket.send_json(message)

    def connect_sse(self) -> tuple[int, asyncio.Queue[dict]]:
        self._next_sse_id += 1
        connection_id = self._next_sse_id
        queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=64)
        self.sse_connections[connection_id] = queue
        return connection_id, queue

    def disconnect_sse(self, connection_id: int) -> None:
        self.sse_connections.pop(connection_id, None)

    async def iter_sse(self, connection_id: int) -> AsyncIterator[dict]:
        queue = self.sse_connections[connection_id]
        try:
            while True:
                message = await queue.get()
                yield message
        finally:
            self.disconnect_sse(connection_id)

    async def broadcast(self, message: dict) -> None:
        stale_connections: list[WebSocket] = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                stale_connections.append(connection)

        for connection in stale_connections:
            self.disconnect(connection)

        stale_sse: list[int] = []
        for connection_id, queue in list(self.sse_connections.items()):
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                with suppress(Exception):
                    _ = queue.get_nowait()
                try:
                    queue.put_nowait(message)
                except Exception:
                    stale_sse.append(connection_id)
            except Exception:
                stale_sse.append(connection_id)

        for connection_id in stale_sse:
            self.disconnect_sse(connection_id)


websocket_manager = ConnectionManager()
