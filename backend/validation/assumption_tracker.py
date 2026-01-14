"""
Assumption Tracker
Tracks all assumptions made during analysis.
"""

from typing import List, Dict, Optional
from datetime import datetime


class AssumptionTracker:
    """Tracks all assumptions made by agents during analysis."""
    
    def __init__(self):
        self.assumptions: List[Dict] = []
        self.assumptions_by_factor: Dict[int, List[Dict]] = {}
        self.assumptions_by_agent: Dict[str, List[Dict]] = {}
    
    def register_assumption(
        self,
        agent_id: str,
        factor_id: Optional[int],
        assumption: str,
        context: Optional[str] = None,
        resolution_tracker: Optional['ResolutionTracker'] = None
    ) -> Optional[Dict]:
        """
        Register an assumption made during analysis.
        
        Args:
            agent_id: ID of agent making the assumption
            factor_id: ID of factor this assumption relates to (None for general)
            assumption: Description of the assumption
            context: Optional context for the assumption
            resolution_tracker: Optional resolution tracker to check if factor is rejected
            
        Returns:
            Assumption record dict or None if factor is rejected
        """
        # Check if factor is rejected - do NOT track assumptions for rejected factors
        if resolution_tracker and factor_id:
            from validation.resolution_tracker import ResolutionStatus
            resolution = resolution_tracker.get_resolution(factor_id)
            if resolution and resolution['status'] == ResolutionStatus.REJECTED.value:
                # Do NOT track assumptions for rejected factors
                return None
        
        assumption_record = {
            'id': len(self.assumptions) + 1,
            'agent_id': agent_id,
            'factor_id': factor_id,
            'assumption': assumption,
            'context': context,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.assumptions.append(assumption_record)
        
        # Index by factor
        if factor_id is not None:
            if factor_id not in self.assumptions_by_factor:
                self.assumptions_by_factor[factor_id] = []
            self.assumptions_by_factor[factor_id].append(assumption_record)
        
        # Index by agent
        if agent_id not in self.assumptions_by_agent:
            self.assumptions_by_agent[agent_id] = []
        self.assumptions_by_agent[agent_id].append(assumption_record)
        
        return assumption_record
    
    def get_assumptions_by_factor(self, factor_id: int) -> List[Dict]:
        """Get all assumptions related to a specific factor."""
        return self.assumptions_by_factor.get(factor_id, [])
    
    def get_assumptions_by_agent(self, agent_id: str) -> List[Dict]:
        """Get all assumptions made by a specific agent."""
        return self.assumptions_by_agent.get(agent_id, [])
    
    def get_all_assumptions(self) -> List[Dict]:
        """Get all assumptions."""
        return self.assumptions.copy()
    
    def get_assumption_audit_report(self) -> str:
        """Generate a human-readable assumption audit report."""
        if not self.assumptions:
            return "=== ASSUMPTIONS AUDIT ===\n\nNo assumptions recorded.\n"
        
        report = "=== ASSUMPTIONS AUDIT ===\n\n"
        report += f"Total Assumptions: {len(self.assumptions)}\n\n"
        
        # Group by factor
        factor_ids = sorted(self.assumptions_by_factor.keys())
        
        for factor_id in factor_ids:
            assumptions = self.assumptions_by_factor[factor_id]
            report += f"Factor {factor_id}:\n"
            for i, assumption in enumerate(assumptions, 1):
                report += f"  {i}. {assumption['assumption']}\n"
                if assumption['context']:
                    report += f"     Context: {assumption['context']}\n"
                report += f"     (by {assumption['agent_id']})\n"
            report += "\n"
        
        # General assumptions (not tied to specific factor)
        general_assumptions = [a for a in self.assumptions if a['factor_id'] is None]
        if general_assumptions:
            report += "General Assumptions:\n"
            for i, assumption in enumerate(general_assumptions, 1):
                report += f"  {i}. {assumption['assumption']}\n"
                if assumption['context']:
                    report += f"     Context: {assumption['context']}\n"
                report += f"     (by {assumption['agent_id']})\n"
            report += "\n"
        
        return report
    
    def clear(self):
        """Clear all assumptions."""
        self.assumptions = []
        self.assumptions_by_factor = {}
        self.assumptions_by_agent = {}
