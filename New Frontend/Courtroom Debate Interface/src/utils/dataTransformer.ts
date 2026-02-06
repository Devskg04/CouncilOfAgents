/**
 * Data Transformer
 * Converts backend API responses to frontend TypeScript types
 */

import { Decision, Factor, AgentMessage, FinalRecommendation, Synthesis } from '../types/aether';
import { BackendResponse } from '../services/api';

/**
 * Transform backend response to frontend Decision type
 */
export function transformBackendResponse(
    response: BackendResponse,
    problemStatement: string
): Decision {
    if (!response.success) {
        throw new Error(response.error || 'Analysis failed');
    }

    const factors = transformFactors(response);
    const finalRecommendation = extractFinalRecommendation(response);

    // Calculate overall scores
    const overallDisagreementScore = calculateOverallDisagreementScore(factors);
    const overallRiskScore = calculateOverallRiskScore(response, finalRecommendation);

    return {
        id: response.analysis_id?.toString() || Date.now().toString(),
        problemStatement,
        timestamp: new Date(),
        factors,
        finalRecommendation,
        overallRiskScore,
        overallDisagreementScore,
    };
}

/**
 * Transform backend factors to frontend Factor type with debates
 */
function transformFactors(response: BackendResponse): Factor[] {
    const backendFactors = response.factors || [];
    const debates = response.debates || {};
    const allMessages = response.all_messages || [];

    return backendFactors.map((backendFactor, index) => {
        const factorId = backendFactor.id;
        const debateData = debates[factorId] || {};

        // Extract debate messages for this factor
        const debateMessages = extractDebateMessages(factorId, allMessages, debateData);

        // Extract synthesis for this factor
        const synthesis = extractFactorSynthesis(factorId, response, debateData);

        // Calculate disagreement score based on debate
        const disagreementScore = calculateDisagreementScore(debateData, debateMessages);

        // Calculate weight (normalized by number of factors)
        const weight = 1.0 / backendFactors.length;

        return {
            id: factorId,
            name: backendFactor.name || `Factor ${index + 1}`,
            description: backendFactor.description || '',
            debate: debateMessages,
            synthesis,
            disagreementScore,
            weight,
        };
    });
}

/**
 * Extract debate messages for a specific factor
 */
