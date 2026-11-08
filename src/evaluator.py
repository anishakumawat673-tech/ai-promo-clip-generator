"""
Multi-Model Promo Evaluator.
Integrates with Gemini, OpenAI, or an Offline Rule-Based Engine.
Provides plug-and-play model swapping for evaluation and live interview testing.
"""

import os
import json
import re
from typing import Dict, Any, Optional, List
from src.candidate_gen import PromoCandidate


PROMO_EVAL_PROMPT = """You are an elite short-form video editor for microdrama apps (like ReelShort, DramaBox, Kuku TV).
Your job is to evaluate a candidate 20-60 second promo clip taken from a screenplay to be posted on TikTok, Instagram Reels, and YouTube Shorts.

CRITERIA FOR A WINNING PROMO:
1. Opens on a HOOK (first 3 seconds): Must stop a scrolling user dead in their tracks (slap, gasp, scandalous reveal, sudden betrayal, weapon drawn, shocking line).
2. Ends on a CLIFFHANGER: Cuts at an unresolved moment so the viewer feels an irresistible itch to know what happens next.
3. STANDALONE COHERENCE: Makes emotional and dramatic sense on its own to someone who has NEVER seen this show before.

CANDIDATE CLIP DETAILS:
- Episode: {episode_num}
- Timestamps: {start_str} to {end_str} ({duration_s} seconds)
- Opening 3 Seconds (Hook Window):
  {hook_window}
- Final 4 Seconds (Cliffhanger Window):
  {cliff_window}
- Full Clip Script Excerpt:
  {full_transcript}

Respond strictly in valid JSON with this exact schema:
{{
  "hook_score": <float 1.0 to 10.0>,
  "cliffhanger_score": <float 1.0 to 10.0>,
  "standalone_score": <float 1.0 to 10.0>,
  "hook_description": "<concise description of the 3-second hook>",
  "cliffhanger_description": "<concise description of the cut point tension>",
  "why_it_works": "<exactly one punchy sentence explaining why this clip converts scrolling viewers into app downloads>",
  "posting_priority": "<'Post First (Top-of-Funnel Viral)' OR 'Post Second (Mid-Funnel Conversion)' OR 'Do Not Post (Lacks Punch)'>"
}}
"""


