"""
Factor Validator
Validates factors against document content and detects circular reasoning.
"""

import re
from typing import List, Dict, Tuple


class FactorValidator:
    """Validates factors to ensure they are grounded in the document and not circular."""
    
    # Patterns that indicate circular reasoning (outcome-as-cause)
    CIRCULAR_PATTERNS = [
        r'\btrade-?off(s)?\b',
        r'\bbalance(s)?\b',
        r'\boutcome(s)?\b',
        r'\bresult(s)?\b',
        r'\bconsequence(s)?\b',
        r'\beffect(s)?\b',
        r'\bimpact(s)?\b',
        r'\bchallenge(s)?\b',
        r'\bissue(s)?\b',
        r'\bproblem(s)?\b'
    ]
    
    # Whitelist: Valid uses of these terms that are NOT circular
    WHITELIST_PATTERNS = [
        r'information source',
        r'institutional incentive',
        r'ideological frame',
        r'material condition',
        r'cognitive bias',
        r'resource constraint',
        r'structural barrier'
    ]
    
    def __init__(self):
        self.validation_results = []
    
    def validate_factor_grounding(self, factor: Dict, document: str) -> Tuple[bool, str]:
        """
        Validate that a factor is grounded in the document.
        
        Args:
            factor: Factor dict with 'name' and 'description'
            document: Original document text
            
        Returns:
            (is_grounded, validation_note)
        """
        factor_name = factor.get('name', '')
        factor_desc = factor.get('description', '')
        
        # Extract key terms from factor name (ignore common words)
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        key_terms = [
            word.lower() for word in re.findall(r'\b\w+\b', factor_name)
            if word.lower() not in common_words and len(word) > 3
        ]
        
        if not key_terms:
            return False, "Factor name contains no meaningful terms"
        
        # Check if at least 50% of key terms appear in document
        document_lower = document.lower()
        found_terms = [term for term in key_terms if term in document_lower]
        
        grounding_ratio = len(found_terms) / len(key_terms) if key_terms else 0
        
        if grounding_ratio >= 0.5:
            return True, f"Grounded: {len(found_terms)}/{len(key_terms)} key terms found in document"
        else:
            return False, f"Not grounded: Only {len(found_terms)}/{len(key_terms)} key terms found in document"
    
    def detect_circular_reasoning(self, factor: Dict) -> Tuple[bool, str]:
        """
        Detect if a factor represents circular reasoning (outcome-as-cause).
        
        Args:
            factor: Factor dict with 'name' and 'description'
            
        Returns:
            (is_circular, detection_note)
        """
        factor_name = factor.get('name', '').lower()
        factor_desc = factor.get('description', '').lower()
        combined_text = f"{factor_name} {factor_desc}"
        
        # Check whitelist first (valid uses)
        for whitelist_pattern in self.WHITELIST_PATTERNS:
            if re.search(whitelist_pattern, combined_text, re.IGNORECASE):
                return False, "Valid causal factor (whitelisted pattern)"
        
        # Check for circular patterns
        detected_patterns = []
        for pattern in self.CIRCULAR_PATTERNS:
            if re.search(pattern, combined_text, re.IGNORECASE):
                detected_patterns.append(pattern.replace(r'\b', '').replace('?', '').replace('(s)', ''))
        
        if detected_patterns:
            # Additional check: Does the description explain a mechanism?
            mechanism_indicators = [
                r'because', r'causes?', r'leads? to', r'results? in',
                r'influences?', r'affects?', r'drives?', r'produces?',
                r'creates?', r'generates?'
            ]
            has_mechanism = any(re.search(ind, factor_desc) for ind in mechanism_indicators)
            
            if has_mechanism:
                return False, f"Contains outcome terms ({', '.join(detected_patterns)}) but explains causal mechanism"
            else:
                return True, f"CIRCULAR: Describes outcome ({', '.join(detected_patterns)}) not cause"
        
        return False, "No circular reasoning detected"
    
    def validate_factor_list(self, factors: List[Dict], document: str) -> Dict:
        """
        Validate a list of factors.
        
        Args:
            factors: List of factor dicts
            document: Original document text
            
        Returns:
            Validation summary dict
        """
        results = {
            'total_factors': len(factors),
            'grounded_factors': 0,
            'ungrounded_factors': 0,
            'circular_factors': 0,
            'valid_factors': 0,
            'factor_validations': []
        }
        
        for factor in factors:
            is_grounded, grounding_note = self.validate_factor_grounding(factor, document)
            is_circular, circular_note = self.detect_circular_reasoning(factor)
            
            is_valid = is_grounded and not is_circular
            
            validation = {
                'factor_id': factor.get('id'),
                'factor_name': factor.get('name'),
                'is_grounded': is_grounded,
                'grounding_note': grounding_note,
                'is_circular': is_circular,
                'circular_note': circular_note,
                'is_valid': is_valid
            }
            
            results['factor_validations'].append(validation)
            
            if is_grounded:
                results['grounded_factors'] += 1
            else:
                results['ungrounded_factors'] += 1
            
            if is_circular:
                results['circular_factors'] += 1
            
            if is_valid:
                results['valid_factors'] += 1
        
        return results
    
    def get_validation_report(self, validation_results: Dict) -> str:
        """Generate a human-readable validation report."""
        report = "=== FACTOR VALIDATION REPORT ===\n\n"
        report += f"Total Factors: {validation_results['total_factors']}\n"
        report += f"Valid Factors: {validation_results['valid_factors']}\n"
        report += f"Grounded Factors: {validation_results['grounded_factors']}\n"
        report += f"Ungrounded Factors: {validation_results['ungrounded_factors']}\n"
        report += f"Circular Factors (Rejected): {validation_results['circular_factors']}\n\n"
        
        if validation_results['circular_factors'] > 0:
            report += "CIRCULAR FACTORS DETECTED:\n"
            for val in validation_results['factor_validations']:
                if val['is_circular']:
                    report += f"  - Factor {val['factor_id']}: {val['factor_name']}\n"
                    report += f"    Reason: {val['circular_note']}\n"
            report += "\n"
        
        if validation_results['ungrounded_factors'] > 0:
            report += "UNGROUNDED FACTORS DETECTED:\n"
            for val in validation_results['factor_validations']:
                if not val['is_grounded']:
                    report += f"  - Factor {val['factor_id']}: {val['factor_name']}\n"
                    report += f"    Reason: {val['grounding_note']}\n"
            report += "\n"
        
        return report
