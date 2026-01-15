"""
Base Agent Service - FastAPI Template for All Agents
Provides common functionality for agent microservices
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
from datetime import datetime
import time

from infrastructure.local_message_bus import get_message_bus, Message, MessageType
from infrastructure.state_manager import get_state_manager
from infrastructure.logger import setup_logger, log_with_context


class BaseAgentService:
    """
    Base class for all agent microservices
    Provides:
    - FastAPI app setup
    - Message bus integration
    - State management
    - Health checks
    - Structured logging
    """
    
    def __init__(self, agent_name: str, agent_type: str):
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.app = FastAPI(title=f"{agent_name} Service")
        
        # Infrastructure
        self.message_bus = get_message_bus()
        self.state_manager = get_state_manager()
        self.logger = setup_logger(agent_name)
        
        # Metrics
        self.start_time = time.time()
        self.messages_processed = 0
        self.processing_times = []
        
        # Setup routes
        self._setup_routes()
        
        # Setup message subscriptions (override in subclass)
        self._setup_subscriptions()
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/health")
        async def health():
            """Health check endpoint"""
            uptime = time.time() - self.start_time
            return {
                "status": "healthy",
                "agent": self.agent_name,
                "type": self.agent_type,
                "uptime_seconds": int(uptime),
                "message_bus": "connected",
                "state_manager": "connected"
            }
        
        @self.app.get("/metrics")
        async def metrics():
            """Optional metrics endpoint"""
            avg_time = (
                sum(self.processing_times) / len(self.processing_times)
                if self.processing_times else 0
            )
            
            return {
                "agent": self.agent_name,
                "messages_processed": self.messages_processed,
                "avg_processing_time_ms": round(avg_time * 1000, 2),
                "uptime_seconds": int(time.time() - self.start_time)
            }
        
        @self.app.on_event("startup")
        async def startup():
            """Startup event"""
            await self.message_bus.start()
            log_with_context(
                self.logger,
                "info",
                f"{self.agent_name} service started",
                agent=self.agent_name
            )
        
        @self.app.on_event("shutdown")
        async def shutdown():
            """Shutdown event"""
            await self.message_bus.stop()
            log_with_context(
                self.logger,
                "info",
                f"{self.agent_name} service stopped",
                agent=self.agent_name
            )
    
    def _setup_subscriptions(self):
        """
        Setup message subscriptions
        Override in subclass to subscribe to specific message types
        """
        pass
    
    async def process_message(self, message: Message):
        """
        Process a message
        Override in subclass with specific logic
        """
        raise NotImplementedError("Subclass must implement process_message")
    
    async def _track_processing(self, message: Message):
        """Track message processing with metrics"""
        start_time = time.time()
        
        try:
            await self.process_message(message)
            self.messages_processed += 1
            
            processing_time = time.time() - start_time
            self.processing_times.append(processing_time)
            
            # Keep only last 100 processing times
            if len(self.processing_times) > 100:
                self.processing_times.pop(0)
            
            log_with_context(
                self.logger,
                "info",
                f"Processed message {message.message_type}",
                agent=self.agent_name,
                session_id=message.session_id,
                data={"processing_time_ms": round(processing_time * 1000, 2)}
            )
        
        except Exception as e:
            log_with_context(
                self.logger,
                "error",
                f"Error processing message: {str(e)}",
                agent=self.agent_name,
                session_id=message.session_id,
                data={"error": str(e)}
            )
    
    def subscribe(self, message_type: MessageType):
        """Subscribe to a message type"""
        self.message_bus.subscribe(message_type, self._track_processing)
    
    async def publish(self, message: Message):
        """Publish a message"""
        await self.message_bus.publish(message)
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the service"""
        import uvicorn
        uvicorn.run(self.app, host=host, port=port)


# Example: Factor Agent Service Implementation
class FactorAgentService(BaseAgentService):
    """Factor extraction agent service"""
    
    def __init__(self):
        super().__init__("FactorAgent", "factor")
    
    def _setup_subscriptions(self):
        """Subscribe to session start messages"""
        self.subscribe(MessageType.SESSION_START)
    
    async def process_message(self, message: Message):
        """Process session start and extract factors"""
        if message.message_type == MessageType.SESSION_START:
            session_id = message.session_id
            problem_statement = message.payload.get("problem_statement", "")
            
            # TODO: Call actual factor extraction logic
            # For now, simulate factor extraction
            factors = [
                {"id": 1, "name": "Factor 1", "description": "First factor"},
                {"id": 2, "name": "Factor 2", "description": "Second factor"}
            ]
            
            # Store factors in state
            for factor in factors:
                await self.state_manager.store_factor(
                    session_id=session_id,
                    factor_id=factor["id"],
                    name=factor["name"],
                    description=factor["description"]
                )
            
            # Publish factor discovered messages
            for factor in factors:
                factor_message = Message(
                    message_type=MessageType.FACTOR_DISCOVERED,
                    payload={"factor": factor},
                    session_id=session_id,
                    sender=self.agent_name
                )
                await self.publish(factor_message)