function extractDebateMessages(
    factorId: string,
    allMessages: any[],
    debateData: any
): AgentMessage[] {
    const messages: AgentMessage[] = [];
    let messageCounter = 0;

    // Get support, critique, and rebuttal from debate data
    const support = debateData.support;
    const critique = debateData.critique;
    const rebuttal = debateData.rebuttal;

    // Add supporting argument - split bullets into separate rounds
    if (support) {
        const supportMsg = allMessages.find(
            m => m.type === 'SUPPORT_ARGUMENT' && m.factor_id === factorId
        );

        const supportText = typeof support === 'string' ? support : (support.argument || support.content || '');
        const bullets = supportText.split('\n').filter((line: string) => line.trim().startsWith('•'));

        if (bullets.length > 0) {
            // Each bullet becomes its own round
            bullets.forEach((bullet: string, index: number) => {
                messages.push({
                    id: `${factorId}_support_${messageCounter++}`,
                    agent: 'SupportingAgent',
                    content: bullet.trim(),
                    timestamp: supportMsg?.timestamp ? new Date(supportMsg.timestamp) : new Date(),
                    round: index + 1,
                });
            });
        } else {
            // No bullets, use full text as round 1
            messages.push({
                id: `${factorId}_support_${messageCounter++}`,
                agent: 'SupportingAgent',
                content: supportText,
                timestamp: supportMsg?.timestamp ? new Date(supportMsg.timestamp) : new Date(),
                round: 1,
            });
        }
    }

    // Add critique - split bullets into separate rounds matching support rounds
    if (critique) {
        const critiqueMessages = allMessages.filter(
            m => m.type === 'CRITIQUE' && m.factor_id === factorId
        );

        const originalCritique = critiqueMessages.find(m => !m.is_update) || critiqueMessages[0];

        if (originalCritique) {
            const critiqueText = typeof critique === 'string' ? critique : (critique.argument || critique.content || '');
            const bullets = critiqueText.split('\n').filter((line: string) => line.trim().startsWith('•'));

            if (bullets.length > 0) {
                // Each bullet becomes its own round
                bullets.forEach((bullet: string, index: number) => {
                    messages.push({
                        id: `${factorId}_critique_${messageCounter++}`,
                        agent: 'CriticAgent',
                        content: bullet.trim(),
                        timestamp: originalCritique?.timestamp ? new Date(originalCritique.timestamp) : new Date(),
                        round: index + 1,
                    });
                });
            } else {
                // No bullets, use full text as round 1
                messages.push({
                    id: `${factorId}_critique_${messageCounter++}`,
                    agent: 'CriticAgent',
                    content: critiqueText,
                    timestamp: originalCritique?.timestamp ? new Date(originalCritique.timestamp) : new Date(),
                    round: 1,
                });
            }
        }
    }

    // Add rebuttal - split bullets into separate rounds
    if (rebuttal) {
        const rebuttalMsg = allMessages.find(
            m => m.type === 'REBUTTAL' && m.factor_id === factorId
        );

        const isConcession = rebuttalMsg?.is_concession ||
            (typeof rebuttal === 'string' && rebuttal.toUpperCase().includes('CONCEDE'));

        if (!isConcession) {
            const rebuttalText = typeof rebuttal === 'string' ? rebuttal : (rebuttal.rebuttal || rebuttal.content || '');
            const bullets = rebuttalText.split('\n').filter((line: string) => line.trim().startsWith('•'));

            // Get the max round from previous messages to continue numbering
            const maxRound = Math.max(...messages.map(m => m.round || 1), 0);

            if (bullets.length > 0) {
                bullets.forEach((bullet: string, index: number) => {
                    messages.push({
                        id: `${factorId}_rebuttal_${messageCounter++}`,
                        agent: 'SupportingAgent',
                        content: bullet.trim(),
                        timestamp: rebuttalMsg?.timestamp ? new Date(rebuttalMsg.timestamp) : new Date(),
                        round: maxRound + index + 1,
                    });
                });
            } else {
                messages.push({
                    id: `${factorId}_rebuttal_${messageCounter++}`,
                    agent: 'SupportingAgent',
                    content: rebuttalText,
                    timestamp: rebuttalMsg?.timestamp ? new Date(rebuttalMsg.timestamp) : new Date(),
                    round: maxRound + 1,
                });
            }
        }
    }

    // Add critic's re-evaluation - split bullets into separate rounds
    const critiqueUpdate = allMessages.find(
        m => m.type === 'CRITIQUE' && m.factor_id === factorId && m.is_update === true
    );

    if (critiqueUpdate) {
        const updateText = critiqueUpdate.argument || '';
        const bullets = updateText.split('\n').filter((line: string) => line.trim().startsWith('•'));

        // Get the max round from previous messages to continue numbering
        const maxRound = Math.max(...messages.map(m => m.round || 1), 0);

        if (bullets.length > 0) {
            bullets.forEach((bullet: string, index: number) => {
                messages.push({
                    id: `${factorId}_critique_update_${messageCounter++}`,
                    agent: 'CriticAgent',
                    content: bullet.trim(),
                    timestamp: critiqueUpdate.timestamp ? new Date(critiqueUpdate.timestamp) : new Date(),
                    round: maxRound + index + 1,
                });
            });
        } else {
            messages.push({
                id: `${factorId}_critique_update_${messageCounter++}`,
                agent: 'CriticAgent',
                content: updateText,
                timestamp: critiqueUpdate.timestamp ? new Date(critiqueUpdate.timestamp) : new Date(),
                round: maxRound + 1,
            });
        }
    }

    return messages;
}

