"""
Output Formatter
Formats analysis results according to strict validation rules output format.
"""

from typing import Dict, List


class OutputFormatter:
    """Formats analysis results in the required strict format."""
    
    @staticmethod
    def format_analysis_output(result: Dict) -> str:
        """
        Format analysis result according to strict validation rules.
        
        Args:
            result: Analysis result dict from Orchestrator
            
        Returns:
            Formatted output string
        """
        lines = []  # Use lines instead of output to avoid confusion
        
        # === FACTOR EXTRACTION ===
        lines.append("=== FACTOR EXTRACTION ===\n")
        factors = result.get('factors', [])
        for factor in factors:
            validation = factor.get('validation', {})
            status = "✓" if validation.get('is_valid', True) else "✗"
            lines.append(f"{status} Factor {factor['id']}: {factor['name']}")
            lines.append(f"   Description: {factor['description']}")
            if not validation.get('is_valid', True):
                if validation.get('is_circular'):
                    lines.append(f"   REJECTED: {validation.get('circular_note', 'Circular reasoning')}")
                elif not validation.get('is_grounded'):
                    lines.append(f"   REJECTED: {validation.get('grounding_note', 'Not grounded in document')}")
            lines.append("")
        
        # === FACTOR VALIDATION ===
        lines.append("\n=== FACTOR VALIDATION ===\n")
        validation_results = result.get('validation_results', {})
        if validation_results:
            lines.append(f"Total Factors: {validation_results.get('total_factors', 0)}")
            lines.append(f"Valid Factors: {validation_results.get('valid_factors', 0)}")
            lines.append(f"Grounded Factors: {validation_results.get('grounded_factors', 0)}/{validation_results.get('total_factors', 0)}")
            lines.append(f"Circular Factors Detected: {validation_results.get('circular_factors', 0)} (rejected)")
        lines.append("")
        
        # === AGENT DEBATE LOG ===
        lines.append("\n=== AGENT DEBATE LOG ===\n")
        debates = result.get('debates', {})
        
        # Handle both dict and list formats
        if isinstance(debates, dict):
            debate_items = debates.items()
        else:
            debate_items = enumerate(debates)
        
        for factor_id, debate in debate_items:
            if isinstance(debate, dict):
                factor = debate.get('factor', {})
                lines.append(f"Factor {factor_id}: {factor.get('name', 'Unknown')}")
                
                # Supporting Agent
                support = debate.get('support')
                if support:
                    lines.append(f"  Supporting Agent:")
                    lines.append(f"    {support.get('argument', '')[:200]}...")
                    lines.append(f"    Evidence Provided: {'Yes' if support.get('has_evidence', True) else 'No'}")
                
                # Critic Agent
                critique = debate.get('critique')
                if critique:
                    lines.append(f"  Critic Agent:")
                    lines.append(f"    {critique.get('argument', '')[:200]}...")
                    lines.append(f"  Resolution: {critique.get('resolution', 'UNKNOWN')}")
                    lines.append(f"  Justification: {critique.get('justification', 'See critique above')}")
                    
                    # Sub-claims for PARTIALLY_ACCEPTED
                    sub_claims = critique.get('sub_claims', [])
                    if sub_claims:
                        lines.append(f"  Sub-claims:")
                        for sc in sub_claims:
                            lines.append(f"    - {sc['claim']}: {sc['status']}")
                
                lines.append("")
        
        # === REJECTED FACTORS (ENFORCED) ===
        lines.append("\n=== REJECTED FACTORS (ENFORCED) ===\n")
        resolutions = result.get('resolutions', {})
        rejected_ids = resolutions.get('rejected', [])
        
        if rejected_ids:
            synthesis = result.get('synthesis', {})
            rejected_factors = synthesis.get('rejected_factors', [])
            
            for rejected in rejected_factors:
                lines.append(f"Factor {rejected['factor_id']}: {rejected['factor_name']}")
                lines.append(f"  Rejection Reason: {rejected['rejection_reason']}")
            
            lines.append(f"\n✓ Confirmed: {len(rejected_ids)} rejected factors excluded from synthesis")
        else:
            lines.append("No factors were rejected.")
        lines.append("")
        
        # === ASSUMPTIONS AUDIT ===
        lines.append("\n=== ASSUMPTIONS AUDIT ===\n")
        assumptions = result.get('assumptions', [])
        
        if assumptions:
            # Group by factor
            assumptions_by_factor = {}
            for assumption in assumptions:
                factor_id = assumption.get('factor_id')
                if factor_id not in assumptions_by_factor:
                    assumptions_by_factor[factor_id] = []
                assumptions_by_factor[factor_id].append(assumption)
            
            for factor_id, factor_assumptions in sorted(assumptions_by_factor.items()):
                lines.append(f"Factor {factor_id}:")
                for i, assumption in enumerate(factor_assumptions, 1):
                    lines.append(f"  {i}. {assumption['assumption']}")
                lines.append("")
        else:
            lines.append("No assumptions recorded.")
        lines.append("")
        
        # === FINAL SYNTHESIS ===
        lines.append("\n=== FINAL SYNTHESIS ===\n")
        synthesis = result.get('synthesis', {})
        structured = synthesis.get('structured', {})
        
        lines.append("Based ONLY on accepted and partially accepted factors:\n")
        lines.append(structured.get('narrative_summary', synthesis.get('synthesis', 'No synthesis available')))
        lines.append("")
        
        # === SYSTEM INTEGRITY CHECK ===
        lines.append("\n=== SYSTEM INTEGRITY CHECK ===\n")
        integrity_report = result.get('integrity_report', '')
        lines.append(integrity_report)
        
        return "\n".join(lines)
    
    @staticmethod
    def format_compact_summary(result: Dict) -> str:
        """Generate a compact summary of the analysis."""
        validation_results = result.get('validation_results', {})
        resolutions = result.get('resolutions', {})
        integrity = result.get('integrity_check', {})
        
        summary = []
        summary.append("=== ANALYSIS SUMMARY ===\n")
        summary.append(f"Factors Extracted: {validation_results.get('total_factors', 0)}")
        summary.append(f"Valid Factors: {validation_results.get('valid_factors', 0)}")
        summary.append(f"Circular Factors Rejected: {validation_results.get('circular_factors', 0)}")
        summary.append(f"\nResolutions:")
        summary.append(f"  Accepted: {len(resolutions.get('accepted', []))}")
        summary.append(f"  Partially Accepted: {len(resolutions.get('partially_accepted', []))}")
        summary.append(f"  Rejected: {len(resolutions.get('rejected', []))}")
        summary.append(f"\nIntegrity: {'✓ VALID' if integrity.get('synthesis_valid', False) else '✗ INVALID'}")
        
        return "\n".join(summary)
