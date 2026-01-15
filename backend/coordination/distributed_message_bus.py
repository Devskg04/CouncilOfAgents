"""
Distributed Message Bus using RabbitMQ
Enables agent communication across distributed microservices
"""

import pika
import json
import asyncio
from typing import Callable, Dict, List, Optional
from datetime import datetime
import uuid
from enum import Enum


class MessageType(str, Enum):
    """Message types for agent communication"""
    FACTOR_DISCOVERED = "FACTOR_DISCOVERED"
    FACTOR_LIST = "FACTOR_LIST"
    SUPPORT_ARGUMENT = "SUPPORT_ARGUMENT"
    CRITIQUE = "CRITIQUE"
    REBUTTAL = "REBUTTAL"
    SYNTHESIS = "SYNTHESIS"
    FINAL_REPORT = "FINAL_REPORT"


class DistributedMessageBus:
    """
    Message bus using RabbitMQ for distributed agent communication.
    Replaces in-memory MessageBus for microservices architecture.
    """
    
    def __init__(self, rabbitmq_url: str):
        self.rabbitmq_url = rabbitmq_url
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None
        self.subscribers: Dict[str, List[Callable]] = {}
        self.exchange_name = "aether_events"
        self.session_id = str(uuid.uuid4())
        
    async def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            parameters = pika.URLParameters(self.rabbitmq_url)
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare exchange (topic for routing)
            self.channel.exchange_declare(
                exchange=self.exchange_name,
                exchange_type='topic',
                durable=True
            )
            
            print(f"✓ Connected to RabbitMQ: {self.exchange_name}")
        except Exception as e:
            print(f"✗ Failed to connect to RabbitMQ: {e}")
            raise
    
    async def disconnect(self):
        """Close connection to RabbitMQ"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            print("✓ Disconnected from RabbitMQ")
    
    async def publish(self, message_type: str, payload: Dict, correlation_id: Optional[str] = None):
        """
        Publish message to exchange
        
        Args:
            message_type: Type of message (routing key)
            payload: Message payload
            correlation_id: Session/request ID for tracking
        """
        if not self.channel:
            raise RuntimeError("Not connected to RabbitMQ. Call connect() first.")
        
        message = {
            "id": str(uuid.uuid4()),
            "type": message_type,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat(),
            "correlation_id": correlation_id or self.session_id
        }
        
        try:
            self.channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=message_type,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistent
                    content_type='application/json',
                    correlation_id=correlation_id or self.session_id
                )
            )
            print(f"→ Published: {message_type} (id: {message['id'][:8]}...)")
        except Exception as e:
            print(f"✗ Failed to publish message: {e}")
            raise
    
    async def subscribe(self, message_type: str, callback: Callable):
        """
        Subscribe to message type
        
        Args:
            message_type: Type of message to subscribe to
            callback: Async function to call when message received
        """
        if not self.channel:
            raise RuntimeError("Not connected to RabbitMQ. Call connect() first.")
        
        # Create queue for this subscriber (unique per agent instance)
        queue_name = f"{message_type}_{uuid.uuid4().hex[:8]}"
        self.channel.queue_declare(queue=queue_name, durable=True, auto_delete=True)
        
        # Bind queue to exchange with routing key
        self.channel.queue_bind(
            exchange=self.exchange_name,
            queue=queue_name,
            routing_key=message_type
        )
        
        # Register callback
        if message_type not in self.subscribers:
            self.subscribers[message_type] = []
        self.subscribers[message_type].append(callback)
        
        # Start consuming
        def on_message(ch, method, properties, body):
            try:
                message = json.loads(body)
                # Run callback in event loop
                asyncio.create_task(callback(message['payload']))
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                print(f"✗ Error processing message: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=on_message
        )
        
        print(f"✓ Subscribed to: {message_type}")
    
    def start_consuming(self):
        """Start consuming messages (blocking)"""
        if not self.channel:
            raise RuntimeError("Not connected to RabbitMQ. Call connect() first.")
        
        print("🎧 Starting message consumption...")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            print("\n⏹ Stopping message consumption...")
            self.channel.stop_consuming()
    
    async def get_message(self, message_type: str, timeout: float = 5.0) -> Optional[Dict]:
        """
        Get a single message of specified type (for request-response pattern)
        
        Args:
            message_type: Type of message to retrieve
            timeout: Timeout in seconds
            
        Returns:
            Message payload or None if timeout
        """
        if not self.channel:
            raise RuntimeError("Not connected to RabbitMQ. Call connect() first.")
        
        queue_name = f"{message_type}_temp_{uuid.uuid4().hex[:8]}"
        self.channel.queue_declare(queue=queue_name, durable=False, auto_delete=True)
        self.channel.queue_bind(
            exchange=self.exchange_name,
            queue=queue_name,
            routing_key=message_type
        )
        
        # Try to get message with timeout
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            method, properties, body = self.channel.basic_get(queue=queue_name, auto_ack=True)
            if method:
                message = json.loads(body)
                self.channel.queue_delete(queue=queue_name)
                return message['payload']
            await asyncio.sleep(0.1)
        
        self.channel.queue_delete(queue=queue_name)
        return None


class RedisStateStore:
    """
    Redis-based state store for distributed agents.
    Stores factors, claims, resolutions, etc.
    """
    
    def __init__(self, redis_url: str):
        import redis.asyncio as redis
        self.redis = redis.from_url(redis_url, decode_responses=True)
    
    async def set_factor(self, factor_id: str, factor_data: Dict, session_id: str):
        """Store factor data"""
        key = f"session:{session_id}:factor:{factor_id}"
        await self.redis.set(key, json.dumps(factor_data), ex=3600)  # 1 hour TTL
    
    async def get_factor(self, factor_id: str, session_id: str) -> Optional[Dict]:
        """Retrieve factor data"""
        key = f"session:{session_id}:factor:{factor_id}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None
    
    async def set_resolution(self, factor_id: str, resolution: str, session_id: str):
        """Store factor resolution"""
        key = f"session:{session_id}:resolution:{factor_id}"
        await self.redis.set(key, resolution, ex=3600)
    
    async def get_resolution(self, factor_id: str, session_id: str) -> Optional[str]:
        """Retrieve factor resolution"""
        key = f"session:{session_id}:resolution:{factor_id}"
        return await self.redis.get(key)
    
    async def get_all_factors(self, session_id: str) -> List[Dict]:
        """Get all factors for a session"""
        pattern = f"session:{session_id}:factor:*"
        keys = await self.redis.keys(pattern)
        factors = []
        for key in keys:
            data = await self.redis.get(key)
            if data:
                factors.append(json.loads(data))
        return factors
    
    async def clear_session(self, session_id: str):
        """Clear all data for a session"""
        pattern = f"session:{session_id}:*"
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