/**
 * Extract synthesis for a specific factor
 */
function extractFactorSynthesis(
    factorId: string,
    response: BackendResponse,
    debateData: any
): Synthesis {
    const critique = debateData.critique || {};
    const resolution = critique.resolution || debateData.resolution || 'UNKNOWN';
    const support = debateData.support || {};
    const rebuttal = debateData.rebuttal || {};

    // Try to get REAL confidence from backend synthesis
    const synthesisData = response.synthesis || {};
    const structured = synthesisData.structured || {};
    const perFactorConfidence = structured.per_factor_confidence || {};
    const backendConfidence = perFactorConfidence[factorId];

    // Extract actual text from support and critique
    const supportText = typeof support === 'string' ? support : (support.argument || support.content || '');
    const critiqueText = typeof critique === 'string' ? critique : (critique.argument || critique.content || '');
    const rebuttalText = typeof rebuttal === 'string' ? rebuttal : (rebuttal.rebuttal || rebuttal.content || '');

    // Extract key points from actual debate content
    const keyPoints: string[] = [];
    let summary = '';

    // Extract supporting point (first sentence or key claim)
    if (supportText) {
        const supportSentences = supportText.split(/[.!?]/).filter((s: string) => s.trim().length > 10);
        if (supportSentences.length > 0) {
            keyPoints.push(`Supporting: ${supportSentences[0].trim().substring(0, 100)}...`);
        }
    }

    // Extract critique point
    if (critiqueText) {
        const critiqueSentences = critiqueText.split(/[.!?]/).filter((s: string) => s.trim().length > 10);
        if (critiqueSentences.length > 0) {
            keyPoints.push(`Critique: ${critiqueSentences[0].trim().substring(0, 100)}...`);
        }
    }

    // Extract rebuttal point if exists
    if (rebuttalText) {
        const rebuttalSentences = rebuttalText.split(/[.!?]/).filter((s: string) => s.trim().length > 10);
        if (rebuttalSentences.length > 0) {
            keyPoints.push(`Rebuttal: ${rebuttalSentences[0].trim().substring(0, 100)}...`);
        }
    }

    // Add resolution and confidence to key points
    keyPoints.push(`Resolution: ${resolution}`);
    if (typeof backendConfidence === 'number') {
        keyPoints.push(`Confidence: ${(backendConfidence * 100).toFixed(0)}%`);
    }

    // Generate summary based on resolution and actual debate
    switch (resolution.toUpperCase()) {
        case 'ACCEPTED':
            summary = supportText
                ? `Factor accepted. ${supportText.substring(0, 150)}...`
                : 'Factor accepted with supporting evidence.';
            break;

        case 'REJECTED':
            summary = critiqueText
                ? `Factor rejected. ${critiqueText.substring(0, 150)}...`
                : 'Factor rejected due to insufficient evidence.';
            break;

        case 'WEAKENED':
            summary = critiqueText
                ? `Factor weakened by critique. ${critiqueText.substring(0, 150)}...`
                : 'Factor weakened by valid concerns.';
            break;

        case 'PARTIALLY_ACCEPTED':
            summary = rebuttalText
                ? `Partially accepted with conditions. ${rebuttalText.substring(0, 150)}...`
                : 'Factor partially accepted with caveats.';
            break;

        default:
            summary = 'Debate completed with mixed results.';
            keyPoints.push('Multiple perspectives considered');
    }

    // Fallback if no key points extracted
    if (keyPoints.length === 0) {
        keyPoints.push('Debate completed');
        keyPoints.push(`Resolution: ${resolution}`);
    }

    return {
        summary,
        keyPoints,
        synthesizedBy: 'SynthesizerAgent',
    };
}

/**
 * Calculate disagreement score for a factor based on actual debate dynamics
 */
