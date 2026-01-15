"""
Base Agent Service
Template for creating agent microservices
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import os
from typing import Optional
from coordination.distributed_message_bus import DistributedMessageBus, RedisStateStore


class AgentService:
    """
    Base class for agent microservices.
    Each agent runs as an independent service communicating via RabbitMQ.
    """
    
    def __init__(self, agent_name: str, agent_class, port: int = 8000):
        self.app = FastAPI(
            title=f"{agent_name} Service",
            description=f"AETHER {agent_name} Microservice",
            version="1.0.0"
        )
        self.agent_name = agent_name
        self.agent_class = agent_class
        self.port = port
        
        # Get config from environment
        self.rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672")
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        
        # Initialize message bus and state store
        self.message_bus: Optional[DistributedMessageBus] = None
        self.state_store: Optional[RedisStateStore] = None
        
        # Initialize agent
        self.agent = None
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup routes
        self.setup_routes()
    
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.on_event("startup")
        async def startup():
            """Initialize connections and start agent"""
            print(f"\n🚀 Starting {self.agent_name} Service...")
            
            try:
                # Connect to message bus
                self.message_bus = DistributedMessageBus(self.rabbitmq_url)
                await self.message_bus.connect()
                
                # Connect to state store
                self.state_store = RedisStateStore(self.redis_url)
                
                # Initialize agent with distributed components
                self.agent = self.agent_class(
                    message_bus=self.message_bus,
                    state_store=self.state_store
                )
                
                # Start agent (setup subscriptions)
                if hasattr(self.agent, 'start'):
                    await self.agent.start()
                
                print(f"✓ {self.agent_name} Service ready on port {self.port}")
                
            except Exception as e:
                print(f"✗ Failed to start {self.agent_name}: {e}")
                raise
        
        @self.app.on_event("shutdown")
        async def shutdown():
            """Cleanup connections"""
            print(f"\n⏹ Stopping {self.agent_name} Service...")
            
            if self.agent and hasattr(self.agent, 'stop'):
                await self.agent.stop()
            
            if self.message_bus:
                await self.message_bus.disconnect()
            
            print(f"✓ {self.agent_name} Service stopped")
        
        @self.app.get("/health")
        async def health():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "agent": self.agent_name,
                "message_bus": "connected" if self.message_bus else "disconnected",
                "state_store": "connected" if self.state_store else "disconnected"
            }
        
        @self.app.get("/metrics")
        async def metrics():
            """Metrics endpoint for monitoring"""
            if not self.agent:
                raise HTTPException(status_code=503, detail="Agent not initialized")
            
            metrics_data = {
                "agent": self.agent_name,
                "messages_processed": getattr(self.agent, 'messages_processed', 0),
                "uptime_seconds": getattr(self.agent, 'uptime_seconds', 0),
            }
            
            return metrics_data
        
        @self.app.get("/status")
        async def status():
            """Detailed status endpoint"""
            if not self.agent:
                raise HTTPException(status_code=503, detail="Agent not initialized")
            
            return {
                "agent": self.agent_name,
                "status": "running",
                "agent_id": getattr(self.agent, 'agent_id', 'unknown'),
                "role": getattr(self.agent, 'role', 'unknown'),
                "subscriptions": list(self.message_bus.subscribers.keys()) if self.message_bus else []
            }
    
    def run(self, host: str = "0.0.0.0"):
        """Run the service"""
        import uvicorn
        uvicorn.run(self.app, host=host, port=self.port)


# Example usage for each agent type

class FactorAgentService(AgentService):
    """Factor Extraction Agent Service"""
    def __init__(self):
        from agents.factor_extraction_agent import FactorExtractionAgent
        super().__init__("FactorAgent", FactorExtractionAgent, port=8001)


class SupportingAgentService(AgentService):
    """Supporting Agent Service"""
    def __init__(self):
        from agents.supporting_agent import SupportingAgent
        super().__init__("SupportingAgent", SupportingAgent, port=8002)


class CriticAgentService(AgentService):
    """Critic Agent Service"""
    def __init__(self):
        from agents.critic_agent import CriticAgent
        super().__init__("CriticAgent", CriticAgent, port=8003)


class SynthesizerAgentService(AgentService):
    """Synthesizer Agent Service"""
    def __init__(self):
        from agents.synthesizer_agent import SynthesizerAgent
        super().__init__("SynthesizerAgent", SynthesizerAgent, port=8004)


class FinalDecisionAgentService(AgentService):
    """Final Decision Agent Service"""
    def __init__(self):
        from agents.final_decision_agent import FinalDecisionAgent
        super().__init__("FinalDecisionAgent", FinalDecisionAgent, port=8005)
