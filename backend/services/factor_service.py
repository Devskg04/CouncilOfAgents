"""
Factor Agent Service - Extracts factors from documents
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.base_agent_service import BaseAgentService
from infrastructure.local_message_bus import Message, MessageType
from agents.factor_extraction_agent import FactorExtractionAgent


class FactorAgentService(BaseAgentService):
    """Factor extraction agent service"""
    
    def __init__(self):
        super().__init__("FactorAgent", "factor")
        
        # Initialize the actual factor extraction agent
        from orchestration.message_bus import MessageBus
        from llm.llm_client import LLMClient
        
        message_bus = MessageBus()
        llm_client = LLMClient()
        
        self.factor_agent = FactorExtractionAgent(
            agent_id="factor_agent",
            message_bus=message_bus,
            llm_client=llm_client
        )
    
    def _setup_subscriptions(self):
        """Subscribe to session start messages"""
        self.subscribe(MessageType.SESSION_START)
    
    async def process_message(self, message: Message):
        """Process session start and extract factors"""
        if message.message_type == MessageType.SESSION_START:
            session_id = message.session_id
            problem_statement = message.payload.get("problem_statement", "")
            
            # Extract factors using the existing agent
            factors = await self.factor_agent.extract_factors(problem_statement)
            
            # Store factors in state
            for factor in factors:
                await self.state_manager.store_factor(
                    session_id=session_id,
                    factor_id=factor["id"],
                    name=factor["name"],
                    description=factor["description"],
                    validation=factor.get("validation")
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


if __name__ == "__main__":
    service = FactorAgentService()
    service.run(host="0.0.0.0", port=8000)
