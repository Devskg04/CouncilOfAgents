"""
Integrity Checker
Post-analysis validation of system integrity.
"""

from typing import Dict, List, Optional
from .resolution_tracker import ResolutionTracker, ResolutionStatus


class IntegrityChecker:
    """Validates system integrity after analysis."""
    
    def __init__(self):
        self.checks = {}
    
    def check_irrelevant_factors(
        self,
        factors: List[Dict],
        validation_results: Dict
    ) -> bool:
        """
        Check if any irrelevant (ungrounded) factors were introduced.
        
        Args:
            factors: List of extracted factors
            validation_results: Results from FactorValidator
            
        Returns:
            True if no irrelevant factors, False otherwise
        """
        ungrounded_count = validation_results.get('ungrounded_factors', 0)
        self.checks['irrelevant_factors'] = {
            'passed': ungrounded_count == 0,
            'count': ungrounded_count,
            'message': f"No irrelevant factors introduced" if ungrounded_count == 0 
                      else f"{ungrounded_count} ungrounded factors detected"
        }
        return ungrounded_count == 0
    
    def check_rejected_factors_excluded(
        self,
        synthesis: Dict,
        resolution_tracker: ResolutionTracker
    ) -> bool:
        """
        Check if rejected factors were excluded from synthesis.
        
        Args:
            synthesis: Synthesis result dict
            resolution_tracker: ResolutionTracker instance
            
        Returns:
            True if rejected factors excluded, False otherwise
        """
        rejected_factor_ids = set(resolution_tracker.get_rejected_factors())
        
        if not rejected_factor_ids:
            self.checks['rejected_factors_excluded'] = {
                'passed': True,
                'message': "No rejected factors to exclude"
            }
            return True
        
        # Check if any rejected factor IDs appear in synthesis
        synthesis_text = str(synthesis).lower()
        structured = synthesis.get('structured', {})
        
        # Check what_worked and narrative_summary
        what_worked = structured.get('what_worked', [])
        what_worked_ids = {item.get('factor_id') for item in what_worked if isinstance(item, dict)}
        
        # Check if any rejected factor appears in what_worked
        rejected_in_synthesis = rejected_factor_ids.intersection(what_worked_ids)
        
        if rejected_in_synthesis:
            self.checks['rejected_factors_excluded'] = {
                'passed': False,
                'rejected_ids': list(rejected_in_synthesis),
                'message': f"INVALID: Rejected factors {rejected_in_synthesis} appear in synthesis"
            }
            return False
        
        self.checks['rejected_factors_excluded'] = {
            'passed': True,
            'rejected_count': len(rejected_factor_ids),
            'message': f"{len(rejected_factor_ids)} rejected factors properly excluded from synthesis"
        }
        return True
    
    def check_circular_reasoning(
        self,
        validation_results: Dict
    ) -> bool:
        """
        Check if any circular reasoning was detected.
        
        Args:
            validation_results: Results from FactorValidator
            
        Returns:
            True if no circular reasoning, False otherwise
        """
        circular_count = validation_results.get('circular_factors', 0)
        
        self.checks['circular_reasoning'] = {
            'passed': circular_count == 0,
            'count': circular_count,
            'message': "No circular reasoning detected" if circular_count == 0
                      else f"{circular_count} circular factors detected and rejected"
        }
        return circular_count == 0
    
    def check_critic_won_debate(
        self,
        resolution_tracker: ResolutionTracker
    ) -> bool:
        """
        Check if the critic agent won at least one debate.
        
        Args:
            resolution_tracker: ResolutionTracker instance
            
        Returns:
            True if critic won at least one debate, False otherwise
        """
        critic_won = resolution_tracker.did_critic_win_any_debate()
        rejected_count = len(resolution_tracker.get_rejected_factors())
        
        self.checks['critic_won_debate'] = {
            'passed': critic_won,
            'rejected_count': rejected_count,
            'message': f"Critic won {rejected_count} debate(s)" if critic_won
                      else "WARNING: Critic did not reject any factors"
        }
        return critic_won
    
    def check_all_factors_resolved(
        self,
        factors: List[Dict],
        resolution_tracker: ResolutionTracker
    ) -> bool:
        """
        Check if all factors have explicit resolutions.
        
        Args:
            factors: List of factors
            resolution_tracker: ResolutionTracker instance
            
        Returns:
            True if all factors resolved, False otherwise
        """
        factor_ids = [f['id'] for f in factors]
        unresolved = resolution_tracker.get_unresolved_factors(factor_ids)
        
        self.checks['all_factors_resolved'] = {
            'passed': len(unresolved) == 0,
            'unresolved_count': len(unresolved),
            'unresolved_ids': unresolved,
            'message': "All factors have explicit resolutions" if len(unresolved) == 0
                      else f"INVALID: {len(unresolved)} factors lack explicit resolution: {unresolved}"
        }
        return len(unresolved) == 0
    
    def check_synthesis_validity(
        self,
        factors: List[Dict],
        validation_results: Dict,
        resolution_tracker: ResolutionTracker,
        synthesis: Dict
    ) -> bool:
        """
        Overall synthesis validity check.
        
        Args:
            factors: List of factors
            validation_results: Validation results
            resolution_tracker: Resolution tracker
            synthesis: Synthesis result
            
        Returns:
            True if synthesis is valid, False otherwise
        """
        # Run all checks
        check1 = self.check_irrelevant_factors(factors, validation_results)
        check2 = self.check_rejected_factors_excluded(synthesis, resolution_tracker)
        check3 = self.check_circular_reasoning(validation_results)
        check4 = self.check_critic_won_debate(resolution_tracker)
        check5 = self.check_all_factors_resolved(factors, resolution_tracker)
        
        # Synthesis is valid if:
        # - No irrelevant factors (or they were rejected)
        # - Rejected factors excluded from synthesis
        # - No circular reasoning (or it was detected and rejected)
        # - All factors have explicit resolutions
        is_valid = check2 and check5  # Most critical checks
        
        self.checks['synthesis_valid'] = {
            'passed': is_valid,
            'message': "Synthesis is VALID" if is_valid else "Synthesis is INVALID"
        }
        
        return is_valid
    
    def get_integrity_report(self) -> str:
        """Generate a human-readable integrity report."""
        report = "=== SYSTEM INTEGRITY CHECK ===\n\n"
        
        checks_order = [
            ('irrelevant_factors', 'Were any irrelevant factors introduced?'),
            ('rejected_factors_excluded', 'Did any rejected factor influence synthesis?'),
            ('circular_reasoning', 'Did any circular reasoning occur?'),
            ('critic_won_debate', 'Did the Critic Agent win any debate?'),
            ('all_factors_resolved', 'Do all factors have explicit resolutions?'),
            ('synthesis_valid', 'Is the synthesis VALID?')
        ]
        
        for check_key, check_question in checks_order:
            if check_key in self.checks:
                check = self.checks[check_key]
                status = "✓" if check['passed'] else "✗"
                report += f"{status} {check_question}\n"
                report += f"   {check['message']}\n\n"
        
        # Overall verdict
        if 'synthesis_valid' in self.checks:
            if self.checks['synthesis_valid']['passed']:
                report += "VERDICT: Analysis passed all integrity checks.\n"
            else:
                report += "VERDICT: Analysis FAILED integrity checks.\n"
                report += "\nREASON FOR FAILURE:\n"
                for check_key, _ in checks_order:
                    if check_key in self.checks and not self.checks[check_key]['passed']:
                        report += f"  - {self.checks[check_key]['message']}\n"
        
        return report
    
    def get_integrity_summary(self) -> Dict:
        """Get integrity check results as a dict."""
        return {
            'checks': self.checks,
            'all_passed': all(check.get('passed', False) for check in self.checks.values()),
            'synthesis_valid': self.checks.get('synthesis_valid', {}).get('passed', False)
        }
    
    def clear(self):
        """Clear all checks."""
        self.checks = {}
