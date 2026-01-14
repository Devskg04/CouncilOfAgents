"""
Message Bus - Event-Driven Coordination Layer for Agent Communication
Supports publish/subscribe pattern for reactive agent behavior.
"""

from enum import Enum
from typing import List, Dict, Optional, Callable, Set
from datetime import datetime
import asyncio


class MessageType(Enum):
    """Types of messages in the coordination layer."""
    FACTOR_LIST = "FACTOR_LIST"
    FACTOR_DISCOVERED = "FACTOR_DISCOVERED"  # Individual factor published
    SUPPORT_ARGUMENT = "SUPPORT_ARGUMENT"
    CRITIQUE = "CRITIQUE"
    REBUTTAL = "REBUTTAL"
    SYNTHESIS_NOTE = "SYNTHESIS_NOTE"
    FINAL_DIRECTIVE = "FINAL_DIRECTIVE"


class MessageBus:
    """
    Event-driven message bus with subscription support.
    Agents subscribe to message types and react automatically.
    """
    
    def __init__(self):
        self.messages: List[Dict] = []
        self.factors: List[Dict] = []
        
        # Subscription system: message_type -> list of handler callbacks
        self._subscriptions: Dict[str, List[Callable]] = {}
        
        # Track which agents have handled which messages (for idempotency)
        self._handled_by: Dict[str, Set[str]] = {}  # message_id -> set of agent_ids
    
    def subscribe(self, message_type: str, handler: Callable):
        """
        Subscribe to a message type.
        
        Args:
            message_type: The message type to listen for
            handler: Async callback function(message: Dict) -> None
        """
        if message_type not in self._subscriptions:
            self._subscriptions[message_type] = []
        self._subscriptions[message_type].append(handler)
    
    def unsubscribe(self, message_type: str, handler: Callable):
        """Unsubscribe from a message type."""
        if message_type in self._subscriptions:
            if handler in self._subscriptions[message_type]:
                self._subscriptions[message_type].remove(handler)
    
    async def publish(self, message: Dict, agent_id: Optional[str] = None):
        """
        Publish a message to the bus and notify subscribers.
        
        Args:
            message: Message dictionary with 'type' field
            agent_id: Optional ID of agent publishing (for tracking)
        """
        if not isinstance(message, dict):
            raise ValueError("Message must be a dictionary")
        
        message['timestamp'] = message.get('timestamp', datetime.utcnow().isoformat())
        message['id'] = message.get('id', f"msg_{len(self.messages)}")
        message['publisher'] = agent_id
        
        self.messages.append(message)
        
        # Store factors separately for easy access
        if message.get('type') == MessageType.FACTOR_LIST.value:
            self.factors = message.get('factors', [])
            # Also publish individual FACTOR_DISCOVERED events for reactive processing
            for factor in self.factors:
                await self.publish({
                    'type': MessageType.FACTOR_DISCOVERED.value,
                    'factor': factor,
                    'factor_id': factor.get('id')
                }, agent_id=agent_id)
        
        # Notify subscribers
        message_type = message.get('type')
        if message_type in self._subscriptions:
            # Call all subscribers asynchronously
            tasks = []
            for handler in self._subscriptions[message_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        tasks.append(asyncio.create_task(handler(message)))
                    else:
                        # Sync handler, wrap in async
                        handler(message)
                except Exception as e:
                    print(f"Error in subscription handler for {message_type}: {e}")
            
            # Wait for all async handlers
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    def mark_handled(self, message_id: str, agent_id: str):
        """Mark a message as handled by an agent (for idempotency)."""
        if message_id not in self._handled_by:
            self._handled_by[message_id] = set()
        self._handled_by[message_id].add(agent_id)
    
    def is_handled_by(self, message_id: str, agent_id: str) -> bool:
        """Check if a message was already handled by an agent."""
        return agent_id in self._handled_by.get(message_id, set())
    
    def get_all_messages(self) -> List[Dict]:
        """Get all messages in chronological order."""
        return self.messages.copy()
    
    def get_messages_by_type(self, message_type: MessageType) -> List[Dict]:
        """Get messages of a specific type."""
        return [
            msg for msg in self.messages
            if msg.get('type') == message_type.value
        ]
    
    def get_factors(self) -> List[Dict]:
        """Get all extracted factors."""
        return self.factors.copy()
    
    def get_factor(self, factor_id: int) -> Optional[Dict]:
        """Get a specific factor by ID."""
        for factor in self.factors:
            if factor.get('id') == factor_id:
                return factor
        return None
    
    def clear(self):
        """Clear all messages and factors."""
        self.messages = []
        self.factors = []
        self._handled_by.clear()
    
    def get_debate_summary(self) -> Dict:
        """Get a summary of all debates organized by factor."""
        summary = {}
        
        for factor in self.factors:
            factor_id = factor['id']
            summary[factor_id] = {
                "factor": factor,
                "support": None,
                "critique": None,
                "rebuttal": None,
                "debate_rounds": 0
            }
        
        for msg in self.messages:
            msg_type = msg.get('type')
            factor_id = msg.get('factor_id')
            
            if factor_id and factor_id in summary:
                if msg_type == MessageType.SUPPORT_ARGUMENT.value:
                    summary[factor_id]['support'] = msg
                    summary[factor_id]['debate_rounds'] += 1
                elif msg_type == MessageType.CRITIQUE.value:
                    summary[factor_id]['critique'] = msg
                    summary[factor_id]['debate_rounds'] += 1
                elif msg_type == MessageType.REBUTTAL.value:
                    summary[factor_id]['rebuttal'] = msg
                    summary[factor_id]['debate_rounds'] += 1
        
        return summary

