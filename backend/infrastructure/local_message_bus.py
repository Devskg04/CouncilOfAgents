"""
Local Message Bus - Free, Zero-Cost Async Pub/Sub
Replaces RabbitMQ/Kafka with in-memory message passing + SQLite persistence
"""

import asyncio
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Callable, Any, Optional
from enum import Enum
import uuid
from pathlib import Path
import aiosqlite


class MessageType(str, Enum):
    """Message types for agent communication"""
    FACTOR_DISCOVERED = "FACTOR_DISCOVERED"
    SUPPORT_ARGUMENT = "SUPPORT_ARGUMENT"
    CRITIQUE = "CRITIQUE"
    REBUTTAL = "REBUTTAL"
    SYNTHESIS_NOTE = "SYNTHESIS_NOTE"
    FINAL_REPORT = "FINAL_REPORT"
    SESSION_START = "SESSION_START"
    SESSION_END = "SESSION_END"


class Message:
    """Message container with metadata"""
    
    def __init__(
        self,
        message_type: MessageType,
        payload: Dict[str, Any],
        session_id: str,
        correlation_id: Optional[str] = None,
        sender: Optional[str] = None
    ):
        self.id = str(uuid.uuid4())
        self.message_type = message_type
        self.payload = payload
        self.session_id = session_id
        self.correlation_id = correlation_id or self.id
        self.sender = sender
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "message_type": self.message_type.value,
            "payload": self.payload,
            "session_id": self.session_id,
            "correlation_id": self.correlation_id,
            "sender": self.sender,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        msg = cls(
            message_type=MessageType(data["message_type"]),
            payload=data["payload"],
            session_id=data["session_id"],
            correlation_id=data.get("correlation_id"),
            sender=data.get("sender")
        )
        msg.id = data["id"]
        msg.timestamp = data["timestamp"]
        return msg


class LocalMessageBus:
    """
    Free, zero-cost async message bus
    - In-memory pub/sub for low latency
    - SQLite persistence for reliability
    - No external dependencies
    """
    
    def __init__(self, db_path: str = "data/message_bus.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # In-memory subscribers: {message_type: [callback_functions]}
        self.subscribers: Dict[MessageType, List[Callable]] = {}
        
        # Message queues for async delivery
        self.message_queue: asyncio.Queue = asyncio.Queue()
        
        # Session tracking
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Background task for message processing
        self.processor_task: Optional[asyncio.Task] = None
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database for message persistence"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                message_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                session_id TEXT NOT NULL,
                correlation_id TEXT,
                sender TEXT,
                timestamp TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_id ON messages(session_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_message_type ON messages(message_type)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_correlation_id ON messages(correlation_id)
        """)
        
        conn.commit()
        conn.close()
    
    async def start(self):
        """Start the message bus processor"""
        if self.processor_task is None:
            self.processor_task = asyncio.create_task(self._process_messages())
    
    async def stop(self):
        """Stop the message bus processor"""
        if self.processor_task:
            self.processor_task.cancel()
            try:
                await self.processor_task
            except asyncio.CancelledError:
                pass
    
    async def publish(self, message: Message):
        """
        Publish a message to all subscribers
        - Adds to in-memory queue for immediate delivery
        - Persists to SQLite for reliability
        """
        # Persist to SQLite
        await self._persist_message(message)
        
        # Add to in-memory queue for async delivery
        await self.message_queue.put(message)
    
    async def _persist_message(self, message: Message):
        """Persist message to SQLite"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute(
                """
                INSERT INTO messages (id, message_type, payload, session_id, correlation_id, sender, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message.id,
                    message.message_type.value,
                    json.dumps(message.payload),
                    message.session_id,
                    message.correlation_id,
                    message.sender,
                    message.timestamp
                )
            )
            await db.commit()
    
    async def _process_messages(self):
        """Background task to process messages from queue"""
        while True:
            try:
                message = await self.message_queue.get()
                await self._deliver_message(message)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error processing message: {e}")
    
    async def _deliver_message(self, message: Message):
        """Deliver message to all subscribers"""
        subscribers = self.subscribers.get(message.message_type, [])
        
        # Fan-out to all subscribers concurrently
        tasks = [subscriber(message) for subscriber in subscribers]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def subscribe(self, message_type: MessageType, callback: Callable):
        """
        Subscribe to a message type
        Callback signature: async def callback(message: Message)
        """
        if message_type not in self.subscribers:
            self.subscribers[message_type] = []
        
        self.subscribers[message_type].append(callback)
    
    def unsubscribe(self, message_type: MessageType, callback: Callable):
        """Unsubscribe from a message type"""
        if message_type in self.subscribers:
            self.subscribers[message_type].remove(callback)
    
    async def get_session_messages(self, session_id: str) -> List[Message]:
        """Retrieve all messages for a session from SQLite"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            async with db.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at",
                (session_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                
                messages = []
                for row in rows:
                    message_dict = {
                        "id": row[0],
                        "message_type": row[1],
                        "payload": json.loads(row[2]),
                        "session_id": row[3],
                        "correlation_id": row[4],
                        "sender": row[5],
                        "timestamp": row[6]
                    }
                    messages.append(Message.from_dict(message_dict))
                
                return messages
    
    async def get_messages_by_type(
        self,
        session_id: str,
        message_type: MessageType
    ) -> List[Message]:
        """Retrieve messages of a specific type for a session"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            async with db.execute(
                "SELECT * FROM messages WHERE session_id = ? AND message_type = ? ORDER BY created_at",
                (session_id, message_type.value)
            ) as cursor:
                rows = await cursor.fetchall()
                
                messages = []
                for row in rows:
                    message_dict = {
                        "id": row[0],
                        "message_type": row[1],
                        "payload": json.loads(row[2]),
                        "session_id": row[3],
                        "correlation_id": row[4],
                        "sender": row[5],
                        "timestamp": row[6]
                    }
                    messages.append(Message.from_dict(message_dict))
                
                return messages
    
    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new session"""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        self.active_sessions[session_id] = {
            "created_at": datetime.utcnow().isoformat(),
            "status": "active"
        }
        
        return session_id
    
    def end_session(self, session_id: str):
        """End a session"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["status"] = "completed"
            self.active_sessions[session_id]["ended_at"] = datetime.utcnow().isoformat()


# Global singleton instance
_message_bus: Optional[LocalMessageBus] = None


def get_message_bus() -> LocalMessageBus:
    """Get or create the global message bus instance"""
    global _message_bus
    if _message_bus is None:
        _message_bus = LocalMessageBus()
    return _message_bus
