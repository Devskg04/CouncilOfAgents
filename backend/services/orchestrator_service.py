"""
Orchestrator Service - Main Coordinator
Handles incoming requests and coordinates agent workflow
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.base_agent_service import BaseAgentService
from infrastructure.local_message_bus import Message, MessageType
from infrastructure.state_manager import get_state_manager


class AnalysisRequest(BaseModel):
    problem_statement: str
    session_id: Optional[str] = None


class OrchestratorService(BaseAgentService):
    """Main orchestrator service that coordinates the agent workflow"""
    
    def __init__(self):
        super().__init__("Orchestrator", "orchestrator")
        self.state_manager = get_state_manager()
        
        # Add custom routes
        self._setup_custom_routes()
    
    def _setup_custom_routes(self):
        """Setup orchestrator-specific routes"""
        
        @self.app.post("/analyze")
        async def analyze(request: AnalysisRequest):
            """Start a new analysis session"""
            try:
                # Create session
                session_id = request.session_id or self.message_bus.create_session()
                
                await self.state_manager.create_session(
                    session_id=session_id,
                    problem_statement=request.problem_statement
                )
                
                # Publish session start message
                start_message = Message(
                    message_type=MessageType.SESSION_START,
                    payload={
                        "problem_statement": request.problem_statement
                    },
                    session_id=session_id,
                    sender=self.agent_name
                )
                
                await self.publish(start_message)
                
                return {
                    "session_id": session_id,
                    "status": "started",
                    "message": "Analysis session initiated"
                }
            
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/session/{session_id}")
        async def get_session(session_id: str):
            """Get session status and results"""
            try:
                session = await self.state_manager.get_session(session_id)
                if not session:
                    raise HTTPException(status_code=404, detail="Session not found")
                
                factors = await self.state_manager.get_factors(session_id)
                debate_status = await self.state_manager.get_debate_status(session_id)
                
                return {
                    "session": session,
                    "factors": factors,
                    "debate_status": debate_status
                }
            
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    def _setup_subscriptions(self):
        """Orchestrator doesn't subscribe to messages, it initiates them"""
        pass
    
    async def process_message(self, message: Message):
        """Process messages (orchestrator mainly publishes)"""
        pass


if __name__ == "__main__":
    service = OrchestratorService()
    service.run(host="0.0.0.0", port=8000)
