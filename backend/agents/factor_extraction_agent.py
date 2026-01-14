"""
Factor Extraction Agent
Identifies and lists all key factors, variables, or dimensions in the input.
Self-deploys and reacts to analysis requests.
"""

from typing import List, Dict, Set
from .base_agent import BaseAgent
from coordination.message_bus import MessageBus, MessageType
from coordination.agent_registry import AgentRegistry, AgentRole
from coordination.role_policy import RolePolicyEngine


class FactorExtractionAgent(BaseAgent):
    """Extracts key factors from input documents."""
    
    def __init__(
        self,
        message_bus: MessageBus,
        llm_client,
        registry: AgentRegistry = None,
        policy_engine: RolePolicyEngine = None,
        factor_validator=None
    ):
        super().__init__(
            name="FactorExtractionAgent",
            agent_id="factor_extraction_001",
            role=AgentRole.FACTOR_EXTRACTION,
            message_bus=message_bus,
            llm_client=llm_client,
            registry=registry,
            policy_engine=policy_engine
        )
        self.current_input_text: str = ""
        self.factor_validator = factor_validator
    
    def _get_input_types(self) -> Set[str]:
        """This agent doesn't subscribe to events - it's triggered directly."""
        return set()
    
    def _get_output_types(self) -> Set[str]:
        return {MessageType.FACTOR_LIST.value, MessageType.FACTOR_DISCOVERED.value}
    
    def _get_description(self) -> str:
        return "Extracts causal, testable factors explaining belief formation and persistence"
    
    async def process(self, input_text: str) -> List[Dict]:
        """Extract factors from input and broadcast via Coordination Layer."""
        
        prompt = f"""You are the Factor Extraction Agent inside Project AETHER.

CRITICAL RULE: Extract ONLY factors that appear EXPLICITLY in the document with EXACT QUOTES.

STRICT REQUIREMENTS:
1. You MUST provide an exact quote from the document for each factor
2. Do NOT infer, extrapolate, or add external knowledge
3. Do NOT extract factors based on "reasonable assumptions" or "implied" concepts
4. If a concept is not explicitly mentioned in the document, do NOT include it
5. The factor name and description must be derived ONLY from the quoted text
6. Do NOT create "Analytically Rejected Factor" entries - extract only what exists

For each factor, you MUST provide:
- QUOTE: Exact verbatim text from the document (copy-paste)
- NAME: Short name derived ONLY from the quote
- DESCRIPTION: Explanation using ONLY information in the quote

Document:
{input_text}

Output as JSON array with this EXACT structure:
[
  {{
    "id": 1,
    "quote": "exact verbatim text from document",
    "name": "Factor Name (from quote only)",
    "description": "Explanation using only quote content"
  }},
  {{
    "id": 2,
    "quote": "another exact quote",
    "name": "Another Factor",
    "description": "Description from quote only"
  }}
]

Extract 3-8 factors. Each MUST have a verifiable quote from the document.
"""

        response = await self.llm_client.generate(prompt)
        factors = self._parse_factors(response)
        
        # Store input text for reference
        self.current_input_text = input_text
        
        # Validate factors if validator is available
        validation_results = None
        if self.factor_validator:
            validation_results = self.factor_validator.validate_factor_list(factors, input_text)
            
            # Add validation metadata to each factor
            for factor in factors:
                factor_id = factor['id']
                validation = next(
                    (v for v in validation_results['factor_validations'] if v['factor_id'] == factor_id),
                    None
                )
                if validation:
                    factor['validation'] = {
                        'is_grounded': validation['is_grounded'],
                        'is_circular': validation['is_circular'],
                        'is_valid': validation['is_valid'],
                        'grounding_note': validation['grounding_note'],
                        'circular_note': validation['circular_note']
                    }
        
        # CRITICAL: Validate quotes exist in document
        for factor in factors:
            quote = factor.get('quote', '')
            if quote:
                # Check if quote actually appears in document
                if quote.lower() not in input_text.lower():
                    # Mark as invalid - hallucinated quote
                    if 'validation' not in factor:
                        factor['validation'] = {}
                    factor['validation']['is_valid'] = False
                    factor['validation']['is_grounded'] = False
                    factor['validation']['grounding_note'] = f"HALLUCINATION: Quote not found in document"
            else:
                # No quote provided - mark as invalid
                if 'validation' not in factor:
                    factor['validation'] = {}
                factor['validation']['is_valid'] = False
                factor['validation']['is_grounded'] = False
                factor['validation']['grounding_note'] = "No quote provided"

        
        # Broadcast factors via Coordination Layer (event-driven)
        await self._publish({
            "type": MessageType.FACTOR_LIST.value,
            "factors": factors,
            "validation_results": validation_results,
            "input_text_preview": input_text[:500],
            "timestamp": self._get_timestamp()
        })
        
        return factors
    
    def _parse_factors(self, response: str) -> List[Dict]:
        """Parse LLM response into structured factor list."""
        import json
        import re
        
        # Try to extract JSON from response
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            try:
                factors = json.loads(json_match.group())
                # Ensure all factors have required fields
                for i, factor in enumerate(factors, 1):
                    if "id" not in factor:
                        factor["id"] = i
                    if "name" not in factor:
                        factor["name"] = f"Factor {i}"
                    if "description" not in factor:
                        factor["description"] = "No description provided"
                return factors
            except json.JSONDecodeError:
                pass
        
        # Fallback: parse numbered list
        factors = []
        lines = response.split('\n')
        current_id = 1
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Match numbered list patterns
            match = re.match(r'^(\d+)[\.\)]\s*(.+?)(?:[:]\s*(.+))?$', line)
            if match:
                num, name, desc = match.groups()
                factors.append({
                    "id": int(num),
                    "name": name.strip(),
                    "description": (desc or name).strip()
                })
                current_id = int(num) + 1
        
        # If no structured format found, create single factor
        if not factors:
            factors = [{
                "id": 1,
                "name": "Primary Analysis Factor",
                "description": response[:200]
            }]
        
        return factors

