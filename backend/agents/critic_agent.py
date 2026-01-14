"""
Critic Agent
Argues AGAINST each factor, identifying flaws, risks, and alternative explanations.
Reactive: automatically responds to support arguments.
"""

from typing import Dict, Set
from .base_agent import BaseAgent
from coordination.message_bus import MessageBus, MessageType
from coordination.agent_registry import AgentRegistry, AgentRole
from coordination.role_policy import RolePolicyEngine
from coordination.claims import Claim, ClaimStatus, EvidenceStrength


class CriticAgent(BaseAgent):
    """Argues against factors, identifying weaknesses. Reacts to support arguments automatically."""
    
    def __init__(
        self,
        message_bus: MessageBus,
        llm_client,
        registry: AgentRegistry = None,
        policy_engine: RolePolicyEngine = None,
        resolution_tracker=None
    ):
        super().__init__(
            name="CriticAgent",
            agent_id="critic_001",
            role=AgentRole.CRITIC,
            message_bus=message_bus,
            llm_client=llm_client,
            registry=registry,
            policy_engine=policy_engine
        )
        self.claims: Dict[int, Claim] = {}  # Track critique claims per factor
        self.current_input_text: str = ""
        self.resolution_tracker = resolution_tracker
    
    def _get_input_types(self) -> Set[str]:
        return {MessageType.SUPPORT_ARGUMENT.value}
    
    def _get_output_types(self) -> Set[str]:
        return {MessageType.CRITIQUE.value}
    
    def _get_description(self) -> str:
        return "Challenges factors and support arguments; identifies flaws and analytically rejects invalid claims"
    
    def _setup_subscriptions(self):
        """Subscribe to support arguments - react automatically."""
        self.message_bus.subscribe(MessageType.SUPPORT_ARGUMENT.value, self._on_support_argument)
    
    async def _on_support_argument(self, message: Dict):
        """React to a support argument - generate critique automatically."""
        # Skip if we already handled this
        message_id = message.get('id')
        if message_id and self.message_bus.is_handled_by(message_id, self.agent_id):
            return
        
        factor_id = message.get('factor_id')
        if not factor_id:
            return
        
        # Get factor and input text
        factor = self.message_bus.get_factor(factor_id)
        if not factor:
            return
        
        input_text = self.current_input_text or message.get('input_text_preview', '')
        
        # Generate critique
        await self.critique_factor(factor, message, input_text)
        
        # Mark as handled
        if message_id:
            self.message_bus.mark_handled(message_id, self.agent_id)
    
    async def critique_factor(self, factor: Dict, support_argument: Dict, input_text: str) -> Dict:
        """Generate critique for a factor and its support argument. Creates structured Claim."""
        self.current_input_text = input_text
        
        # Detect context size for mode selection
        context_size = len(input_text.strip())
        is_small_context = context_size < 500
        
        # Extract supporting agent's claim if available
        support_claim_data = support_argument.get('claim')
        has_evidence = support_argument.get('has_evidence', True)
        
        # Check if factor has validation issues
        factor_validation = factor.get('validation', {})
        is_circular = factor_validation.get('is_circular', False)
        is_grounded = factor_validation.get('is_grounded', True)
        
        # Check if supporting agent conceded in any rebuttal
        has_concession = False
        all_messages = self.message_bus.get_all_messages()
        for msg in all_messages:
            if (msg.get('type') == MessageType.REBUTTAL.value and 
                msg.get('factor_id') == factor['id'] and
                msg.get('is_concession', False)):
                has_concession = True
                break
        
        # Check if this is a simple descriptive fact (before LLM call)
        context_size = len(input_text.strip())
        is_small_context = context_size < 500
        
        factor_desc = factor.get('description', '').lower()
        factor_name = factor.get('name', '').lower()
        
        # Detect if factor makes causal claim
        causal_keywords = ['caused', 'led to', 'resulted in', 'because', 'due to', 'therefore', 'thus', 'consequently']
        is_causal_claim = any(keyword in factor_desc or keyword in factor_name for keyword in causal_keywords)
        
        # Build context-aware prompt
        if is_small_context:
            mode_instruction = """CONTEXT MODE: SMALL/TRIVIAL STATEMENT
- You may use general knowledge and common sense for evaluation
- The statement is too brief for deep documentary analysis
- Apply logical reasoning and well-established facts
- CRITICAL: Do NOT hallucinate or invent counter-facts
- If using general knowledge, state it explicitly: "Based on general knowledge..."
- Still prefer document-based critique when possible"""
        else:
            mode_instruction = """CONTEXT MODE: SUBSTANTIAL DOCUMENT
- You MUST critique using ONLY information from the document
- Do NOT use external knowledge or assumptions
- Every critique must reference document content
- CRITICAL: Do NOT hallucinate or add information not in the document"""
        
        prompt = f"""You are the Critic Agent inside Project AETHER. Your role is to stress-test each factor and, when appropriate, reject it outright.

{mode_instruction}

STRICT RULES:
- ANTI-HALLUCINATION: NEVER invent counter-evidence not present in the source
- NEVER add external information without explicitly stating "Based on general knowledge"
- Be transparent about what comes from the document vs. general knowledge
- Challenge both factual accuracy and moral validity when applicable
- If a factor relies on historically falsified claims, genocide, crimes against humanity, or extremist narratives, explicitly label it as "Analytically Rejected Factor"
- Do NOT simulate false balance: if evidence clearly invalidates a factor, say so directly
- If the Supporting Agent provided INSUFFICIENT_EVIDENCE, you MUST REJECT the factor
- If the factor is circular reasoning (outcome-as-cause), you MUST REJECT it for causal inference

CRITICAL: CAUSALITY vs DESCRIPTION
- If a factor is DESCRIPTIVE (states what happened/exists), it is VALID unless contradicted
- Descriptive facts do NOT require causal mechanisms or justification
- Do NOT reject descriptive facts for "lack of specificity" when none is required
- If a factor claims CAUSALITY (X caused Y), THEN verify causal evidence
- If no causal mechanism is provided for a causal claim, REJECT the causal claim (may accept as descriptive)

ILLEGITIMATE REJECTION CRITERIA (DO NOT USE):
- Do NOT reject for "lack of specificity" if the factor is descriptive
- Do NOT reject for "lack of mechanism" if the factor is not making a causal claim
- Do NOT reject for "lack of evidence" if the factor is a simple descriptive fact from the document
- Do NOT apply epistemic standards inappropriate to the claim type

MANDATORY RESOLUTION:
You MUST provide a clear resolution at the end in this EXACT format:

RESOLUTION: [ACCEPTED | ACCEPTED (DESCRIPTIVE ONLY) | PARTIALLY_ACCEPTED | REJECTED]
JUSTIFICATION: [Clear explanation]

For PARTIALLY_ACCEPTED, you MUST also provide:
SUB-CLAIMS:
- [Sub-claim 1]: ACCEPTED/REJECTED
- [Sub-claim 2]: ACCEPTED/REJECTED

For ACCEPTED (DESCRIPTIVE ONLY):
- State: "This factor describes what happened but does NOT establish causality"

Factor:
ID: {factor['id']}
Name: {factor['name']}
Description: {factor['description']}
Validation Status: {'CIRCULAR - REJECT FOR CAUSALITY' if is_circular else 'UNGROUNDED - MUST REJECT' if not is_grounded else 'Valid for debate'}

Supporting Agent's Argument:
{support_argument.get('argument', 'No argument provided')}
Evidence Provided: {'NO - MUST REJECT' if not has_evidence else 'YES'}

Original Document Context:
{input_text[:2000]}

Provide a critical analysis that:
1. Identifies specific flaws or weaknesses in the factor
2. Points out risks, harms, or negative consequences of accepting this factor
3. Highlights missing assumptions or biases
4. Suggests alternative, more accurate explanations or mechanisms
5. Challenges the evidence or logic presented
6. CRITICAL: If the factor claims causality, verify causal mechanism exists
7. CRITICAL: Distinguish between descriptive facts and causal claims
8. States clearly whether this factor should be ACCEPTED, ACCEPTED (DESCRIPTIVE ONLY), PARTIALLY_ACCEPTED, or REJECTED

CAUSALITY CHECK:
- Does the factor claim "X caused Y" or "X led to Y"?
- If YES: Does the supporting argument provide a causal mechanism?
- If NO mechanism: REJECT the causal claim (may accept as descriptive)

Be thorough and explicit. Challenge the supporting argument point-by-point and avoid diplomatic language when the factor is clearly invalid.

Remember: You MUST end with the RESOLUTION section in the exact format specified above."""

        response = await self.llm_client.generate(prompt)
        
        # Auto-accept descriptive facts in small contexts (skip debate)
        if not is_causal_claim and is_small_context and not (has_concession or is_circular or not is_grounded):
            resolution_str = "ACCEPTED"
            justification = "Descriptive fact from document - accepted without substantive debate"
        # Auto-reject if supporting agent conceded or factor has validation issues
        elif has_concession or is_circular or not is_grounded or not has_evidence:
            resolution_str = "REJECTED"
            if has_concession:
                justification = "Supporting agent conceded - unable to provide documentary evidence"
            elif is_circular:
                justification = f"Circular reasoning detected: {factor_validation.get('circular_note', 'Outcome used as cause')} - REJECTED for causal inference"
            elif not is_grounded:
                justification = f"Factor not grounded in document: {factor_validation.get('grounding_note', 'No evidence in text')}"
            elif not has_evidence:
                justification = "Supporting agent provided insufficient evidence"
            else:
                justification = "Factor failed validation"
        else:
            # Parse resolution from response
            import re
            resolution_match = re.search(r'RESOLUTION:\s*(ACCEPTED(?:\s*\(DESCRIPTIVE ONLY\))?|PARTIALLY_ACCEPTED|REJECTED)', response, re.IGNORECASE)
            justification_match = re.search(r'JUSTIFICATION:\s*(.+?)(?:SUB-CLAIMS:|$)', response, re.DOTALL | re.IGNORECASE)
            
            # Determine resolution
            if resolution_match:
                resolution_str = resolution_match.group(1).upper()
                # Normalize "ACCEPTED (DESCRIPTIVE ONLY)" to just "ACCEPTED" with note
                if "DESCRIPTIVE" in resolution_str:
                    resolution_str = "ACCEPTED"
                    is_descriptive_only = True
                else:
                    is_descriptive_only = False
            else:
                # Fallback: determine from keywords
                if "ANALYTICALLY REJECTED" in response.upper() or "INVALID" in response.upper() or "REJECT" in response.upper():
                    resolution_str = "REJECTED"
                elif "PARTIALLY" in response.upper() or "SOME" in response.upper():
                    resolution_str = "PARTIALLY_ACCEPTED"
                elif "ACCEPT" in response.upper():
                    resolution_str = "ACCEPTED"
                else:
                    resolution_str = "REJECTED"  # Default to rejection if unclear
                is_descriptive_only = False
            
            justification = justification_match.group(1).strip() if justification_match else "See critique above"
            
            # CRITICAL: Check if rebuttal addressed causality challenge
            # If critic raised causality issue and rebuttal only re-quoted, auto-reject
            if "CAUSAL" in response.upper() or "CAUSALITY" in response.upper():
                # Check if there's a rebuttal
                rebuttal_msg = None
                for msg in all_messages:
                    if (msg.get('type') == MessageType.REBUTTAL.value and 
                        msg.get('factor_id') == factor['id']):
                        rebuttal_msg = msg
                        break
                
                if rebuttal_msg:
                    rebuttal_text = rebuttal_msg.get('rebuttal', '').upper()
                    # Check if rebuttal only re-quotes without addressing causality
                    has_causal_mechanism = any(term in rebuttal_text for term in [
                        'MECHANISM', 'BECAUSE', 'THEREFORE', 'THUS', 'CONSEQUENTLY',
                        'LEADS TO', 'RESULTS IN', 'CAUSES'
                    ])
                    
                    if not has_causal_mechanism and 'QUOTE:' in rebuttal_text:
                        # Rebuttal only re-quoted without addressing causality - Critic wins
                        resolution_str = "REJECTED"
                        justification = "Critic raised causality challenge - rebuttal only re-quoted document without providing causal mechanism"
            
            # Add descriptive-only note if applicable
            if is_descriptive_only and resolution_str == "ACCEPTED":
                justification = f"DESCRIPTIVE ONLY: {justification}. This factor describes what happened but does NOT establish causality."
        
        # Parse sub-claims for PARTIALLY_ACCEPTED
        sub_claims = []
        if resolution_str == "PARTIALLY_ACCEPTED":
            subclaims_match = re.search(r'SUB-CLAIMS:(.*?)(?:$)', response, re.DOTALL | re.IGNORECASE)
            if subclaims_match:
                subclaims_text = subclaims_match.group(1)
                subclaim_lines = re.findall(r'-\s*(.+?):\s*(ACCEPTED|REJECTED)', subclaims_text, re.IGNORECASE)
                sub_claims = [
                    {"claim": claim.strip(), "status": status.upper()}
                    for claim, status in subclaim_lines
                ]
        
        # CRITICAL: Validate resolution exists and is valid
        allowed_resolutions = ["ACCEPTED", "PARTIALLY_ACCEPTED", "REJECTED"]
        if resolution_str not in allowed_resolutions:
            # Force to REJECTED if invalid
            resolution_str = "REJECTED"
            justification = f"Invalid resolution detected - defaulting to REJECTED. Original: {resolution_str}"
        
        # Track resolution
        if self.resolution_tracker:
            from validation.resolution_tracker import ResolutionStatus
            status_map = {
                "ACCEPTED": ResolutionStatus.ACCEPTED,
                "PARTIALLY_ACCEPTED": ResolutionStatus.PARTIALLY_ACCEPTED,
                "REJECTED": ResolutionStatus.REJECTED
            }
            self.resolution_tracker.set_resolution(
                factor_id=factor['id'],
                status=status_map[resolution_str],
                justification=justification,
                sub_claims=sub_claims if sub_claims else None,
                critic_agent_id=self.agent_id
            )
        
        # Create structured claim
        factor_id = factor['id']
        claim = Claim(
            claim_id=f"critique_{factor_id}_{self._get_timestamp()}",
            content=response,
            factor_id=factor_id,
            agent_id=self.agent_id
        )
        
        # Determine claim status based on resolution
        if resolution_str == "REJECTED":
            claim.status = ClaimStatus.INVALIDATED
            claim.confidence = 0.9
        elif resolution_str == "PARTIALLY_ACCEPTED":
            claim.status = ClaimStatus.WEAKENED
            claim.confidence = 0.5
        else:  # ACCEPTED
            claim.status = ClaimStatus.CHALLENGED
            claim.confidence = 0.7
        
        # Link to supporting agent's claim if available
        if support_claim_data:
            support_claim_id = support_claim_data.get('claim_id')
            if support_claim_id:
                claim.challenges.append(support_claim_id)
        
        self.claims[factor_id] = claim
        
        critique = {
            "type": MessageType.CRITIQUE.value,
            "factor_id": factor['id'],
            "factor_name": factor['name'],
            "responding_to": support_argument.get('agent_id', 'SupportingAgent'),
            "argument": response,
            "claim": claim.to_dict(),
            "resolution": resolution_str,
            "justification": justification,
            "sub_claims": sub_claims,
            "verdict": resolution_str,  # Keep for backward compatibility
            "timestamp": self._get_timestamp()
        }
        
        await self._publish(critique)
        return critique
