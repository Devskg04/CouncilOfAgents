"""
Final Decision Agent Service - Generates final report
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.base_agent_service import BaseAgentService
from infrastructure.local_message_bus import Message, MessageType
from agents.final_decision_agent import FinalDecisionAgent


class FinalDecisionAgentService(BaseAgentService):
    """Final decision agent service"""
    
    def __init__(self):
        super().__init__("FinalDecisionAgent", "final_decision")
        
        # Initialize the actual final decision agent
        from orchestration.message_bus import MessageBus
        from llm.llm_client import LLMClient
        
        message_bus = MessageBus()
        llm_client = LLMClient()
        
        self.final_decision_agent = FinalDecisionAgent(
            agent_id="final_decision_agent",
            message_bus=message_bus,
            llm_client=llm_client
        )
    
    def _setup_subscriptions(self):
        """Subscribe to synthesis notes"""
        self.subscribe(MessageType.SYNTHESIS_NOTE)
    
    async def process_message(self, message: Message):
        """Process synthesis and generate final report"""
        if message.message_type == MessageType.SYNTHESIS_NOTE:
            session_id = message.session_id
            
            # Get session and all data
            session = await self.state_manager.get_session(session_id)
            factors = await self.state_manager.get_factors(session_id)
            
            input_text = session["problem_statement"] if session else ""
            
            # Generate final report (simplified)
            final_report = {
                "session_id": session_id,
                "total_factors": len(factors),
                "status": "completed"
            }
            
            # Store final report
            await self.state_manager.store_agent_output(
                session_id=session_id,
                agent_name=self.agent_name,
                output_type="FINAL_REPORT",
                content=final_report
            )
            
            # Update session status
            await self.state_manager.update_session_status(session_id, "completed")
            
            # Publish final report
            report_message = Message(
                message_type=MessageType.FINAL_REPORT,
                payload={"report": final_report},
                session_id=session_id,
                sender=self.agent_name
            )
            await self.publish(report_message)


if __name__ == "__main__":
    service = FinalDecisionAgentService()
    service.run(host="0.0.0.0", port=8000)
