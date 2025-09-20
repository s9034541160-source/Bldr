# ЭТОТ ФАЙЛ УДАЛЕН - используйте C:\Bldr\core\websocket_manager.py
WebSocket Server для SuperBuilder Tools
Обеспечивает real-time уведомления о статусе задач и системных событиях.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set, Any, Optional
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Менеджер WebSocket соединений"""
    
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # connection_id -> set of subscription types
        self.job_subscriptions: Dict[str, Set[str]] = {}  # job_id -> set of connection_ids
        
    async def connect(self, websocket: WebSocket) -> str:
        """Принять новое WebSocket соединение"""
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        self.connections[connection_id] = websocket
        self.subscriptions[connection_id] = set()
        
        logger.info(f"WebSocket connection established: {connection_id}")
        
        # Send welcome message
        await self.send_personal_message(connection_id, {
            'type': 'connection_established',
            'connection_id': connection_id,
            'timestamp': datetime.now().isoformat(),
            'message': 'WebSocket connection established'
        })
        
        return connection_id
    
    def disconnect(self, connection_id: str):
        """Закрыть WebSocket соединение"""
        if connection_id in self.connections:
            websocket = self.connections[connection_id]
            if websocket.application_state != WebSocketState.DISCONNECTED:
                try:
                    asyncio.create_task(websocket.close())
                except:
                    pass
                    
            del self.connections[connection_id]
            
        if connection_id in self.subscriptions:
            del self.subscriptions[connection_id]
            
        # Remove from job subscriptions
        for job_id, subscriber_ids in self.job_subscriptions.items():
            subscriber_ids.discard(connection_id)
            
        logger.info(f"WebSocket connection closed: {connection_id}")
    
    async def send_personal_message(self, connection_id: str, message: Dict[str, Any]):
        """Отправить сообщение конкретному подключению"""
        if connection_id in self.connections:
            websocket = self.connections[connection_id]
            try:
                if websocket.application_state == WebSocketState.CONNECTED:
                    await websocket.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                self.disconnect(connection_id)
    
    async def broadcast(self, message: Dict[str, Any], subscription_type: str = None):
        """Отправить широковещательное сообщение"""
        if not self.connections:
            return
            
        message['broadcast_time'] = datetime.now().isoformat()
        
        # If subscription type is specified, send only to subscribed connections
        if subscription_type:
            target_connections = [
                conn_id for conn_id, subs in self.subscriptions.items() 
                if subscription_type in subs
            ]
        else:
            target_connections = list(self.connections.keys())
        
        # Send to all target connections
        tasks = []
        for connection_id in target_connections:
            if connection_id in self.connections:
                tasks.append(self.send_personal_message(connection_id, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def notify_job_update(self, job_id: str, job_data: Dict[str, Any]):
        """Уведомить о обновлении задачи"""
        message = {
            'type': 'job_update',
            'job_id': job_id,
            'data': job_data,
            'timestamp': datetime.now().isoformat()
        }
        
        # Send to subscribers of this specific job
        if job_id in self.job_subscriptions:
            tasks = []
            for connection_id in self.job_subscriptions[job_id]:
                if connection_id in self.connections:
                    tasks.append(self.send_personal_message(connection_id, message))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        
        # Also broadcast to general job subscribers
        await self.broadcast(message, 'jobs')
    
    async def notify_system_status(self, status_data: Dict[str, Any]):
        """Уведомить о статусе системы"""
        message = {
            'type': 'system_status',
            'data': status_data,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.broadcast(message, 'system')
    
    def subscribe_to_job(self, connection_id: str, job_id: str):
        """Подписаться на обновления конкретной задачи"""
        if job_id not in self.job_subscriptions:
            self.job_subscriptions[job_id] = set()
        
        self.job_subscriptions[job_id].add(connection_id)
        logger.info(f"Connection {connection_id} subscribed to job {job_id}")
    
    def unsubscribe_from_job(self, connection_id: str, job_id: str):
        """Отписаться от обновлений задачи"""
        if job_id in self.job_subscriptions:
            self.job_subscriptions[job_id].discard(connection_id)
            
            # Clean up empty subscriptions
            if not self.job_subscriptions[job_id]:
                del self.job_subscriptions[job_id]
        
        logger.info(f"Connection {connection_id} unsubscribed from job {job_id}")
    
    def add_subscription(self, connection_id: str, subscription_type: str):
        """Добавить подписку на тип событий"""
        if connection_id in self.subscriptions:
            self.subscriptions[connection_id].add(subscription_type)
            logger.info(f"Connection {connection_id} subscribed to {subscription_type}")
    
    def remove_subscription(self, connection_id: str, subscription_type: str):
        """Удалить подписку на тип событий"""
        if connection_id in self.subscriptions:
            self.subscriptions[connection_id].discard(subscription_type)
            logger.info(f"Connection {connection_id} unsubscribed from {subscription_type}")
    
    def get_connection_count(self) -> int:
        """Получить количество активных соединений"""
        return len(self.connections)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику WebSocket сервера"""
        return {
            'active_connections': len(self.connections),
            'total_subscriptions': sum(len(subs) for subs in self.subscriptions.values()),
            'job_subscriptions': len(self.job_subscriptions),
            'subscription_types': {
                sub_type: sum(1 for subs in self.subscriptions.values() if sub_type in subs)
                for sub_type in ['jobs', 'system', 'notifications']
            }
        }

