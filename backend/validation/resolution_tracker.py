"""
Resolution Tracker
Tracks debate resolution status for each factor.
"""

from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime


class ResolutionStatus(Enum):
    """Resolution status for factors after debate."""
    PENDING = "PENDING"  # Not yet resolved
    ACCEPTED = "ACCEPTED"  # Factor accepted with strong evidence
    PARTIALLY_ACCEPTED = "PARTIALLY_ACCEPTED"  # Some sub-claims accepted, others rejected
    REJECTED = "REJECTED"  # Factor rejected due to lack of evidence or circular reasoning


class ResolutionTracker:
    """Tracks debate resolution status for each factor."""
    
    def __init__(self):
        self.resolutions: Dict[int, Dict] = {}
    
    def set_resolution(
        self,
        factor_id: int,
        status: ResolutionStatus,
        justification: str,
        sub_claims: Optional[List[Dict]] = None,
        critic_agent_id: Optional[str] = None
    ) -> Dict:
        """
        Set the resolution status for a factor.
        
        Args:
            factor_id: ID of the factor
            status: Resolution status
            justification: Explanation for the resolution
            sub_claims: For PARTIALLY_ACCEPTED, list of sub-claims with their status
            critic_agent_id: ID of critic agent that made the resolution
            
        Returns:
            Resolution record dict
        """
        if status == ResolutionStatus.PARTIALLY_ACCEPTED and not sub_claims:
            raise ValueError("PARTIALLY_ACCEPTED status requires sub_claims to be specified")
        
        resolution = {
            'factor_id': factor_id,
            'status': status.value,
            'justification': justification,
            'sub_claims': sub_claims or [],
            'critic_agent_id': critic_agent_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.resolutions[factor_id] = resolution
        return resolution
    
    def get_resolution(self, factor_id: int) -> Optional[Dict]:
        """Get the resolution for a specific factor."""
        return self.resolutions.get(factor_id)
    
    def get_unresolved_factors(self, all_factor_ids: List[int]) -> List[int]:
        """Get list of factor IDs that don't have a resolution."""
        return [fid for fid in all_factor_ids if fid not in self.resolutions]
    
    def get_factors_by_status(self, status: ResolutionStatus) -> List[Dict]:
        """Get all resolutions with a specific status."""
        return [
            res for res in self.resolutions.values()
            if res['status'] == status.value
        ]
    
    def get_accepted_factors(self) -> List[int]:
        """Get list of accepted factor IDs."""
        return [
            fid for fid, res in self.resolutions.items()
            if res['status'] == ResolutionStatus.ACCEPTED.value
        ]
    
    def get_partially_accepted_factors(self) -> List[int]:
        """Get list of partially accepted factor IDs."""
        return [
            fid for fid, res in self.resolutions.items()
            if res['status'] == ResolutionStatus.PARTIALLY_ACCEPTED.value
        ]
    
    def get_rejected_factors(self) -> List[int]:
        """Get list of rejected factor IDs."""
        return [
            fid for fid, res in self.resolutions.items()
            if res['status'] == ResolutionStatus.REJECTED.value
        ]
    
    def did_critic_win_any_debate(self) -> bool:
        """Check if the critic agent won at least one debate (rejected a factor)."""
        return len(self.get_rejected_factors()) > 0
    
    def get_resolution_report(self, factors: List[Dict]) -> str:
        """Generate a human-readable resolution report."""
        report = "=== DEBATE RESOLUTIONS ===\n\n"
        
        accepted = self.get_accepted_factors()
        partial = self.get_partially_accepted_factors()
        rejected = self.get_rejected_factors()
        
        report += f"Total Factors: {len(factors)}\n"
        report += f"Accepted: {len(accepted)}\n"
        report += f"Partially Accepted: {len(partial)}\n"
        report += f"Rejected: {len(rejected)}\n\n"
        
        # Detailed resolutions
        for factor in factors:
            factor_id = factor['id']
            resolution = self.get_resolution(factor_id)
            
            if not resolution:
                report += f"Factor {factor_id}: {factor['name']}\n"
                report += "  Status: UNRESOLVED (ERROR)\n\n"
                continue
            
            report += f"Factor {factor_id}: {factor['name']}\n"
            report += f"  Resolution: {resolution['status']}\n"
            report += f"  Justification: {resolution['justification']}\n"
            
            if resolution['sub_claims']:
                report += "  Sub-claims:\n"
                for sc in resolution['sub_claims']:
                    report += f"    - {sc['claim']}: {sc['status']}\n"
            
            report += "\n"
        
        return report
    
    def clear(self):
        """Clear all resolutions."""
        self.resolutions = {}
