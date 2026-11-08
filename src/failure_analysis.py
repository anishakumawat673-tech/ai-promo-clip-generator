"""
Quality Checking & Failure Analysis Engine.
Audits promo outputs, flags edge cases where automated tools fail,
and provides editor-in-the-loop mitigation guidelines.
"""

from typing import List, Dict, Any


class PromoFailureAnalyzer:
    """Analyzes candidate promos to detect common failure modes and false positives."""

    FAILURE_MODES = {
        "FM1_LORE_OVERLOAD": {
            "name": "Late-Show Lore Bleed",
            "description": "High cliffhanger score but relies heavily on intricate late-season character lore that baffles a first-time viewer on TikTok.",
            "mitigation": "Editor should restrict Tier-1 ad spend to Episodes 1-10, or add a 2-second on-screen context card."
        },
        "FM2_PACING_LAG": {
            "name": "Vertical Pacing Lag",
            "description": "Clip duration is > 35s with sparse dialogue (< 3 lines), relying on atmospheric staring that scrollers swipe away from.",
            "mitigation": "Editor should trim internal silent reaction shots to compress duration down to 20-25s."
        },
        "FM3_SUBTLE_HOOK": {
            "name": "Subtle Opening Setup",
            "description": "Clip begins with polite or ambiguous setup lines before the explosive conflict hits 6 seconds in (missing the 3-second hook window).",
            "mitigation": "Snip the opening 3 seconds so the video begins directly on the provocative rebuttal or slap."
        },
        "FM4_SEMANTIC_MISMATCH": {
            "name": "Physical vs Lexical Disconnect",
            "description": "Dramatic text description (e.g. 'cold gaze') that does not translate to visceral visual shock without specialized camera work.",
            "mitigation": "Review storyboard/video rough cut to ensure actor expression carries sufficient kinetic energy."
        }
    }

    @classmethod
    def audit_promo(cls, promo: Dict[str, Any]) -> List[Dict[str, str]]:
        """Audits an individual promo and flags any potential failure modes."""
        flags = []
        ep_num = promo["episode"]
        duration = promo.get("total_duration_s", 0)
        hook_score = promo.get("hook_score", 0)
        cliff_score = promo.get("cliffhanger_score", 0)
        preview = promo.get("dialogue_preview", "")

        # FM1: High cliffhanger from late episodes that might confuse cold scrollers
        if ep_num > 25 and cliff_score >= 7.5 and hook_score < 7.0:
            flags.append({
                "mode": "FM1_LORE_OVERLOAD",
                "details": f"Episode {ep_num} promo contains high late-season stakes that cold scrollers might not grasp without knowing prior character relationships."
            })

        # FM2: Long clip with sparse dialogue
        turns = preview.count("|") + 1 if preview else 0
        if duration >= 40.0 and turns <= 3:
            flags.append({
                "mode": "FM2_PACING_LAG",
                "details": f"Clip duration is {duration:.1f}s with only {turns} dialogue exchanges. Risks swipe-away during visual lulls."
            })

        # FM3: Hook score is mediocre (under 5.5) but overall score was lifted by cliffhanger
        if hook_score < 5.5 and cliff_score >= 8.0:
            flags.append({
                "mode": "FM3_SUBTLE_HOOK",
                "details": "Strong ending cliffhanger, but the opening 3 seconds lack an immediate scroll-stopping punch. Editor should trim intro."
            })

        return flags

    @classmethod
    def generate_audit_report(cls, all_promos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generates a comprehensive quality check and failure audit across the entire promo suite."""
        audited_promos = []
        mode_counts = {k: 0 for k in cls.FAILURE_MODES.keys()}

        for p in all_promos:
            flags = cls.audit_promo(p)
            for f in flags:
                mode_counts[f["mode"]] += 1
            p_audit = dict(p)
            p_audit["quality_flags"] = flags
            audited_promos.append(p_audit)

        flagged_count = sum(1 for p in audited_promos if p["quality_flags"])

        return {
            "total_promos_audited": len(all_promos),
            "flagged_for_human_review": flagged_count,
            "pass_rate_clean": f"{((len(all_promos) - flagged_count) / len(all_promos) * 100):.1f}%" if all_promos else "0%",
            "failure_mode_breakdown": mode_counts,
            "failure_taxonomy": cls.FAILURE_MODES,
            "representative_edge_cases": [p for p in audited_promos if p["quality_flags"]][:5]
        }

