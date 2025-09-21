import asyncio
import logging
from fastapi import WebSocket
from typing import List

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connection accepted. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket connection closed. Active connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message to websocket: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return
            
        # Create a copy of the list to avoid modification during iteration
        connections = list(self.active_connections)
        
        # Send to all connections concurrently
        tasks = []
        disconnected = []
        
        for connection in connections:
            try:
                tasks.append(connection.send_text(message))
            except Exception as e:
                logger.error(f"Error preparing message for websocket: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
        
        # Execute all send operations concurrently
        if tasks:
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")

# Global instance
manager = ConnectionManager()