function calculateDisagreementScore(debateData: any, messages: AgentMessage[]): number {
    // Extract resolution and debate data
    const critique = debateData.critique || {};
    const support = debateData.support || {};
    const rebuttal = debateData.rebuttal || {};
    const resolution = critique.resolution || debateData.resolution || '';

    // Base score from resolution type
    let baseScore = 0.5;
    switch (resolution.toUpperCase()) {
        case 'ACCEPTED':
            baseScore = 0.1;
            break;
        case 'PARTIALLY_ACCEPTED':
            baseScore = 0.4;
            break;
        case 'WEAKENED':
            baseScore = 0.6;
            break;
        case 'REJECTED':
            baseScore = 0.7; // Changed from 0.9 - not all rejections are 90% disagreement
            break;
        default:
            baseScore = 0.5;
    }

    // Analyze debate dynamics for adjustment
    let adjustmentFactor = 0;

    // Factor 1: Evidence quality (has_evidence flag)
    const hasEvidence = support.has_evidence !== false;
    if (!hasEvidence) {
        adjustmentFactor += 0.15; // Weak evidence increases disagreement
    }

    // Factor 2: Rebuttal presence and quality
    const hasRebuttal = messages.some(m => m.round === 2);
    if (hasRebuttal) {
        const rebuttalText = typeof rebuttal === 'string' ? rebuttal : (rebuttal.rebuttal || '');
        const isConcession = rebuttal.is_concession ||
            rebuttalText.toUpperCase().includes('CONCEDE');

        if (isConcession) {
            adjustmentFactor += 0.15; // Concession increases disagreement
        } else if (rebuttalText.length > 100) {
            adjustmentFactor -= 0.1; // Strong rebuttal reduces disagreement
        }
    }

    // Factor 3: Debate intensity (message count and length)
    const totalDebateLength = messages.reduce((sum, msg) => sum + msg.content.length, 0);
    if (totalDebateLength > 1000) {
        adjustmentFactor += 0.05; // Longer debates suggest more disagreement
    }

    // Factor 4: Sub-claims (for PARTIALLY_ACCEPTED)
    const subClaims = critique.sub_claims || [];
    if (subClaims.length > 0) {
        const rejectedSubClaims = subClaims.filter((sc: any) =>
            sc.status?.toUpperCase() === 'REJECTED'
        ).length;
        const subClaimRejectionRate = rejectedSubClaims / subClaims.length;
        adjustmentFactor += subClaimRejectionRate * 0.2; // More rejected sub-claims = more disagreement
    }

    // Calculate final score with adjustments
    const finalScore = Math.max(0, Math.min(1, baseScore + adjustmentFactor));

    return finalScore;
}

/**
 * Extract final recommendation from backend response
 */
function extractFinalRecommendation(response: BackendResponse): FinalRecommendation {
    const finalReport = response.final_report || {};
    const structured = finalReport.structured || {};
    const factorOutcomes = finalReport.factor_outcomes || {};
    const resolutions = response.resolutions || { accepted: [], partially_accepted: [], rejected: [] };

    // Determine decision type based on rejected/accepted factors
    const rejectedCount = (resolutions.rejected || []).length;
    const acceptedCount = (resolutions.accepted || []).length;
    const partialCount = (resolutions.partially_accepted || []).length;
    const totalFactors = (response.factors || []).length;

    let decision: 'PROCEED' | 'REJECT' | 'CONDITIONAL_PROCEED' | 'NEEDS_MORE_DATA';

    if (rejectedCount > totalFactors / 2) {
        decision = 'REJECT';
    } else if (partialCount > 0 || (rejectedCount > 0 && acceptedCount > 0)) {
        decision = 'CONDITIONAL_PROCEED';
    } else if (acceptedCount > totalFactors / 2) {
        decision = 'PROCEED';
    } else {
        decision = 'NEEDS_MORE_DATA';
    }

    // Calculate confidence from integrity check and REAL backend data
    const integrityCheck = response.integrity_check || {};
    const confidence = calculateConfidence(integrityCheck, resolutions, finalReport);

    // Extract reasoning from final report
    const reasoning = extractReasoning(finalReport);

    // Extract accepted and rejected arguments
    const acceptedArguments = extractAcceptedArguments(response);
    const rejectedArguments = extractRejectedArguments(response);

    // Extract conditions if conditional proceed
    const conditions = decision === 'CONDITIONAL_PROCEED'
        ? extractConditions(response)
        : undefined;

    // Calculate agent influence
    const agentInfluence = calculateAgentInfluence(response);
    const mostInfluentialAgent = getMostInfluentialAgent(agentInfluence);

    return {
        decision,
        confidence,
        reasoning,
        acceptedArguments,
        rejectedArguments,
        conditions,
        mostInfluentialAgent,
        agentInfluence,
    };
}

