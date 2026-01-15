"""
Synthesizer Agent Service - Synthesizes debate results
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.base_agent_service import BaseAgentService
from infrastructure.local_message_bus import Message, MessageType


class SynthesizerAgentService(BaseAgentService):
    """Synthesizer agent service"""
    
    def __init__(self):
        super().__init__("SynthesizerAgent", "synthesizer")
    
    def _setup_subscriptions(self):
        """Subscribe to critique messages"""
        self.subscribe(MessageType.CRITIQUE)
    
    async def process_message(self, message: Message):
        """Process critique and synthesize results"""
        if message.message_type == MessageType.CRITIQUE:
            session_id = message.session_id
            
            # Get all factors and their debates
            factors = await self.state_manager.get_factors(session_id)
            
            # Simple synthesis logic (can be enhanced)
            synthesis = {
                "total_factors": len(factors),
                "status": "in_progress"
            }
            
            # Store synthesis
            await self.state_manager.store_agent_output(
                session_id=session_id,
                agent_name=self.agent_name,
                output_type="SYNTHESIS",
                content=synthesis
            )
            
            # Publish synthesis note
            synthesis_message = Message(
                message_type=MessageType.SYNTHESIS_NOTE,
                payload={"synthesis": synthesis},
                session_id=session_id,
                sender=self.agent_name
            )
            await self.publish(synthesis_message)


if __name__ == "__main__":
    service = SynthesizerAgentService()
    service.run(host="0.0.0.0", port=8000)
