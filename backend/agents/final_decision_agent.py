"""
Final Decision Agent
Produces ONE unified, structured final report with decisive verdicts.
"""

from typing import Dict, Set, List
from .base_agent import BaseAgent
from coordination.message_bus import MessageBus, MessageType
from coordination.agent_registry import AgentRegistry, AgentRole
from coordination.role_policy import RolePolicyEngine
import json
import re


class FinalDecisionAgent(BaseAgent):
    """Generates the final unified report with mandatory decisive verdict."""
    
    def __init__(
        self,
        message_bus: MessageBus,
        llm_client,
        registry: AgentRegistry = None,
        policy_engine: RolePolicyEngine = None
    ):
        super().__init__(
            name="FinalDecisionAgent",
            agent_id="final_decision_001",
            role=AgentRole.FINAL_DECISION,
            message_bus=message_bus,
            llm_client=llm_client,
            registry=registry,
            policy_engine=policy_engine
        )
    
    def _get_input_types(self) -> Set[str]:
        return {MessageType.SYNTHESIS_NOTE.value}
    
    def _get_output_types(self) -> Set[str]:
        return {MessageType.FINAL_DIRECTIVE.value}
    
    def _get_description(self) -> str:
        return "Generates final decisive report with structured verdict and confidence scoring"
    
    def _setup_subscriptions(self):
        """Subscribe to synthesis completion."""
        self.message_bus.subscribe(MessageType.SYNTHESIS_NOTE.value, self._on_synthesis_complete)
    
    async def _on_synthesis_complete(self, message: Dict):
        """React to synthesis - generate final report automatically."""
        # This could be auto-triggered, but for now we'll keep manual trigger
        # to ensure orchestrator controls timing
        pass
    
    async def generate_final_report(self, input_text: str) -> Dict:
        """Generate the final structured report with explicit factor listing and debate log."""
        
        # Collect all information
        factors = self.message_bus.get_factors()
        all_messages = self.message_bus.get_all_messages()
        synthesis = None
        
        for msg in all_messages:
            if msg['type'] == MessageType.SYNTHESIS_NOTE.value:
                synthesis = msg
                break
        
        # Build comprehensive debate log per factor
        debate_log = self._build_debate_log(factors, all_messages)
        
        # Identify failed/weak/rejected factors
        factor_outcomes = self._classify_factor_outcomes(factors, all_messages, debate_log)
        
        # Build comprehensive context
        factors_text = "\n".join([
            f"{f['id']}. {f['name']}: {f['description']}"
            for f in factors
        ])
        
        synthesis_text = synthesis.get('synthesis', 'No synthesis available') if synthesis else "No synthesis available"
        structured_synthesis = synthesis.get('structured', {}) if synthesis else {}
        
        prompt = f"""You are the Final Decision Agent inside Project AETHER. You are the ONLY agent allowed to generate the final answer.

Meta-rules (MANDATORY):
- Project AETHER is not a consensus engine; it is a truth-seeking, failure-detecting analytical system.
- Do NOT assume moral or factual symmetry between opposing viewpoints.
- When the text involves historically falsified claims, genocide, crimes against humanity, or extremist/totalitarian narratives, you MUST explicitly reject them as false and ethically indefensible.
- You must identify invalid premises and reject false conclusions using evidence-based reasoning.
- Diplomatic language ("both sides have merit", "no clear answer") is forbidden when evidence is decisive.

Original Document:
{input_text}

Key Factors Identified:
{factors_text}

Synthesis Notes:
{synthesis_text}

Generate a comprehensive final report following this EXACT structure:

=== PROJECT AETHER FINAL REPORT ===

1. Problem Overview
   [Brief summary of the problem/issue analyzed]

2. Key Factors Identified
   [List and briefly describe all key factors]

3. Debate Summary (Pros vs Cons)
   [For each major factor, summarize the supporting arguments vs critiques]

4. Root Cause Analysis
   [Identify underlying causes and patterns]

5. What Worked
   [What aspects of the analysis or factors were strongest]

6. What Failed
   [What aspects were weak or problematic]

7. Why It Happened
   [Explain the reasons behind successes and failures]

8. Actionable Recommendations
   [Specific, actionable steps or decisions]

9. Risks & Limitations
   [Identify risks and acknowledge limitations]

10. Final Verdict
    [Provide a clear, decisive conclusion that:
     - States whether the core claims in the document are factually valid or invalid
     - Identifies any false or unethical assumptions
     - Explains why any harmful or revisionist narratives are rejected
     - Distinguishes between explaining how beliefs form and endorsing those beliefs
     - States your confidence level]

==================================

IMPORTANT:
- Do NOT repeat agent outputs verbatim.
- Integrate insights and resolve conflicts; avoid "on the one hand / on the other hand" when evidence is one-sided.
- Be transparent about confidence levels.
- Make it actionable and clear.
- If the evidence is genuinely inconclusive, you may say so, but you must explain WHY it is inconclusive. Otherwise, you must provide a definite verdict on validity."""

        # Identify rejected factors
        rejected_factor_ids = {fid for fid, log in debate_log.items() if log.get('is_rejected', False)}
        
        # Generate final report in the EXACT required format
        prompt = f"""You are the Final Decision Agent inside Project AETHER. Generate the final report in the EXACT format specified below.

CRITICAL REQUIREMENTS (VIOLATIONS CAUSE SYSTEM FAILURE):

1. REJECTED FACTORS MUST BE EXCLUDED FROM FINAL SYNTHESIS:
   - Factors marked REJECTED (IDs: {list(rejected_factor_ids)}) MUST NOT influence your final recommendations or positive reasoning.
   - You may ONLY reference them to explain why they were rejected.
   - If you mention a rejected factor in synthesis, you MUST state: "This factor was REJECTED and does NOT contribute to the final decision because..."

2. Explicitly list ALL extracted factors.

3. For EACH factor, show:
   a) Supporting Agent argument (max 2 bullet points)
   b) Critic Agent counter-argument (max 2 bullet points)
   c) Direct rebuttal or concession

4. Explicitly identify:
   - Factors that FAILED due to weak evidence or assumptions
   - Factors that were PARTIALLY ACCEPTED and why
   - Factors that were REJECTED and why (with rejecting agent and reason)

5. Do NOT merge agent opinions prematurely.

6. Do NOT hide disagreement.

7. If a factor is mentioned in the final decision, it MUST appear in the debate section first.

8. If a factor is discarded, explicitly state which agent rejected it and on what grounds.

9. The final synthesis MUST justify why alternative decisions were NOT chosen.

10. Circular factors (outcomes used as causes) MUST be rejected.

11. If a rebuttal relies on assertion instead of specific evidence, the Critic WINS (factor rejected or weakened accordingly).

12. ALL assumptions must be explicitly listed in the final synthesis section.

13. If ANY rule above is violated, mark synthesis as INVALID and explain why.

Original Document:
{input_text[:2000]}

Debate Data:
{self._format_debate_log(debate_log)}

Failed/Weak Factors:
{self._format_failed_factors(factor_outcomes)}

Synthesis Context:
{synthesis_text[:1000]}

You MUST generate a report in this EXACT format (copy the structure exactly):

=== FACTOR EXTRACTION ===
[List ALL factors here - one per line with ID, name, and description]

=== AGENT DEBATE LOG ===
Factor 1:
- Supporting Agent:
  [Full supporting argument text]
- Critic Agent:
  [Full critique text]
- Resolution:
  [REBUTTAL: rebuttal text if present, or CONCEDED, or status]

Factor 2:
- Supporting Agent:
  [Full supporting argument text]
- Critic Agent:
  [Full critique text]
- Resolution:
  [REBUTTAL: rebuttal text if present, or CONCEDED, or status]

[Continue for ALL factors]

=== FAILED / WEAK FACTORS ===
[List factors that did not hold up, with reasons]
- Factor X: [reason it failed/weakened/rejected]
- Factor Y: [reason]

=== FINAL SYNTHESIS ===
[Unified decision with justification that:
- States clearly what is true, false, valid, or invalid
- Explains why one position fails, not merely that disagreement exists
- Prioritizes correctness over neutrality
- Justifies why alternative decisions were NOT chosen
- Distinguishes between explaining belief formation and endorsing beliefs
- Provides confidence level (0.0-1.0)
- CRITICAL: Do NOT use REJECTED factors (IDs: {list(rejected_factor_ids)}) as support for your conclusions. If you mention them, state they were REJECTED and do NOT contribute to the decision.]

=== SELF-CHECK ===
- Did any factor bypass debate? (Yes/No - list any that did)
- Did any conclusion rely on unstated assumptions? (List them)
- Did the system collapse to summarization? (Yes/No - explain)

Generate the complete report following this EXACT format. Include ALL factors in the debate log. Do NOT skip any section."""

        response = await self.llm_client.generate(prompt)
        
        # Generate self-check section with actual data (async)
        self_check_data = await self._generate_self_check(factors, debate_log, all_messages, input_text)
        self_check_text = self._format_self_check(self_check_data)
        
        # Append self-check to response if not already included
        if "=== SELF-CHECK ===" not in response:
            response += f"\n\n=== SELF-CHECK ===\n{self_check_text}"
        
        # Build structured report
        structured_report = {
            "format": "strict_requirements",
            "factor_extraction": self._format_factors(factors),
            "debate_log": debate_log,
            "failed_weak_factors": factor_outcomes,
            "final_synthesis": response,
            "self_check": self_check_data,
            "full_report": response
        }
        
        report = {
            "type": MessageType.FINAL_DIRECTIVE.value,
            "report": response,
            "structured": structured_report,
            "debate_log": debate_log,
            "factor_outcomes": factor_outcomes,
            "timestamp": self._get_timestamp()
        }
        
        await self._publish(report)
        return report
    
    def _format_self_check(self, self_check_data: Dict) -> str:
        """Format self-check section."""
        lines = []
        
        bypassed = self_check_data.get('factors_bypassed_count', 0)
        if bypassed > 0:
            lines.append(f"- Did any factor bypass debate? Yes - Factors {self_check_data.get('factors_bypassed_debate', [])}")
        else:
            lines.append("- Did any factor bypass debate? No")
        
        unstated = self_check_data.get('unstated_assumptions', [])
        if unstated:
            lines.append(f"- Did any conclusion rely on unstated assumptions? Yes - {', '.join(unstated)}")
        else:
            lines.append("- Did any conclusion rely on unstated assumptions? None identified")
        
        collapsed = self_check_data.get('collapsed_to_summarization', False)
        if collapsed:
            lines.append("- Did the system collapse to summarization? Yes - Debate was incomplete or factors lacked proper support/critique")
        else:
            lines.append("- Did the system collapse to summarization? No - Full debate occurred for all factors")
        
        return "\n".join(lines)
    
    def _build_debate_log(self, factors: list, all_messages: list) -> Dict:
        """Build complete debate log for each factor."""
        debate_log = {}
        rejected_factors = set()
        
        for factor in factors:
            factor_id = factor['id']
            debate_log[factor_id] = {
                "factor": factor,
                "support": None,
                "critique": None,
                "rebuttal": None,
                "resolution": None,  # ACCEPTED, WEAKENED, REJECTED, CONCEDED
                "is_rejected": False
            }
        
        # Extract messages by type
        for msg in all_messages:
            factor_id = msg.get('factor_id')
            if not factor_id or factor_id not in debate_log:
                continue
            
            msg_type = msg.get('type')
            if msg_type == MessageType.SUPPORT_ARGUMENT.value:
                debate_log[factor_id]['support'] = msg.get('argument', '')
            elif msg_type == MessageType.CRITIQUE.value:
                debate_log[factor_id]['critique'] = msg.get('argument', '')
                # Check verdict from critique - REJECTED takes precedence
                verdict = msg.get('verdict', '').upper()
                if 'REJECTED' in verdict or 'ANALYTICALLY_REJECTED' in verdict:
                    debate_log[factor_id]['resolution'] = 'REJECTED'
                    debate_log[factor_id]['is_rejected'] = True
                    rejected_factors.add(factor_id)
                elif 'WEAKENED' in verdict and debate_log[factor_id]['resolution'] != 'REJECTED':
                    debate_log[factor_id]['resolution'] = 'WEAKENED'
            elif msg_type == MessageType.REBUTTAL.value:
                debate_log[factor_id]['rebuttal'] = msg.get('rebuttal', '')
                # Check if rebuttal was a concession
                if msg.get('is_concession', False):
                    debate_log[factor_id]['resolution'] = 'REJECTED'
                    debate_log[factor_id]['is_rejected'] = True
                    rejected_factors.add(factor_id)
                elif msg.get('resolution_status') == 'WEAKENED':
                    debate_log[factor_id]['resolution'] = 'WEAKENED'
                # Rebuttal does NOT override REJECTED status
                elif debate_log[factor_id]['resolution'] != 'REJECTED':
                    # Only partially accept if critic didn't reject
                    if debate_log[factor_id]['critique']:
                        verdict = None
                        for m in all_messages:
                            if m.get('factor_id') == factor_id and m.get('type') == MessageType.CRITIQUE.value:
                                verdict = m.get('verdict', '').upper()
                                break
                        if verdict and 'REJECTED' not in verdict:
                            debate_log[factor_id]['resolution'] = 'PARTIALLY_ACCEPTED'
        
        # Set default resolution for factors without explicit resolution
        for factor_id, log in debate_log.items():
            if not log['resolution']:
                if log['support'] and log['critique']:
                    if log['rebuttal']:
                        log['resolution'] = 'PARTIALLY_ACCEPTED'
                    else:
                        log['resolution'] = 'WEAKENED'
                elif log['support'] and not log['critique']:
                    log['resolution'] = 'ACCEPTED'
                elif not log['support']:
                    log['resolution'] = 'NO_SUPPORT'
        
        return debate_log
    
    def _classify_factor_outcomes(self, factors: list, all_messages: list, debate_log: Dict) -> Dict:
        """Classify factors as failed, weak, or rejected."""
        outcomes = {
            "failed": [],
            "weak": [],
            "rejected": [],
            "partially_accepted": []
        }
        
        for factor in factors:
            factor_id = factor['id']
            log = debate_log.get(factor_id, {})
            resolution = log.get('resolution', '')
            is_rejected = log.get('is_rejected', False)
            
            factor_info = {
                "factor_id": factor_id,
                "factor_name": factor['name'],
                "reason": ""
            }
            
            # Find rejection reason from critique
            rejection_reason = None
            for msg in all_messages:
                if msg.get('factor_id') == factor_id and msg.get('type') == MessageType.CRITIQUE.value:
                    if 'REJECTED' in msg.get('verdict', '').upper():
                        rejection_reason = msg.get('rejection_reason') or msg.get('argument', '')[:300]
                        break
            
            if is_rejected or resolution == 'REJECTED':
                factor_info["reason"] = f"REJECTED: {rejection_reason or log.get('critique', 'No critique available')[:200]}"
                # For now, attribute rejection to CriticAgent; concessions are handled in claim state
                factor_info["rejected_by"] = "CriticAgent"
                outcomes["rejected"].append(factor_info)
            elif resolution == 'WEAKENED':
                factor_info["reason"] = f"Critique weakened assumptions or evidence: {log.get('critique', '')[:200]}"
                outcomes["weak"].append(factor_info)
            elif resolution == 'PARTIALLY_ACCEPTED':
                factor_info["reason"] = f"Rebuttal partially addressed critique but factor remains weakened"
                outcomes["partially_accepted"].append(factor_info)
            elif resolution == 'NO_SUPPORT':
                factor_info["reason"] = "No supporting argument generated"
                outcomes["failed"].append(factor_info)
            elif not log.get('support') or not log.get('critique'):
                factor_info["reason"] = "Incomplete debate - missing support or critique"
                outcomes["failed"].append(factor_info)
        
        return outcomes
    
    def _format_factors(self, factors: list) -> str:
        """Format factors for display."""
        lines = []
        for factor in factors:
            lines.append(f"{factor['id']}. {factor['name']}: {factor['description']}")
        return "\n".join(lines) if lines else "No factors extracted."
    
    def _format_debate_log(self, debate_log: Dict) -> str:
        """Format debate log for display."""
        lines = []
        for factor_id in sorted(debate_log.keys()):
            log = debate_log[factor_id]
            factor = log['factor']
            
            lines.append(f"\nFactor {factor_id}: {factor['name']}")
            lines.append("- Supporting Agent:")
            if log['support']:
                lines.append(f"  {log['support'][:500]}...")
            else:
                lines.append("  [No support argument generated]")
            
            lines.append("- Critic Agent:")
            if log['critique']:
                lines.append(f"  {log['critique'][:500]}...")
            else:
                lines.append("  [No critique generated]")
            
            lines.append("- Resolution:")
            resolution = log.get('resolution', 'UNKNOWN')
            if log['rebuttal']:
                lines.append(f"  REBUTTAL: {log['rebuttal'][:300]}...")
                lines.append(f"  STATUS: {resolution}")
            else:
                lines.append(f"  STATUS: {resolution}")
                if resolution == 'REJECTED':
                    lines.append("  (No rebuttal - factor rejected)")
                elif resolution == 'WEAKENED':
                    lines.append("  (No rebuttal - factor weakened)")
        
        return "\n".join(lines) if lines else "No debate log available."
    
    def _format_failed_factors(self, factor_outcomes: Dict) -> str:
        """Format failed/weak/rejected factors."""
        lines = []
        
        if factor_outcomes.get('rejected'):
            lines.append("REJECTED FACTORS:")
            for factor in factor_outcomes['rejected']:
                lines.append(f"  - Factor {factor['factor_id']}: {factor['factor_name']}")
                lines.append(f"    Rejected by: {factor.get('rejected_by', 'Unknown')}")
                lines.append(f"    Reason: {factor['reason']}")
        
        if factor_outcomes.get('weak'):
            lines.append("\nWEAK FACTORS:")
            for factor in factor_outcomes['weak']:
                lines.append(f"  - Factor {factor['factor_id']}: {factor['factor_name']}")
                lines.append(f"    Reason: {factor['reason']}")
        
        if factor_outcomes.get('partially_accepted'):
            lines.append("\nPARTIALLY ACCEPTED FACTORS:")
            for factor in factor_outcomes['partially_accepted']:
                lines.append(f"  - Factor {factor['factor_id']}: {factor['factor_name']}")
                lines.append(f"    Reason: {factor['reason']}")
        
        if factor_outcomes.get('failed'):
            lines.append("\nFAILED FACTORS:")
            for factor in factor_outcomes['failed']:
                lines.append(f"  - Factor {factor['factor_id']}: {factor['factor_name']}")
                lines.append(f"    Reason: {factor['reason']}")
        
        return "\n".join(lines) if lines else "No failed/weak/rejected factors identified."
    
    async def _generate_self_check(self, factors: list, debate_log: Dict, all_messages: list, input_text: str) -> Dict:
        """Generate self-check answers with real assumption detection."""
        # Check if any factor bypassed debate
        factors_bypassed = []
        for factor in factors:
            factor_id = factor['id']
            log = debate_log.get(factor_id, {})
            if not log.get('support') or not log.get('critique'):
                factors_bypassed.append(factor_id)
        
        # Real assumption detection using LLM
        unstated_assumptions = await self._detect_unstated_assumptions(factors, debate_log, input_text)
        
        # Check if system collapsed to summarization
        collapsed_to_summary = len(factors) == 0 or all(
            not debate_log.get(fid, {}).get('support') 
            for fid in [f['id'] for f in factors]
        )
        
        # Check if rejected factors are being used in synthesis (would be caught in final report generation)
        
        return {
            "factors_bypassed_debate": factors_bypassed,
            "factors_bypassed_count": len(factors_bypassed),
            "unstated_assumptions": unstated_assumptions,
            "collapsed_to_summarization": collapsed_to_summary
        }
    
    async def _detect_unstated_assumptions(self, factors: list, debate_log: Dict, input_text: str) -> List[str]:
        """Use LLM to detect unstated assumptions in the reasoning."""
        # Build summary of factors and debates
        factors_summary = "\n".join([
            f"Factor {f['id']}: {f['name']} - {f['description']}"
            for f in factors
        ])
        
        debates_summary = ""
        for factor_id, log in debate_log.items():
            debates_summary += f"\nFactor {factor_id}:\n"
            if log.get('support'):
                debates_summary += f"  Support: {log['support'][:200]}...\n"
            if log.get('critique'):
                debates_summary += f"  Critique: {log['critique'][:200]}...\n"
            if log.get('rebuttal'):
                debates_summary += f"  Rebuttal: {log['rebuttal'][:200]}...\n"
        
        prompt = f"""You are analyzing a multi-agent debate system's reasoning. Identify unstated assumptions that the reasoning relies on but were not explicitly defended or debated.

Factors analyzed:
{factors_summary}

Debate summary:
{debates_summary}

Original document (excerpt):
{input_text[:1000]}

List 3-10 implicit assumptions that the reasoning relies on but that were NOT explicitly stated, defended, or debated. Return as a JSON array of strings:
["assumption 1", "assumption 2", ...]

If no unstated assumptions are found, return an empty array: []"""

        try:
            response = await self.llm_client.generate(prompt)
            import json
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                assumptions = json.loads(json_match.group())
                return assumptions if isinstance(assumptions, list) else []
        except:
            pass
        
        return []
    
    def _parse_structured_report(self, response: str) -> Dict:
        """Parse structured JSON from LLM response."""
        # Try to extract JSON
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Fallback: return minimal structure with default verdict
        return {
            "problem_overview": "",
            "key_factors": [],
            "debate_summary": "",
            "root_cause_analysis": "",
            "what_worked": [],
            "what_failed": [],
            "why_it_happened": "",
            "actionable_recommendations": [],
            "risks_limitations": "",
            "final_verdict": {
                "core_claim_valid": False,
                "core_claim_invalid": True,
                "invalid_assumptions": [],
                "rejected_narratives": [],
                "belief_formation_explanation": "",
                "confidence": 0.5,
                "verdict_text": response[:500],
                "is_inconclusive": True,
                "inconclusive_reason": "Structured parsing failed"
            },
            "narrative_report": response
        }

