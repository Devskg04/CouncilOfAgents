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
        output = []
        
        # === FACTOR EXTRACTION ===
        output.append("=== FACTOR EXTRACTION ===\n")
        factors = result.get('factors', [])
        for factor in factors:
            validation = factor.get('validation', {})
            status = "✓" if validation.get('is_valid', True) else "✗"
            output.append(f"{status} Factor {factor['id']}: {factor['name']}")
            output.append(f"   Description: {factor['description']}")
            if not validation.get('is_valid', True):
                if validation.get('is_circular'):
                    output.append(f"   REJECTED: {validation.get('circular_note', 'Circular reasoning')}")
                elif not validation.get('is_grounded'):
                    output.append(f"   REJECTED: {validation.get('grounding_note', 'Not grounded in document')}")
            output.append("")
        
        # === FACTOR VALIDATION ===
        output.append("\n=== FACTOR VALIDATION ===\n")
        validation_results = result.get('validation_results', {})
        if validation_results:
            output.append(f"Total Factors: {validation_results.get('total_factors', 0)}")
            output.append(f"Valid Factors: {validation_results.get('valid_factors', 0)}")
            output.append(f"Grounded Factors: {validation_results.get('grounded_factors', 0)}/{validation_results.get('total_factors', 0)}")
            output.append(f"Circular Factors Detected: {validation_results.get('circular_factors', 0)} (rejected)")
        output.append("")
        
        # === AGENT DEBATE LOG ===
        output.append("\n=== AGENT DEBATE LOG ===\n")
        debates = result.get('debates', {})
        for factor_id, debate in debates.items():
            factor = debate.get('factor', {})
            output.append(f"Factor {factor_id}: {factor.get('name', 'Unknown')}")
            
            # Supporting Agent
            support = debate.get('support')
            if support:
                output.append(f"  Supporting Agent:")
                output.append(f"    {support.get('argument', '')[:200]}...")
                output.append(f"    Evidence Provided: {'Yes' if support.get('has_evidence', True) else 'No'}")
            
            # Critic Agent
            critique = debate.get('critique')
            if critique:
                output.append(f"  Critic Agent:")
                output.append(f"    {critique.get('argument', '')[:200]}...")
                output.append(f"  Resolution: {critique.get('resolution', 'UNKNOWN')}")
                output.append(f"  Justification: {critique.get('justification', 'See critique above')}")
                
                # Sub-claims for PARTIALLY_ACCEPTED
                sub_claims = critique.get('sub_claims', [])
                if sub_claims:
                    output.append(f"  Sub-claims:")
                    for sc in sub_claims:
                        output.append(f"    - {sc['claim']}: {sc['status']}")
            
            output.append("")
        
        # === REJECTED FACTORS (ENFORCED) ===
        output.append("\n=== REJECTED FACTORS (ENFORCED) ===\n")
        resolutions = result.get('resolutions', {})
        rejected_ids = resolutions.get('rejected', [])
        
        if rejected_ids:
            synthesis = result.get('synthesis', {})
            rejected_factors = synthesis.get('rejected_factors', [])
            
            for rejected in rejected_factors:
                output.append(f"Factor {rejected['factor_id']}: {rejected['factor_name']}")
                output.append(f"  Rejection Reason: {rejected['rejection_reason']}")
            
            output.append(f"\n✓ Confirmed: {len(rejected_ids)} rejected factors excluded from synthesis")
        else:
            output.append("No factors were rejected.")
        output.append("")
        
        # === ASSUMPTIONS AUDIT ===
        output.append("\n=== ASSUMPTIONS AUDIT ===\n")
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
                output.append(f"Factor {factor_id}:")
                for i, assumption in enumerate(factor_assumptions, 1):
                    output.append(f"  {i}. {assumption['assumption']}")
                output.append("")
        else:
            output.append("No assumptions recorded.")
        output.append("")
        
        # === FINAL SYNTHESIS ===
        output.append("\n=== FINAL SYNTHESIS ===\n")
        synthesis = result.get('synthesis', {})
        structured = synthesis.get('structured', {})
        
        output.append("Based ONLY on accepted and partially accepted factors:\n")
        output.append(structured.get('narrative_summary', synthesis.get('synthesis', 'No synthesis available')))
        output.append("")
        
        # === SYSTEM INTEGRITY CHECK ===
        output.append("\n=== SYSTEM INTEGRITY CHECK ===\n")
        integrity_report = result.get('integrity_report', '')
        output.append(integrity_report)
        
        return "\n".join(output)
    
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