/**
 * Calculate confidence score from REAL backend data
 */
function calculateConfidence(integrityCheck: any, resolutions: any, finalReport: any): number {
    // FIRST: Try to get real confidence from final_report.structured.final_verdict.confidence
    const structured = finalReport?.structured || {};
    const finalVerdict = structured.final_verdict || {};

    if (typeof finalVerdict.confidence === 'number') {
        // Use REAL confidence from backend
        return Math.max(0, Math.min(1, finalVerdict.confidence));
    }

    // FALLBACK: Calculate from integrity check if backend didn't provide it
    let confidence = 0.7;

    if (integrityCheck?.all_factors_debated === true) {
        confidence += 0.1;
    }

    if (integrityCheck?.no_circular_factors === true) {
        confidence += 0.1;
    }

    // Adjust based on resolution distribution
    const accepted = (resolutions?.accepted || []).length;
    const rejected = (resolutions?.rejected || []).length;
    const total = accepted + rejected + (resolutions?.partially_accepted || []).length;

    if (total > 0) {
        const clarity = Math.abs(accepted - rejected) / total;
        confidence = confidence * (0.7 + 0.3 * clarity);
    }

    return Math.max(0, Math.min(1, confidence));
}

/**
 * Extract reasoning from final report
 */
function extractReasoning(finalReport: any): string {
    const report = finalReport.report || '';

    // Try to extract final synthesis section
    const synthesisMatch = report.match(/===\s*FINAL SYNTHESIS\s*===\s*([\s\S]*?)(?:===|$)/i);
    if (synthesisMatch) {
        return synthesisMatch[1].trim().substring(0, 500);
    }

    // Fallback to first 500 characters of report
    return report.substring(0, 500);
}

/**
 * Extract accepted arguments
 */
function extractAcceptedArguments(response: BackendResponse): string[] {
    const accepted = response.resolutions?.accepted || [];
    const factors = response.factors || [];
    const debates = response.debates || {};

    return accepted.map(factorId => {
        const factor = factors.find(f => f.id === factorId);
        const debate = debates[factorId];

        if (factor && debate?.support) {
            let supportText = '';

            // Handle different support formats
            if (typeof debate.support === 'string') {
                supportText = debate.support;
            } else if (typeof debate.support === 'object') {
                // Try different possible fields
                supportText = debate.support.argument ||
                    debate.support.content ||
                    debate.support.text ||
                    JSON.stringify(debate.support);
            }

            if (supportText && supportText.length > 0) {
                return `${factor.name}: ${supportText.substring(0, 150)}...`;
            }
        }

        return factor ? `${factor.name} accepted` : `Factor ${factorId} accepted`;
    });
}

/**
 * Extract rejected arguments
 */
function extractRejectedArguments(response: BackendResponse): string[] {
    const rejected = response.resolutions?.rejected || [];
    const factors = response.factors || [];
    const debates = response.debates || {};

    return rejected.map(factorId => {
        const factor = factors.find(f => f.id === factorId);
        const debate = debates[factorId];

        if (factor && debate?.critique) {
            let critiqueText = '';

            // Handle different critique formats
            if (typeof debate.critique === 'string') {
                critiqueText = debate.critique;
            } else if (typeof debate.critique === 'object') {
                // Try different possible fields
                critiqueText = debate.critique.argument ||
                    debate.critique.content ||
                    debate.critique.text ||
                    JSON.stringify(debate.critique);
            }

            if (critiqueText && critiqueText.length > 0) {
                return `${factor.name}: ${critiqueText.substring(0, 150)}...`;
            }
        }

        return factor ? `${factor.name} rejected` : `Factor ${factorId} rejected`;
    });
}