# Global WebSocket manager instance
manager = WebSocketManager()

async def websocket_endpoint(websocket: WebSocket, path: str = ""):
    """WebSocket endpoint handler"""
    connection_id = None
    
    try:
        connection_id = await manager.connect(websocket)
        
        # Handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                await handle_websocket_message(connection_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket client {connection_id} disconnected normally")
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message from {connection_id}: {e}")
                await manager.send_personal_message(connection_id, {
                    'type': 'error',
                    'message': f'Error processing message: {str(e)}',
                    'timestamp': datetime.now().isoformat()
                })
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        if connection_id:
            manager.disconnect(connection_id)

async def handle_websocket_message(connection_id: str, message: Dict[str, Any]):
    """Обработать входящее WebSocket сообщение"""
    message_type = message.get('type')
    
    if message_type == 'subscribe':
        # Subscribe to event types or specific jobs
        subscription_type = message.get('subscription_type')
        job_id = message.get('job_id')
        
        if job_id:
            manager.subscribe_to_job(connection_id, job_id)
            await manager.send_personal_message(connection_id, {
                'type': 'subscription_confirmed',
                'job_id': job_id,
                'message': f'Subscribed to job {job_id}',
                'timestamp': datetime.now().isoformat()
            })
        elif subscription_type:
            manager.add_subscription(connection_id, subscription_type)
            await manager.send_personal_message(connection_id, {
                'type': 'subscription_confirmed',
                'subscription_type': subscription_type,
                'message': f'Subscribed to {subscription_type}',
                'timestamp': datetime.now().isoformat()
            })
    
    elif message_type == 'unsubscribe':
        subscription_type = message.get('subscription_type')
        job_id = message.get('job_id')
        
        if job_id:
            manager.unsubscribe_from_job(connection_id, job_id)
        elif subscription_type:
            manager.remove_subscription(connection_id, subscription_type)
    
    elif message_type == 'ping':
        # Respond to ping with pong
        await manager.send_personal_message(connection_id, {
            'type': 'pong',
            'timestamp': datetime.now().isoformat()
        })
    
    elif message_type == 'get_statistics':
        # Send WebSocket statistics
        stats = manager.get_statistics()
        await manager.send_personal_message(connection_id, {
            'type': 'statistics',
            'data': stats,
            'timestamp': datetime.now().isoformat()
        })
    
    else:
        await manager.send_personal_message(connection_id, {
            'type': 'error',
            'message': f'Unknown message type: {message_type}',
            'timestamp': datetime.now().isoformat()
        })

# Utility functions for integration with tools API

async def notify_job_progress(job_id: str, status: str, progress: int, message: str, 
                            result: Any = None, error: str = None):
    """Уведомить о прогрессе задачи через WebSocket"""
    job_data = {
        'status': status,
        'progress': progress,
        'message': message,
        'result': result,
        'error': error,
        'updated_at': datetime.now().isoformat()
    }
    
    await manager.notify_job_update(job_id, job_data)

async def notify_new_job(job_id: str, tool_type: str, estimated_time: int = None):
    """Уведомить о новой задаче"""
    await manager.broadcast({
        'type': 'new_job',
        'job_id': job_id,
        'tool_type': tool_type,
        'estimated_time': estimated_time,
        'timestamp': datetime.now().isoformat()
    }, 'jobs')

async def notify_job_completed(job_id: str, tool_type: str, success: bool, 
                              execution_time: float = None):
    """Уведомить о завершении задачи"""
    await manager.broadcast({
        'type': 'job_completed',
        'job_id': job_id,
        'tool_type': tool_type,
        'success': success,
        'execution_time': execution_time,
        'timestamp': datetime.now().isoformat()
    }, 'jobs')

async def send_system_notification(message: str, level: str = 'info', details: Any = None):
    """Отправить системное уведомление"""
    await manager.broadcast({
        'type': 'notification',
        'level': level,  # info, warning, error, success
        'message': message,
        'details': details,
        'timestamp': datetime.now().isoformat()
    }, 'notifications')

# Background task to send periodic system updates
async def periodic_system_updates():
    """Периодически отправлять обновления статуса системы"""
    while True:
        try:
            # Send system statistics every 30 seconds
            await asyncio.sleep(30)
            
            if manager.get_connection_count() > 0:
                from tools_api import active_jobs, completed_jobs  # Import when needed
                
                system_stats = {
                    'active_jobs': len(active_jobs),
                    'completed_jobs': len(completed_jobs),
                    'websocket_connections': manager.get_connection_count(),
                    'uptime': 'N/A',  # Add real uptime calculation if needed
                    'last_update': datetime.now().isoformat()
                }
                
                await manager.notify_system_status(system_stats)
                
        except Exception as e:
            logger.error(f"Error in periodic system updates: {e}")
            await asyncio.sleep(60)  # Wait longer on error

# Export the main components
__all__ = [
    'manager', 
    'websocket_endpoint',
    'notify_job_progress',
    'notify_new_job', 
    'notify_job_completed',
    'send_system_notification',
    'periodic_system_updates'
]