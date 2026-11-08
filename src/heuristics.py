"""
Heuristics and Feature Extraction for Promo Detection.
Evaluates Hook potential, Cliffhanger tension, and Standalone coherence using deterministic rules.
"""

import re
from typing import List, Dict, Any, Tuple
from src.parser import ScriptBlock, format_timestamp


# Keyword sets for high-impact microdrama moments
HOOK_ACTION_KEYWORDS = {
    "slap", "slaps", "slapping", "shatter", "shatters", "grab", "grabs", "shove", "shoves",
    "push", "pushes", "tear", "tears", "rip", "rips", "gasp", "gasps", "strangle", "choke",
    "collapse", "collapses", "faint", "faints", "bleed", "bleeding", "blood", "sword",
    "dagger", "knife", "gun", "shot", "explosion", "explodes", "chains", "arrest",
    "kneel", "kneels", "strip", "strips", "slam", "slams", "violently", "smash", "smashes",
    "drag", "drags", "point", "points", "whip", "screaming", "screams"
}

HOOK_DIALOGUE_KEYWORDS = {
    "liar", "bastard", "traitor", "fool", "disgrace", "mistress", "whore", "harlot",
    "unworthy", "beg", "kill", "die", "poison", "ruined", "divorce", "marry", "wedding",
    "altar", "abandon", "leave", "never", "dare", "shut up", "kneel", "crawl", "worthless",
    "trash", "bastard", "fraud", "impostor", "dead", "murder", "execution", "guilty",
    "secret", "pregnant", "child", "who are you", "what did you do"
}

HIGH_TENSION_EMOTIONS = {
    "furious", "enraged", "cold", "commanding", "sneering", "cruel", "mocking", "icy",
    "venomous", "malicious", "smug", "desperate", "hysterical", "screaming", "shocked",
    "horrified", "breathless", "trembling", "thunderous", "seething", "taunting", "merciless",
    "disdainful", "blunt", "unforgiving"
}

CLIFFHANGER_KEYWORDS = {
    "wait", "stop", "look", "listen", "who", "what", "no", "how could you",
    "it cannot be", "you are", "i know", "tell me", "the truth", "duke",
    "cut to black", "cliffhanger", "swells", "ominous", "drone", "gasp", "freezes"
}


