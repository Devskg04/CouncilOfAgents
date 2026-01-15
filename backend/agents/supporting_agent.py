"""
Supporting Agent
Argues IN FAVOR of each factor's effectiveness or positive impact.
Reactive: automatically responds to factor discoveries and critiques.
"""

from typing import Dict, Set
from .base_agent import BaseAgent
from coordination.message_bus import MessageBus, MessageType
from coordination.agent_registry import AgentRegistry, AgentRole
from coordination.role_policy import RolePolicyEngine
from coordination.claims import Claim, ClaimStatus, EvidenceStrength


class SupportingAgent(BaseAgent):
    """Argues in favor of factors. Reacts to events automatically."""
    
    def __init__(
        self,
        message_bus: MessageBus,
        llm_client,
        registry: AgentRegistry = None,
        policy_engine: RolePolicyEngine = None,
        assumption_tracker=None,
        resolution_tracker=None
    ):
        super().__init__(
            name="SupportingAgent",
            agent_id="supporting_001",
            role=AgentRole.SUPPORTING,
            message_bus=message_bus,
            llm_client=llm_client,
            registry=registry,
            policy_engine=policy_engine
        )
        self.rebuttals_issued = {}  # Track rebuttals per factor (can issue multiple)
        self.claims: Dict[int, Claim] = {}  # Track claims per factor
        self.current_input_text: str = ""
        self.assumption_tracker = assumption_tracker
        self.resolution_tracker = resolution_tracker
    
    def _get_input_types(self) -> Set[str]:
        return {MessageType.FACTOR_DISCOVERED.value, MessageType.CRITIQUE.value}
    
    def _get_output_types(self) -> Set[str]:
        return {MessageType.SUPPORT_ARGUMENT.value, MessageType.REBUTTAL.value}
    
    def _get_description(self) -> str:
        return "Defends mechanisms explaining belief formation; reacts to factors and critiques dynamically"
    
    def _setup_subscriptions(self):
        """Subscribe to events this agent reacts to."""
        # React to factor discoveries
        self.message_bus.subscribe(MessageType.FACTOR_DISCOVERED.value, self._on_factor_discovered)
        # React to critiques (dynamic rebuttals)
        self.message_bus.subscribe(MessageType.CRITIQUE.value, self._on_critique)
    
    async def _on_factor_discovered(self, message: Dict):
        """React to a factor being discovered - generate support automatically."""
        # Skip if we already handled this
        message_id = message.get('id')
        if message_id and self.message_bus.is_handled_by(message_id, self.agent_id):
            return
        
        factor = message.get('factor')
        if not factor:
            return
        
        factor_id = factor.get('id')
        if not factor_id:
            return
        
        # Get input text from context (stored by orchestrator or factor agent)
        input_text = self.current_input_text or message.get('input_text_preview', '')
        
        # Generate support
        await self.support_factor(factor, input_text)
        
        # Mark as handled
        if message_id:
            self.message_bus.mark_handled(message_id, self.agent_id)
    
    async def _on_critique(self, message: Dict):
        """React to a critique - generate rebuttal dynamically."""
        factor_id = message.get('factor_id')
        if not factor_id:
            return
        
        # Check if we have a claim for this factor
        if factor_id not in self.claims:
            return  # No claim to defend
        
        # Get input text
        input_text = self.current_input_text or message.get('input_text_preview', '')
        
        # Generate rebuttal (can issue multiple rebuttals)
        await self.rebut(factor_id, message, input_text)
    
    async def support_factor(self, factor: Dict, input_text: str) -> Dict:
        """Generate supporting arguments for a factor. Creates a structured Claim."""
        self.current_input_text = input_text
        
        # Detect context size for mode selection
        context_size = len(input_text.strip())
        is_small_context = context_size < 500
        
        # Build context-aware prompt
        if is_small_context:
            mode_instruction = """CONTEXT MODE: SMALL/TRIVIAL STATEMENT
- You may use general knowledge and common sense
- The statement is too brief for deep documentary analysis
- Focus on well-established facts and logical reasoning
- CRITICAL: Do NOT hallucinate or invent facts
- If using general knowledge, state it explicitly: "Based on general knowledge..."
- Still prefer document quotes when available"""
        else:
            mode_instruction = """CONTEXT MODE: SUBSTANTIAL DOCUMENT
- You MUST use ONLY information from the document
- Do NOT use external knowledge or assumptions
- Every claim must be backed by document quotes
- CRITICAL: Do NOT hallucinate or add information not in the document"""
        
        prompt = f"""You are the Supporting Agent in Project AETHER.

{mode_instruction}

Your role: Explain why this factor is important for understanding the situation.

Factor:
ID: {factor['id']}
Name: {factor['name']}
Description: {factor['description']}

Document (first 1000 chars):
{input_text[:1000]}

=== REQUIRED FORMAT ===

Provide EXACTLY 2 BULLET POINTS supporting this factor:

• [First supporting point with specific evidence/quote]
• [Second supporting point with specific evidence/quote]

If no evidence available:
INSUFFICIENT_EVIDENCE: [Brief explanation]

CRITICAL RULES:
- Use bullet points (•) for each argument
- EXACTLY 2 bullets - no more, no less
- Each bullet: 1-2 sentences maximum
- Include specific quotes or references
- Be concise and accurate
- No hallucination - only use what's in the document
"""

        response = await self.llm_client.generate(prompt)
        
        # Check for insufficient evidence
        if "INSUFFICIENT_EVIDENCE" in response:
            # Track this as a weak claim
            factor_id = factor['id']
            claim = Claim(
                claim_id=f"support_{factor_id}_{self._get_timestamp()}",
                content=response,
                factor_id=factor_id,
                agent_id=self.agent_id
            )
            claim.confidence = 0.2
            claim.status = ClaimStatus.WEAKENED
            self.claims[factor_id] = claim
            
            argument = {
                "type": MessageType.SUPPORT_ARGUMENT.value,
                "factor_id": factor['id'],
                "factor_name": factor['name'],
                "argument": response,
                "claim": claim.to_dict(),
                "has_evidence": False,
                "timestamp": self._get_timestamp()
            }
            
            await self._publish(argument)
            return argument
        
        # Extract assumptions from response
        import re
        assumptions_match = re.search(r'ASSUMPTIONS:(.*?)(?:ANALYSIS:|$)', response, re.DOTALL)
        if assumptions_match and self.assumption_tracker:
            assumptions_text = assumptions_match.group(1).strip()
            assumption_lines = [
                line.strip() for line in assumptions_text.split('\n')
                if line.strip() and not line.strip().startswith('#')
            ]
            
            for assumption_line in assumption_lines:
                # Remove numbering
                assumption = re.sub(r'^\d+\.\s*', '', assumption_line)
                if assumption:
                    self.assumption_tracker.register_assumption(
                        agent_id=self.agent_id,
                        factor_id=factor['id'],
                        assumption=assumption,
                        context=f"Supporting argument for factor: {factor['name']}",
                        resolution_tracker=getattr(self, 'resolution_tracker', None)
                    )
        
        # Create structured claim
        factor_id = factor['id']
        claim = Claim(
            claim_id=f"support_{factor_id}_{self._get_timestamp()}",
            content=response,
            factor_id=factor_id,
            agent_id=self.agent_id
        )
        
        # Extract assumptions and evidence from response (simplified - could be enhanced with LLM parsing)
        # For now, we'll store the full response as content
        claim.confidence = 0.7  # Default confidence
        claim.status = ClaimStatus.SUPPORTED
        
        self.claims[factor_id] = claim
        
        argument = {
            "type": MessageType.SUPPORT_ARGUMENT.value,
            "factor_id": factor['id'],
            "factor_name": factor['name'],
            "argument": response,
            "claim": claim.to_dict(),
            "has_evidence": True,
            "timestamp": self._get_timestamp()
        }
        
        await self._publish(argument)
        return argument
    
    async def rebut(self, factor_id: int, critique: Dict, input_text: str) -> Dict:
        """Issue rebuttal dynamically in response to critique. Can issue multiple rebuttals."""
        
        # Get our original claim
        if factor_id not in self.claims:
            return None  # No claim to defend
        
        claim = self.claims[factor_id]
        
        prompt = f"""You are the Supporting Agent. The Critic challenged your argument.

CRITICAL: You MUST provide an exact QUOTE from the document or CONCEDE.

Factor: {self.message_bus.get_factor(factor_id).get('name', '')}

Your Original Argument:
{claim.content[:300]}

Critic's Challenge:
{critique.get('argument', '')[:300]}

Document (first 1000 chars):
{input_text[:1000]}

=== REQUIRED FORMAT ===

Provide EXACTLY 2 BULLET POINTS addressing the critique:

• [First rebuttal point with specific quote/evidence]
• [Second rebuttal point addressing critique directly]

OR if you cannot provide documentary evidence:

CONCEDE: Unable to provide documentary evidence
REASON: [One sentence explaining why]

CRITICAL RULES:
- Use bullet points (•) for each rebuttal
- EXACTLY 2 bullets - no more, no less
- Each bullet: 1-2 sentences with SPECIFIC QUOTES
- Address the critique DIRECTLY
- If no documentary evidence exists, you MUST concede
- No vague statements - be specific
"""
        response = await self.llm_client.generate(prompt)
        
        # Check if conceded or no quote provided
        is_concession = "CONCEDE" in response.upper() or "QUOTE:" not in response.upper()
        
        # Update claim with rebuttal
        rebuttal_id = f"rebuttal_{factor_id}_{len(self.rebuttals_issued.get(factor_id, []))}"
        claim.rebuttals.append(rebuttal_id)
        
        # Track rebuttals
        if factor_id not in self.rebuttals_issued:
            self.rebuttals_issued[factor_id] = []
        self.rebuttals_issued[factor_id].append(rebuttal_id)
        
        # If conceded, mark claim as weakened
        if is_concession:
            claim.weaken("Unable to provide documentary evidence - conceded to critic")
        
        rebuttal = {
            "type": MessageType.REBUTTAL.value,
            "factor_id": factor_id,
            "responding_to": critique.get('agent_id', 'CriticAgent'),
            "rebuttal": response,
            "rebuttal_id": rebuttal_id,
            "claim_id": claim.claim_id,
            "updated_claim": claim.to_dict(),
            "is_concession": is_concession,
            "timestamp": self._get_timestamp()
        }
        
        await self._publish(rebuttal)
        return rebuttal
