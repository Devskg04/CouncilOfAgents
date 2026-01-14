"""
Role-Based Policy Engine
Enforces agent role constraints at runtime.
Prevents agents from exceeding their scope.
"""

from typing import Dict, Set, Optional
from enum import Enum
from coordination.agent_registry import AgentRole, RegisteredAgent


class PolicyViolation(Exception):
    """Raised when an agent violates its role policy."""
    pass


class ActionType(Enum):
    """Types of actions agents can attempt."""
    EXTRACT_FACTORS = "extract_factors"
    GENERATE_SUPPORT = "generate_support"
    GENERATE_CRITIQUE = "generate_critique"
    GENERATE_REBUTTAL = "generate_rebuttal"
    SYNTHESIZE = "synthesize"
    GENERATE_FINAL_REPORT = "generate_final_report"
    PUBLISH_MESSAGE = "publish_message"


class RolePolicyEngine:
    """Enforces role-based execution constraints."""
    
    # Define allowed actions per role
    ROLE_PERMISSIONS: Dict[AgentRole, Set[ActionType]] = {
        AgentRole.FACTOR_EXTRACTION: {
            ActionType.EXTRACT_FACTORS,
            ActionType.PUBLISH_MESSAGE
        },
        AgentRole.SUPPORTING: {
            ActionType.GENERATE_SUPPORT,
            ActionType.GENERATE_REBUTTAL,
            ActionType.PUBLISH_MESSAGE
        },
        AgentRole.CRITIC: {
            ActionType.GENERATE_CRITIQUE,
            ActionType.PUBLISH_MESSAGE
        },
        AgentRole.SYNTHESIZER: {
            ActionType.SYNTHESIZE,
            ActionType.PUBLISH_MESSAGE
        },
        AgentRole.FINAL_DECISION: {
            ActionType.GENERATE_FINAL_REPORT,
            ActionType.PUBLISH_MESSAGE
        }
    }
    
    # Define allowed message types per role (what they can publish)
    ROLE_OUTPUT_TYPES: Dict[AgentRole, Set[str]] = {
        AgentRole.FACTOR_EXTRACTION: {"FACTOR_LIST"},
        AgentRole.SUPPORTING: {"SUPPORT_ARGUMENT", "REBUTTAL"},
        AgentRole.CRITIC: {"CRITIQUE"},
        AgentRole.SYNTHESIZER: {"SYNTHESIS_NOTE"},
        AgentRole.FINAL_DECISION: {"FINAL_DIRECTIVE"}
    }
    
    def __init__(self):
        self._enabled = True  # Can be disabled for testing
    
    def validate_action(self, agent: RegisteredAgent, action: ActionType) -> bool:
        """
        Validate that an agent is allowed to perform an action.
        
        Args:
            agent: The agent attempting the action
            action: The action being attempted
        
        Returns:
            True if allowed
        
        Raises:
            PolicyViolation if not allowed
        """
        if not self._enabled:
            return True
        
        allowed_actions = self.ROLE_PERMISSIONS.get(agent.capability.role, set())
        
        if action not in allowed_actions:
            raise PolicyViolation(
                f"Agent {agent.name} (role: {agent.capability.role.value}) "
                f"is not allowed to perform action: {action.value}"
            )
        
        return True
    
    def validate_message_type(self, agent: RegisteredAgent, message_type: str) -> bool:
        """
        Validate that an agent can publish a specific message type.
        
        Args:
            agent: The agent attempting to publish
            message_type: The message type being published
        
        Returns:
            True if allowed
        
        Raises:
            PolicyViolation if not allowed
        """
        if not self._enabled:
            return True
        
        allowed_types = self.ROLE_OUTPUT_TYPES.get(agent.capability.role, set())
        
        if message_type not in allowed_types:
            raise PolicyViolation(
                f"Agent {agent.name} (role: {agent.capability.role.value}) "
                f"is not allowed to publish message type: {message_type}"
            )
        
        return True
    
    def enable(self):
        """Enable policy enforcement."""
        self._enabled = True
    
    def disable(self):
        """Disable policy enforcement (for testing)."""
        self._enabled = False
