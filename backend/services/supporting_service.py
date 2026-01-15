"""
Supporting Agent Service - Generates supporting arguments
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.base_agent_service import BaseAgentService
from infrastructure.local_message_bus import Message, MessageType
from agents.supporting_agent import SupportingAgent


class SupportingAgentService(BaseAgentService):
    """Supporting agent service"""
    
    def __init__(self):
        super().__init__("SupportingAgent", "supporting")
        
        # Initialize the actual supporting agent
        from orchestration.message_bus import MessageBus
        from llm.llm_client import LLMClient
        
        message_bus = MessageBus()
        llm_client = LLMClient()
        
        self.supporting_agent = SupportingAgent(
            agent_id="supporting_agent",
            message_bus=message_bus,
            llm_client=llm_client
        )
    
    def _setup_subscriptions(self):
        """Subscribe to factor discovered messages"""
        self.subscribe(MessageType.FACTOR_DISCOVERED)
    
    async def process_message(self, message: Message):
        """Process factor discovered and generate support"""
        if message.message_type == MessageType.FACTOR_DISCOVERED:
            session_id = message.session_id
            factor = message.payload.get("factor")
            
            # Get problem statement from session
            session = await self.state_manager.get_session(session_id)
            input_text = session["problem_statement"] if session else ""
            
            # Generate supporting argument
            support = await self.supporting_agent.support_factor(factor, input_text)
            
            # Store in state
            await self.state_manager.store_agent_output(
                session_id=session_id,
                agent_name=self.agent_name,
                output_type="SUPPORT_ARGUMENT",
                content=support,
                factor_id=factor["id"]
            )
            
            # Publish support argument message
            support_message = Message(
                message_type=MessageType.SUPPORT_ARGUMENT,
                payload={
                    "factor_id": factor["id"],
                    "support": support
                },
                session_id=session_id,
                sender=self.agent_name
            )
            await self.publish(support_message)


if __name__ == "__main__":
    service = SupportingAgentService()
    service.run(host="0.0.0.0", port=8000)
