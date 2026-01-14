"""
Structured Claim Objects
Claims are attackable entities with assumptions, evidence, and confidence.
They can be weakened or invalidated through debate.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from enum import Enum
from datetime import datetime


class ClaimStatus(Enum):
    """Status of a claim in debate."""
    PENDING = "pending"  # Not yet challenged
    SUPPORTED = "supported"  # Has supporting evidence
    CHALLENGED = "challenged"  # Under attack
    WEAKENED = "weakened"  # Evidence reduced but not invalidated
    INVALIDATED = "invalidated"  # Claim fails
    CONCEDED = "conceded"  # Proponent conceded


class EvidenceStrength(Enum):
    """Strength of evidence supporting a claim."""
    NONE = 0
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    CONCLUSIVE = 4


@dataclass
class Assumption:
    """An assumption underlying a claim."""
    description: str
    is_valid: Optional[bool] = None  # None = untested, True/False = tested
    challenge_reason: Optional[str] = None


@dataclass
class Evidence:
    """Evidence supporting or challenging a claim."""
    description: str
    strength: EvidenceStrength
    source: Optional[str] = None
    challenges_assumption: Optional[str] = None  # Which assumption this challenges


@dataclass
class Claim:
    """
    A structured claim that can be attacked and invalidated.
    
    Claims are the fundamental units of debate in AETHER.
    They have explicit assumptions, evidence, and can fail.
    """
    claim_id: str
    content: str  # The actual claim text
    factor_id: Optional[int] = None  # Which factor this claim relates to
    agent_id: str = ""  # Which agent made the claim
    
    # Structural components
    assumptions: List[Assumption] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)
    
    # Debate state
    status: ClaimStatus = ClaimStatus.PENDING
    confidence: float = 0.5  # 0.0 to 1.0
    
    # Attack tracking
    challenges: List[str] = field(default_factory=list)  # IDs of challenging claims
    rebuttals: List[str] = field(default_factory=list)  # IDs of rebuttal claims
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def add_assumption(self, description: str) -> Assumption:
        """Add an assumption to this claim."""
        assumption = Assumption(description=description)
        self.assumptions.append(assumption)
        return assumption
    
    def add_evidence(self, description: str, strength: EvidenceStrength, source: Optional[str] = None) -> Evidence:
        """Add evidence supporting this claim."""
        evidence = Evidence(description=description, strength=strength, source=source)
        self.evidence.append(evidence)
        return evidence
    
    def challenge_assumption(self, assumption_idx: int, reason: str) -> bool:
        """
        Challenge a specific assumption.
        
        Returns:
            True if assumption was successfully challenged
        """
        if 0 <= assumption_idx < len(self.assumptions):
            self.assumptions[assumption_idx].is_valid = False
            self.assumptions[assumption_idx].challenge_reason = reason
            self._update_status()
            return True
        return False
    
    def weaken(self, reason: str):
        """Weaken the claim (reduce confidence but don't invalidate)."""
        self.confidence = max(0.0, self.confidence - 0.2)
        if self.status == ClaimStatus.SUPPORTED:
            self.status = ClaimStatus.WEAKENED
        self.updated_at = datetime.utcnow().isoformat()
    
    def invalidate(self, reason: str):
        """Invalidate the claim completely."""
        self.status = ClaimStatus.INVALIDATED
        self.confidence = 0.0
        self.updated_at = datetime.utcnow().isoformat()
    
    def concede(self):
        """Concede the claim (proponent gives up)."""
        self.status = ClaimStatus.CONCEDED
        self.updated_at = datetime.utcnow().isoformat()
    
    def _update_status(self):
        """Update status based on assumptions and evidence."""
        # If all assumptions are invalid, claim is invalidated
        if self.assumptions and all(a.is_valid is False for a in self.assumptions):
            self.status = ClaimStatus.INVALIDATED
            self.confidence = 0.0
        # If any assumption is invalid, claim is weakened
        elif any(a.is_valid is False for a in self.assumptions):
            self.status = ClaimStatus.WEAKENED
            self.confidence = max(0.0, self.confidence - 0.3)
        # If claim has strong evidence and no invalid assumptions, it's supported
        elif self.evidence and any(e.strength.value >= EvidenceStrength.STRONG.value for e in self.evidence):
            if self.status == ClaimStatus.PENDING:
                self.status = ClaimStatus.SUPPORTED
    
    def to_dict(self) -> Dict:
        """Convert claim to dictionary for serialization."""
        return {
            "claim_id": self.claim_id,
            "content": self.content,
            "factor_id": self.factor_id,
            "agent_id": self.agent_id,
            "assumptions": [
                {
                    "description": a.description,
                    "is_valid": a.is_valid,
                    "challenge_reason": a.challenge_reason
                }
                for a in self.assumptions
            ],
            "evidence": [
                {
                    "description": e.description,
                    "strength": e.strength.value,
                    "source": e.source
                }
                for e in self.evidence
            ],
            "status": self.status.value,
            "confidence": self.confidence,
            "challenges": self.challenges,
            "rebuttals": self.rebuttals,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Claim":
        """Create claim from dictionary."""
        claim = cls(
            claim_id=data["claim_id"],
            content=data["content"],
            factor_id=data.get("factor_id"),
            agent_id=data.get("agent_id", "")
        )
        
        claim.assumptions = [
            Assumption(
                description=a["description"],
                is_valid=a.get("is_valid"),
                challenge_reason=a.get("challenge_reason")
            )
            for a in data.get("assumptions", [])
        ]
        
        claim.evidence = [
            Evidence(
                description=e["description"],
                strength=EvidenceStrength(e["strength"]),
                source=e.get("source")
            )
            for e in data.get("evidence", [])
        ]
        
        claim.status = ClaimStatus(data["status"])
        claim.confidence = data["confidence"]
        claim.challenges = data.get("challenges", [])
        claim.rebuttals = data.get("rebuttals", [])
        claim.created_at = data.get("created_at", datetime.utcnow().isoformat())
        claim.updated_at = data.get("updated_at", datetime.utcnow().isoformat())
        
        return claim