class ScreenplayHeuristics:
    """Computes rule-based features for any candidate clip window."""

    @staticmethod
    def evaluate_hook(first_blocks: List[ScriptBlock]) -> Dict[str, Any]:
        """
        Analyzes the first 3 seconds of a candidate clip.
        Returns hook score (0-10), trigger reasons, and verbatim hook text.
        """
        score = 2.0  # baseline
        reasons = []
        hook_text = ""

        dialogues = [b for b in first_blocks if b.block_type == "DIALOGUE"]
        actions = [b for b in first_blocks if b.block_type == "ACTION"]
        sounds = [b for b in first_blocks if b.block_type == "SOUND FX"]

        # Check dialogue
        for d in dialogues:
            hook_text += f"{d.character or 'Character'}: \"{d.text}\" "
            text_lower = d.text.lower()
            
            # Dialogue keywords
            for kw in HOOK_DIALOGUE_KEYWORDS:
                if kw in text_lower:
                    score += 2.0
                    reasons.append(f"Shock dialogue keyword: '{kw}'")
                    break

            # Emotion tags
            if d.emotion:
                emo_lower = d.emotion.lower()
                for emo in HIGH_TENSION_EMOTIONS:
                    if emo in emo_lower:
                        score += 1.5
                        reasons.append(f"High-stakes vocal emotion: '{d.emotion}'")
                        break

            # Punchy questions or imperatives
            if "?" in d.text and len(d.text.split()) <= 8:
                score += 1.0
                reasons.append("Punchy confrontational question")
            if "!" in d.text:
                score += 0.8
                reasons.append("Exclamatory delivery")

        # Check action
        for a in actions:
            if not hook_text:
                hook_text = a.text
            text_lower = a.text.lower()
            for kw in HOOK_ACTION_KEYWORDS:
                if kw in text_lower:
                    score += 2.5
                    reasons.append(f"Physical drama action: '{kw}'")
                    break

        # Check sound FX
        for s in sounds:
            text_lower = s.text.lower()
            if any(k in text_lower for k in ["slam", "gunshot", "slap", "shatter", "gasp", "explosion"]):
                score += 1.5
                reasons.append(f"Impact sound effect: {s.text}")

        score = min(10.0, round(score, 1))
        hook_summary = hook_text.strip()[:140] if hook_text else "Visual opening"
        return {
            "score": score,
            "reasons": list(set(reasons)),
            "text": hook_summary
        }

    @staticmethod
    def evaluate_cliffhanger(last_blocks: List[ScriptBlock]) -> Dict[str, Any]:
        """
        Analyzes the last 3-4 seconds of a candidate clip.
        Returns cliffhanger score (0-10), trigger reasons, and cliffhanger text.
        """
        score = 2.0
        reasons = []
        cliff_text = ""

        dialogues = [b for b in last_blocks if b.block_type == "DIALOGUE"]
        actions = [b for b in last_blocks if b.block_type == "ACTION"]
        sounds = [b for b in last_blocks if b.block_type == "SOUND FX"]
        cameras = [b for b in last_blocks if b.block_type == "CAMERA"]

        for d in dialogues:
            cliff_text += f"{d.character or 'Character'}: \"{d.text}\" "
            text = d.text.strip()
            # Cuts off with ellipsis or dash
            if text.endswith("...") or text.endswith("—") or text.endswith("-"):
                score += 3.0
                reasons.append("Cut off mid-sentence / trailing revelation")
            # Unanswered question
            elif text.endswith("?"):
                score += 2.5
                reasons.append("Unresolved direct question")
            
            # Shocking reveal keywords
            for kw in CLIFFHANGER_KEYWORDS:
                if kw in text.lower():
                    score += 1.5
                    reasons.append(f"Cliffhanger keyword: '{kw}'")
                    break

        for a in actions:
            if not cliff_text:
                cliff_text = a.text
            text_lower = a.text.lower()
            if any(k in text_lower for k in ["freeze", "shock", "gasps", "widens", "fist", "blade", "points"]):
                score += 1.5
                reasons.append("Frozen stunned physical reaction")

        for s in sounds:
            text_lower = s.text.lower()
            if any(k in text_lower for k in ["cliffhanger", "swells", "drone", "ominous", "sting", "shatter"]):
                score += 2.5
                reasons.append("Ominous music sting / cliffhanger drone")

        for c in cameras:
            text_lower = c.text.lower()
            if "cut to black" in text_lower:
                score += 2.0
                reasons.append("Hard cut to black")
            elif "push-in" in text_lower or "tight insert" in text_lower:
                score += 1.0
                reasons.append("Intense facial push-in")

        score = min(10.0, round(score, 1))
        cliff_summary = cliff_text.strip()[:140] if cliff_text else "Dramatic pause"
        return {
            "score": score,
            "reasons": list(set(reasons)),
            "text": cliff_summary
        }

    @staticmethod
    def evaluate_standalone(blocks: List[ScriptBlock]) -> Dict[str, Any]:
        """
        Analyzes whether a clip makes sense on its own to someone who hasn't seen the show.
        Checks dialogue coherence, identifiable character roles, and self-contained emotional conflict.
        """
        score = 5.0
        reasons = []

        dialogues = [b for b in blocks if b.block_type == "DIALOGUE"]
        if not dialogues:
            return {"score": 2.0, "reasons": ["No dialogue; visual only"], "text": "Silent sequence"}

        total_words = sum(len(d.text.split()) for d in dialogues)
        num_turns = len(dialogues)

        # Natural conversation pacing (2 to 8 dialogue exchanges)
        if 2 <= num_turns <= 8:
            score += 2.0
            reasons.append(f"Optimal rapid dialogue back-and-forth ({num_turns} turns)")
        elif num_turns > 12:
            score -= 1.0
            reasons.append("Too many rapid turns, potential cognitive overload")

        # Clear relatable relationship markers
        rel_markers = ["sister", "mother", "father", "husband", "wife", "fiancé", "fiance", "bride", "groom", "duke", "lord", "lady", "marry", "wedding"]
        all_text = " ".join(d.text.lower() for d in dialogues)
        found_markers = [m for m in rel_markers if m in all_text]
        if found_markers:
            score += 2.0
            reasons.append(f"Explicit relatable archetypes: {', '.join(found_markers[:3])}")
        else:
            score -= 1.0
            reasons.append("Context-dependent; relationship between speakers requires prior knowledge")

        score = max(1.0, min(10.0, round(score, 1)))
        return {
            "score": score,
            "reasons": reasons,
            "text": f"{num_turns} dialogue turns with relatable stakes"
        }