class PromoEvaluator:
    """Evaluates candidate promos using LLMs or offline heuristic synthesis."""

    def __init__(
        self,
        provider: str = "offline",  # 'offline', 'gemini', 'openai', or 'custom'
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        custom_endpoint: Optional[str] = None
    ):
        self.provider = provider.lower()
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
        self.model_name = model_name or ("gemini-1.5-flash" if "gemini" in self.provider else "gpt-4o-mini")
        self.custom_endpoint = custom_endpoint

    def evaluate_candidate(self, candidate: PromoCandidate) -> Dict[str, Any]:
        """Evaluates a single candidate and returns refined scores and descriptions."""
        if self.provider == "offline" or not self.api_key:
            return self._evaluate_offline(candidate)
        elif "gemini" in self.provider:
            return self._evaluate_gemini(candidate)
        elif "openai" in self.provider:
            return self._evaluate_openai(candidate)
        else:
            return self._evaluate_offline(candidate)

    def _evaluate_offline(self, candidate: PromoCandidate) -> Dict[str, Any]:
        """
        High-fidelity offline heuristic evaluator.
        Ensures the pipeline runs immediately without needing external network or paid API keys.
        """
        hook_s = candidate.hook_score
        cliff_s = candidate.cliffhanger_score
        stand_s = candidate.standalone_score

        # Determine posting priority
        composite = 0.40 * hook_s + 0.35 * cliff_s + 0.25 * stand_s
        if hook_s >= 7.5 and stand_s >= 6.5:
            priority = "Post First (Top-of-Funnel Viral)"
            why_pitch = f"Instantly hooks cold scrollers with high-stakes confrontation ('{candidate.hook_text[:60]}...') and resolves cleanly into an unbearable cliffhanger."
        elif cliff_s >= 7.5:
            priority = "Post Second (Mid-Funnel Conversion)"
            why_pitch = f"High narrative escalation cutting at peak tension ('{candidate.cliffhanger_text[:60]}...'), compelling scrollers to download Kuku to see the payoff."
        else:
            priority = "Post Later (Supporting Lore)"
            why_pitch = f"Builds strong character tension ({candidate.duration_s}s) but relies slightly more on emotional context."

        return {
            "hook_score": hook_s,
            "cliffhanger_score": cliff_s,
            "standalone_score": stand_s,
            "composite_score": round(composite, 2),
            "hook_description": candidate.hook_text,
            "cliffhanger_description": candidate.cliffhanger_text,
            "why_it_works": why_pitch,
            "posting_priority": priority
        }

    def _evaluate_gemini(self, candidate: PromoCandidate) -> Dict[str, Any]:
        """Calls Google Gemini API (gemini-1.5-flash or gemini-2.0-flash)."""
        import requests

        prompt = self._build_prompt(candidate)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "response_mime_type": "application/json"}
        }

        try:
            resp = requests.post(url, json=payload, timeout=20)
            if resp.status_code == 200:
                res_data = resp.json()
                text_out = res_data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text_out)
                return self._format_llm_result(parsed, candidate)
        except Exception as e:
            print(f"Gemini API fallback to offline: {e}")

        return self._evaluate_offline(candidate)

    def _evaluate_openai(self, candidate: PromoCandidate) -> Dict[str, Any]:
        """Calls OpenAI or OpenAI-compatible endpoint."""
        import requests

        prompt = self._build_prompt(candidate)
        base_url = self.custom_endpoint or "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": "You are an expert microdrama promo editor. Output valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }

        try:
            resp = requests.post(base_url, headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                res_data = resp.json()
                text_out = res_data["choices"][0]["message"]["content"]
                parsed = json.loads(text_out)
                return self._format_llm_result(parsed, candidate)
        except Exception as e:
            print(f"OpenAI API fallback to offline: {e}")

        return self._evaluate_offline(candidate)

    def _build_prompt(self, candidate: PromoCandidate) -> str:
        hook_blocks = [b for b in candidate.blocks if b.start_s <= candidate.start_s + 3.5]
        cliff_blocks = [b for b in candidate.blocks if b.end_s >= candidate.end_s - 4.5]

        hook_desc = "\n".join(f"[{b.start_str}] {b.block_type}: {b.text}" for b in hook_blocks)
        cliff_desc = "\n".join(f"[{b.start_str}] {b.block_type}: {b.text}" for b in cliff_blocks)
        transcript = "\n".join(
            f"[{b.start_str} - {b.end_str}] {b.character + ': ' if b.character else ''}{b.text}"
            for b in candidate.blocks
        )

        return PROMO_EVAL_PROMPT.format(
            episode_num=candidate.episode_num,
            start_str=candidate.start_str,
            end_str=candidate.end_str,
            duration_s=candidate.duration_s,
            hook_window=hook_desc,
            cliff_window=cliff_desc,
            full_transcript=transcript[:1500]
        )

    def _format_llm_result(self, parsed: Dict[str, Any], candidate: PromoCandidate) -> Dict[str, Any]:
        hook_s = float(parsed.get("hook_score", candidate.hook_score))
        cliff_s = float(parsed.get("cliffhanger_score", candidate.cliffhanger_score))
        stand_s = float(parsed.get("standalone_score", candidate.standalone_score))
        composite = round(0.40 * hook_s + 0.35 * cliff_s + 0.25 * stand_s, 2)

        return {
            "hook_score": hook_s,
            "cliffhanger_score": cliff_s,
            "standalone_score": stand_s,
            "composite_score": composite,
            "hook_description": parsed.get("hook_description", candidate.hook_text),
            "cliffhanger_description": parsed.get("cliffhanger_description", candidate.cliffhanger_text),
            "why_it_works": parsed.get("why_it_works", candidate.why_it_works),
            "posting_priority": parsed.get("posting_priority", "Post First (Top-of-Funnel Viral)")
        }

