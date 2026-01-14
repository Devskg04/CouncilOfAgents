"""
Agent Registry - Self-Deployment and Discovery System
Agents register themselves and advertise capabilities.
"""

from typing import Dict, List, Optional, Set, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime


class AgentRole(Enum):
    """Defined agent roles with allowed actions."""
    FACTOR_EXTRACTION = "factor_extraction"
    SUPPORTING = "supporting"
    CRITIC = "critic"
    SYNTHESIZER = "synthesizer"
    FINAL_DECISION = "final_decision"


@dataclass
class AgentCapability:
    """Describes what an agent can do."""
    role: AgentRole
    input_types: Set[str]  # Message types this agent can consume
    output_types: Set[str]  # Message types this agent can produce
    description: str
    version: str = "1.0.0"


@dataclass
class RegisteredAgent:
    """Represents a registered agent in the system."""
    agent_id: str
    name: str
    capability: AgentCapability
    endpoint: Optional[str] = None  # For remote agents (URL/address)
    is_local: bool = True
    registered_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "active"  # active, paused, error


class AgentRegistry:
    """Central registry for agent discovery and coordination."""
    
    def __init__(self):
        self._agents: Dict[str, RegisteredAgent] = {}
        self._agents_by_role: Dict[AgentRole, List[str]] = {role: [] for role in AgentRole}
        self._agents_by_output_type: Dict[str, List[str]] = {}  # Message type -> agent IDs
    
    def register(
        self,
        agent_id: str,
        name: str,
        capability: AgentCapability,
        endpoint: Optional[str] = None,
        is_local: bool = True
    ) -> RegisteredAgent:
        """
        Register an agent with the system.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name
            capability: What the agent can do
            endpoint: Optional endpoint for remote agents
            is_local: Whether agent runs in same process
        
        Returns:
            RegisteredAgent instance
        """
        if agent_id in self._agents:
            raise ValueError(f"Agent {agent_id} already registered")
        
        registered = RegisteredAgent(
            agent_id=agent_id,
            name=name,
            capability=capability,
            endpoint=endpoint,
            is_local=is_local
        )
        
        self._agents[agent_id] = registered
        self._agents_by_role[capability.role].append(agent_id)
        
        # Index by output types for message routing
        for output_type in capability.output_types:
            if output_type not in self._agents_by_output_type:
                self._agents_by_output_type[output_type] = []
            self._agents_by_output_type[output_type].append(agent_id)
        
        return registered
    
    def unregister(self, agent_id: str) -> bool:
        """Unregister an agent."""
        if agent_id not in self._agents:
            return False
        
        agent = self._agents[agent_id]
        
        # Remove from role index
        if agent_id in self._agents_by_role[agent.capability.role]:
            self._agents_by_role[agent.capability.role].remove(agent_id)
        
        # Remove from output type index
        for output_type in agent.capability.output_types:
            if output_type in self._agents_by_output_type:
                if agent_id in self._agents_by_output_type[output_type]:
                    self._agents_by_output_type[output_type].remove(agent_id)
        
        del self._agents[agent_id]
        return True
    
    def get_agent(self, agent_id: str) -> Optional[RegisteredAgent]:
        """Get agent by ID."""
        return self._agents.get(agent_id)
    
    def get_agents_by_role(self, role: AgentRole) -> List[RegisteredAgent]:
        """Get all agents with a specific role."""
        agent_ids = self._agents_by_role.get(role, [])
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]
    
    def get_agents_by_output_type(self, message_type: str) -> List[RegisteredAgent]:
        """Get agents that can produce a specific message type."""
        agent_ids = self._agents_by_output_type.get(message_type, [])
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]
    
    def list_all_agents(self) -> List[RegisteredAgent]:
        """List all registered agents."""
        return list(self._agents.values())
    
    def clear(self):
        """Clear all registrations (for testing/reset)."""
        self._agents.clear()
        self._agents_by_role = {role: [] for role in AgentRole}
        self._agents_by_output_type.clear()