/**
 * Extract conditions for conditional proceed
 */
function extractConditions(response: BackendResponse): string[] {
    const conditions: string[] = [];
    const partiallyAccepted = response.resolutions?.partially_accepted || [];
    const factors = response.factors || [];
    const debates = response.debates || {};

    partiallyAccepted.forEach(factorId => {
        const factor = factors.find(f => f.id === factorId);
        const debate = debates[factorId];

        if (factor) {
            conditions.push(`Address concerns regarding ${factor.name}`);
        }
    });

    // Add generic conditions if none found
    if (conditions.length === 0) {
        conditions.push('Further validation required for partially accepted factors');
        conditions.push('Monitor assumptions and gather additional evidence');
    }

    return conditions;
}

/**
 * Calculate agent influence from debate participation
 */
function calculateAgentInfluence(response: BackendResponse): Record<string, number> {
    const allMessages = response.all_messages || [];
    const influence: Record<string, number> = {
        SupportingAgent: 0,
        CriticAgent: 0,
        SynthesizerAgent: 0,
        FinalDecisionAgent: 0,
    };

    // Count messages by type
    let supportCount = 0;
    let critiqueCount = 0;
    let rebuttalCount = 0;

    allMessages.forEach(msg => {
        switch (msg.type) {
            case 'SUPPORT_ARGUMENT':
                supportCount++;
                break;
            case 'CRITIQUE':
                critiqueCount++;
                break;
            case 'REBUTTAL':
                rebuttalCount++;
                break;
        }
    });

    const total = supportCount + critiqueCount + rebuttalCount;

    if (total > 0) {
        influence.SupportingAgent = (supportCount + rebuttalCount) / total;
        influence.CriticAgent = critiqueCount / total;
    }

    // Synthesizer and FinalDecision have fixed small influence
    influence.SynthesizerAgent = 0.1;
    influence.FinalDecisionAgent = 0.1;

    // Normalize
    const sum = Object.values(influence).reduce((a, b) => a + b, 0);
    if (sum > 0) {
        Object.keys(influence).forEach(key => {
            influence[key] = influence[key] / sum;
        });
    }

    return influence;
}

/**
 * Get most influential agent
 */
function getMostInfluentialAgent(agentInfluence: Record<string, number>): string {
    let maxInfluence = 0;
    let mostInfluential = 'SupportingAgent';

    Object.entries(agentInfluence).forEach(([agent, influence]) => {
        if (influence > maxInfluence) {
            maxInfluence = influence;
            mostInfluential = agent;
        }
    });

    return mostInfluential;
}

/**
 * Calculate overall disagreement score
 */
function calculateOverallDisagreementScore(factors: Factor[]): number {
    if (factors.length === 0) return 0;

    const sum = factors.reduce((acc, factor) => acc + factor.disagreementScore, 0);
    return sum / factors.length;
}

/**
 * Calculate overall risk score
 */
function calculateOverallRiskScore(
    response: BackendResponse,
    finalRecommendation: FinalRecommendation
): number {
    const rejectedCount = (response.resolutions?.rejected || []).length;
    const totalFactors = (response.factors || []).length;

    if (totalFactors === 0) return 0.5;

    // Base risk on rejection rate
    const rejectionRate = rejectedCount / totalFactors;

    // Adjust by confidence (lower confidence = higher risk)
    const confidenceAdjustment = 1 - finalRecommendation.confidence;

    // Combine
    const riskScore = (rejectionRate * 0.6) + (confidenceAdjustment * 0.4);

    return Math.max(0, Math.min(1, riskScore));
}
