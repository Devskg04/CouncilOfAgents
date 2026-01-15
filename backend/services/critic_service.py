"""
Critic Agent Service - Provides counter-arguments
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.base_agent_service import BaseAgentService
from infrastructure.local_message_bus import Message, MessageType
from agents.critic_agent import CriticAgent


class CriticAgentService(BaseAgentService):
    """Critic agent service"""
    
    def __init__(self):
        super().__init__("CriticAgent", "critic")
        
        # Initialize the actual critic agent
        from orchestration.message_bus import MessageBus
        from llm.llm_client import LLMClient
        
        message_bus = MessageBus()
        llm_client = LLMClient()
        
        self.critic_agent = CriticAgent(
            agent_id="critic_agent",
            message_bus=message_bus,
            llm_client=llm_client
        )
    
    def _setup_subscriptions(self):
        """Subscribe to support argument messages"""
        self.subscribe(MessageType.SUPPORT_ARGUMENT)
    
    async def process_message(self, message: Message):
        """Process support argument and generate critique"""
        if message.message_type == MessageType.SUPPORT_ARGUMENT:
            session_id = message.session_id
            factor_id = message.payload.get("factor_id")
            support = message.payload.get("support")
            
            # Get factor and problem statement
            factor = await self.state_manager.get_factor(session_id, factor_id)
            session = await self.state_manager.get_session(session_id)
            input_text = session["problem_statement"] if session else ""
            
            # Generate critique
            critique = await self.critic_agent.critique_factor(factor, support, input_text)
            
            # Store in state
            await self.state_manager.store_agent_output(
                session_id=session_id,
                agent_name=self.agent_name,
                output_type="CRITIQUE",
                content=critique,
                factor_id=factor_id
            )
            
            # Publish critique message
            critique_message = Message(
                message_type=MessageType.CRITIQUE,
                payload={
                    "factor_id": factor_id,
                    "critique": critique
                },
                session_id=session_id,
                sender=self.agent_name
            )
            await self.publish(critique_message)


if __name__ == "__main__":
    service = CriticAgentService()
    service.run(host="0.0.0.0", port=8000)
