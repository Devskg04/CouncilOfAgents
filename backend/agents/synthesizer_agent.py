"""
Synthesizer Agent
Observes all debates and extracts insights from both sides.
Produces structured synthesis with mandatory What Worked/Failed sections.
"""

from typing import List, Dict, Set
from .base_agent import BaseAgent
from coordination.message_bus import MessageBus, MessageType
from coordination.agent_registry import AgentRegistry, AgentRole
from coordination.role_policy import RolePolicyEngine
import json
import re


class SynthesizerAgent(BaseAgent):
    """Synthesizes insights from all debates. Reacts to debate completion."""
    
    def __init__(
        self,
        message_bus: MessageBus,
        llm_client,
        registry: AgentRegistry = None,
        policy_engine: RolePolicyEngine = None,
        resolution_tracker=None
    ):
        super().__init__(
            name="SynthesizerAgent",
            agent_id="synthesizer_001",
            role=AgentRole.SYNTHESIZER,
            message_bus=message_bus,
            llm_client=llm_client,
            registry=registry,
            policy_engine=policy_engine
        )
        self.current_input_text: str = ""
        self.synthesis_triggered = False
        self.resolution_tracker = resolution_tracker
    
    def _get_input_types(self) -> Set[str]:
        return {MessageType.REBUTTAL.value}  # Trigger after rebuttals
    
    def _get_output_types(self) -> Set[str]:
        return {MessageType.SYNTHESIS_NOTE.value}
    
    def _get_description(self) -> str:
        return "Synthesizes debate outcomes with structured What Worked/Failed analysis and confidence scores"
    
    def _setup_subscriptions(self):
        """Subscribe to events - could trigger on debate completion."""
        # For now, synthesis is triggered manually by orchestrator
        # Could be enhanced to auto-trigger when all factors have critiques
        pass
    
    async def synthesize(self, input_text: str) -> Dict:
        """Review all debate messages and produce synthesis notes."""
        
        # Get all messages from the coordination layer
        all_messages = self.message_bus.get_all_messages()
        
        # Organize messages by factor
        factors = self.message_bus.get_factors()
        factor_debates = {}
        
        for factor in factors:
            factor_id = factor['id']
            factor_debates[factor_id] = {
                "factor": factor,
                "support": None,
                "critique": None,
                "rebuttal": None
            }
        
        for msg in all_messages:
            if msg['type'] == MessageType.SUPPORT_ARGUMENT.value:
                factor_debates[msg['factor_id']]['support'] = msg
            elif msg['type'] == MessageType.CRITIQUE.value:
                factor_debates[msg['factor_id']]['critique'] = msg
            elif msg['type'] == MessageType.REBUTTAL.value:
                factor_debates[msg['factor_id']]['rebuttal'] = msg
        
        # Filter factors by resolution status
        rejected_factor_ids = set()
        accepted_factor_ids = set()
        partial_factor_ids = set()
        
        if self.resolution_tracker:
            rejected_factor_ids = set(self.resolution_tracker.get_rejected_factors())
            accepted_factor_ids = set(self.resolution_tracker.get_accepted_factors())
            partial_factor_ids = set(self.resolution_tracker.get_partially_accepted_factors())
        
        # Build synthesis prompt - EXCLUDE rejected factors
        debates_text = ""
        rejected_debates_text = ""
        
        for factor_id, debate in factor_debates.items():
            debate_summary = f"\n\nFactor {factor_id}: {debate['factor']['name']}\n"
            if debate['support']:
                debate_summary += f"SUPPORT: {debate['support']['argument'][:500]}\n"
            if debate['critique']:
                debate_summary += f"CRITIQUE: {debate['critique']['argument'][:500]}\n"
                debate_summary += f"RESOLUTION: {debate['critique'].get('resolution', 'UNKNOWN')}\n"
            if debate['rebuttal']:
                debate_summary += f"REBUTTAL: {debate['rebuttal']['rebuttal'][:500]}\n"
            
            # Separate rejected factors
            if factor_id in rejected_factor_ids:
                rejected_debates_text += debate_summary
            else:
                debates_text += debate_summary
        
        prompt = f"""You are the Synthesizer Agent inside Project AETHER. Review all the structured debates below and extract key insights WITHOUT introducing false balance.

Meta-goal: Project AETHER is not a consensus engine. It is a truth-seeking, failure-detecting analytical system.

Original Document:
{input_text[:2000]}

Debate Summary:
{debates_text}

Provide a synthesis that explains:
1. What worked – Which arguments were strongest and why
2. What failed – Which factors or arguments were weakest or analytically rejected, and why
3. Why it happened – Root causes of successes and failures (information sources, incentives, ideology, cognitive bias, etc.)
4. How it can be improved – Recommendations for better analysis and for avoiding invalid or harmful reasoning in the future

Explicitly note any "Analytically Rejected Factors" and summarize why they fail factual and ethical scrutiny.

Format as structured analysis with clear sections. Avoid phrases like "both sides have merit" when evidence clearly supports one conclusion."""

        # Generate structured synthesis with mandatory sections
        structured_prompt = f"""You are the Synthesizer Agent inside Project AETHER. Review all the structured debates below and extract key insights WITHOUT introducing false balance.

Meta-goal: Project AETHER is not a consensus engine. It is a truth-seeking, failure-detecting analytical system.

Original Document:
{input_text[:2000]}

Debate Summary:
{debates_text}

You MUST provide a structured synthesis in JSON format with the following EXACT structure:

{{
  "what_worked": [
    {{"factor_id": <id>, "factor_name": "<name>", "reason": "<why it worked>", "confidence": <0.0-1.0>}},
    ...
  ],
  "what_failed": [
    {{"factor_id": <id>, "factor_name": "<name>", "reason": "<why it failed>", "confidence": <0.0-1.0>}},
    ...
  ],
  "analytically_rejected": [
    {{"factor_id": <id>, "factor_name": "<name>", "rejection_reason": "<why rejected>", "confidence": 1.0}},
    ...
  ],
  "debate_highlights": [
    {{"factor_id": <id>, "highlight_type": "strong_claim|concession|deadlock|breakthrough", "description": "<what happened>"}},
    ...
  ],
  "per_factor_confidence": {{
    "<factor_id>": <0.0-1.0>,
    ...
  }},
  "root_causes": [
    "<root cause 1>",
    "<root cause 2>",
    ...
  ],
  "narrative_summary": "<overall synthesis text>"
}}

Explicitly note any "Analytically Rejected Factors" and summarize why they fail factual and ethical scrutiny.
Avoid phrases like "both sides have merit" when evidence clearly supports one conclusion."""

        response = await self.llm_client.generate(structured_prompt)
        
        # Parse structured response
        structured_data = self._parse_structured_synthesis(response)
        
        # Ensure all mandatory sections exist
        if not structured_data.get('what_worked'):
            structured_data['what_worked'] = []
        if not structured_data.get('what_failed'):
            structured_data['what_failed'] = []
        if not structured_data.get('analytically_rejected'):
            structured_data['analytically_rejected'] = []
        if not structured_data.get('debate_highlights'):
            structured_data['debate_highlights'] = []
        if not structured_data.get('per_factor_confidence'):
            structured_data['per_factor_confidence'] = {}
        
        # Add rejected factors information
        rejected_factors_info = []
        for factor_id in rejected_factor_ids:
            factor = next((f for f in factors if f['id'] == factor_id), None)
            if factor and self.resolution_tracker:
                resolution = self.resolution_tracker.get_resolution(factor_id)
                rejected_factors_info.append({
                    'factor_id': factor_id,
                    'factor_name': factor['name'],
                    'rejection_reason': resolution.get('justification', 'No justification provided') if resolution else 'Unknown'
                })
        
        synthesis = {
            "type": MessageType.SYNTHESIS_NOTE.value,
            "synthesis": structured_data.get('narrative_summary', response),
            "structured": structured_data,
            "debate_summary": debates_text,
            "rejected_factors": rejected_factors_info,
            "rejected_debates": rejected_debates_text,
            "timestamp": self._get_timestamp()
        }
        
        await self._publish(synthesis)
        return synthesis
    
    def _parse_structured_synthesis(self, response: str) -> Dict:
        """Parse structured JSON from LLM response."""
        # Try to extract JSON
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Fallback: return minimal structure
        return {
            "what_worked": [],
            "what_failed": [],
            "analytically_rejected": [],
            "debate_highlights": [],
            "per_factor_confidence": {},
            "root_causes": [],
            "narrative_summary": response
        }

