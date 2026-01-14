"""
Base Agent Class
Common functionality for all agents with self-deployment and reactive behavior.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional, Dict
from coordination.message_bus import MessageBus
from coordination.agent_registry import AgentRegistry, AgentRole, AgentCapability, RegisteredAgent
from coordination.role_policy import RolePolicyEngine, ActionType, PolicyViolation


class BaseAgent(ABC):
    """
    Base class for all agents with self-deployment and event-driven behavior.
    
    Agents:
    - Register themselves on initialization
    - Subscribe to relevant message types
    - React to events automatically
    - Enforce role-based policies
    """
    
    def __init__(
        self,
        name: str,
        agent_id: str,
        role: AgentRole,
        message_bus: MessageBus,
        llm_client,
        registry: Optional[AgentRegistry] = None,
        policy_engine: Optional[RolePolicyEngine] = None
    ):
        self.name = name
        self.agent_id = agent_id
        self.role = role
        self.message_bus = message_bus
        self.llm_client = llm_client
        self.registry = registry
        self.policy_engine = policy_engine
        
        # Register this agent
        if registry:
            self._register()
        
        # Subscribe to relevant events
        self._setup_subscriptions()
    
    def _register(self):
        """Register this agent with the registry."""
        if not self.registry:
            return
        
        capability = AgentCapability(
            role=self.role,
            input_types=self._get_input_types(),
            output_types=self._get_output_types(),
            description=self._get_description()
        )
        
        self.registered_agent = self.registry.register(
            agent_id=self.agent_id,
            name=self.name,
            capability=capability,
            is_local=True
        )
    
    def _setup_subscriptions(self):
        """Set up event subscriptions. Override in subclasses."""
        pass
    
    def _get_input_types(self) -> set:
        """Get message types this agent can consume. Override in subclasses."""
        return set()
    
    def _get_output_types(self) -> set:
        """Get message types this agent can produce. Override in subclasses."""
        return set()
    
    def _get_description(self) -> str:
        """Get agent description. Override in subclasses."""
        return f"{self.name} agent"
    
    def _validate_action(self, action: ActionType):
        """Validate that this agent can perform an action."""
        if self.policy_engine and hasattr(self, 'registered_agent'):
            self.policy_engine.validate_action(self.registered_agent, action)
    
    def _validate_message_type(self, message_type: str):
        """Validate that this agent can publish a message type."""
        if self.policy_engine and hasattr(self, 'registered_agent'):
            self.policy_engine.validate_message_type(self.registered_agent, message_type)
    
    async def _publish(self, message: Dict):
        """Publish a message with validation."""
        message_type = message.get('type')
        if message_type:
            self._validate_message_type(message_type)
        
        message['agent'] = self.name
        message['agent_id'] = self.agent_id
        await self.message_bus.publish(message, agent_id=self.agent_id)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        return datetime.utcnow().isoformat()
    
    async def process(self, *args, **kwargs) -> Any:
        """
        Process method - optional, can be overridden by agents that need it.
        Some agents use specific methods instead (e.g., support_factor, critique_factor).
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement process() or use specific methods")

