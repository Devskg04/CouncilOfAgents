"""
Coordination Layer - Message Bus, Registry, and Policy Engine for Agent Communication
"""

from .message_bus import MessageBus, MessageType
from .agent_registry import AgentRegistry, AgentRole, AgentCapability, RegisteredAgent
from .role_policy import RolePolicyEngine, ActionType, PolicyViolation
from .claims import Claim, ClaimStatus, EvidenceStrength, Assumption, Evidence

__all__ = [
    'MessageBus', 'MessageType',
    'AgentRegistry', 'AgentRole', 'AgentCapability', 'RegisteredAgent',
    'RolePolicyEngine', 'ActionType', 'PolicyViolation',
    'Claim', 'ClaimStatus', 'EvidenceStrength', 'Assumption', 'Evidence'
]

