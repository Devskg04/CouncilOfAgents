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
        
        prompt = f"""You are the Supporting Agent inside Project AETHER.
Your role is to explore how and why a factor might appear compelling, but you are NOT allowed to legitimize historically false, genocidal, or extremist claims.

STRICT EVIDENCE REQUIREMENTS:
- You MUST provide specific evidence from the document
- You MUST explicitly list all assumptions underlying your argument
- You MUST provide testable predictions if this factor is valid
- If you cannot provide evidence beyond assertion, you MUST state "INSUFFICIENT_EVIDENCE"

STRICT RULES:
- You may defend only the mechanism (how belief forms or why someone might rely on this factor), NOT the truth, morality, or legitimacy of any claim that involves crimes against humanity or clearly falsified history.
- If the factor is an "Analytically Rejected Factor", focus solely on explaining how someone could be persuaded by it (misinformation channels, ideology, cognitive bias), while explicitly stating that the underlying claim remains invalid.

Factor:
ID: {factor['id']}
Name: {factor['name']}
Description: {factor['description']}

Original Document Context:
{input_text[:2000]}

Provide a strong, evidence-based analysis in this EXACT format:

EVIDENCE FROM DOCUMENT:
[List specific quotes or references from the document]

ASSUMPTIONS:
1. [Explicit assumption 1]
2. [Explicit assumption 2]
...

ANALYSIS:
[Why this factor is important for understanding belief formation or outcomes]
[Evidence or logic for why people might rely on it]
[Examples or scenarios where this factor shapes interpretation or behavior]

TESTABLE PREDICTIONS:
[What would we observe if this factor is valid?]

If you cannot provide specific evidence from the document, respond with:
INSUFFICIENT_EVIDENCE: [Explanation of why evidence is lacking]
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
        
        prompt = f"""You are the Supporting Agent inside Project AETHER. You have been challenged by the Critic Agent.

CRITICAL REQUIREMENT: Your rebuttal MUST include an exact QUOTE from the document or you MUST CONCEDE.

STRICT RULES:
1. You MUST provide an exact quote from the document that supports your position
2. If you cannot provide a quote, you MUST state: "CONCEDE: Unable to provide documentary evidence"
3. Do NOT redefine the factor
4. Do NOT shift definitions
5. Do NOT appeal to "intent" without evidence
6. Do NOT use assertions without quotes

Original Factor:
{self.message_bus.get_factor(factor_id)}

Your Original Claim:
{claim.content[:1000]}

Critic's Challenge:
{critique.get('argument', '')}

Original Document:
{input_text[:2000]}

Provide your rebuttal in this format:

QUOTE: "exact text from document"

REBUTTAL:
[Your response addressing the critic's concerns using the quote as evidence]

If you cannot provide a quote, respond with:
CONCEDE: Unable to provide documentary evidence
REASON: [Why you cannot provide evidence]
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
