# KUKU — Automated Microdrama Promo Intelligence Engine
**Assignment:** Kuku AI Generalist — Problem 1: Find the Promos (Ads)  
**Target Show:** *I Married a Broken Soldier. He was a Duke* (50 Episodes)  
**Format:** Executive Solution Brief (Strict 2-Page PDF)

---

## 1. Problem Choice, Framing & Assumptions

### Why Problem 1?
Kuku’s core business model is short vertical microdrama (1–2 minute episodes). User acquisition across TikTok, Instagram Reels, and YouTube Shorts depends on high-converting **20–60 second promo clips**. Today, editors manually scrub through 50+ episodes per show every week—an expensive 4-to-6 hour bottleneck per series. Problem 1 directly solves this operational friction.

### Core Assumptions Made (Where Brief Was Silent)
1. **3-Second Sensory Rule:** A cold scroller decides to stay or swipe within 3.0s. The opening must have immediate visceral drama (slap, gasp, accusation, drawn blade) rather than slow scenery.
2. **Dialogue Boundary Snapping:** Cuts cannot slice mid-sentence or mid-breath. Cuts snap deterministically to dialogue or action boundaries.
3. **Standalone Coherence Priority:** A promo fails if it requires prior episode lore. Universal archetypes (betrayal at altar, cruel in-laws, unmasking) rank higher than mid-season politics.

---

## 2. System Architecture: Balancing Code vs. AI

Passing 100 minutes of screenplay text directly into an LLM is slow, expensive, and inaccurate at calculating exact durations. We engineered a **hybrid two-tier pipeline**:

### ⚙️ Tier 1: Deterministic Code & Heuristics (Python Engine)
* **Regex AST Parser:** Extracts scenes, character emotions, actions, and millisecond timestamps into typed dataclasses in **0.07s for 50 episodes**.
* **Sliding Candidate Generator:** Generates valid windows strictly bound between **20.0s and 60.0s** snapping to natural pauses.
* **Non-Maximum Suppression (NMS):** Suppresses temporal overlaps ($IoU > 0.50$), eliminating duplicate cuts of the same scene.
* **Multi-Segment Stitching:** Supports cross-scene or episode-boundary transition clips as permitted by the brief.

### 🤖 Tier 2: AI & Semantic Reasoning (LLM / Heuristics)
* **3s Hook Scoring (0–100):** Evaluates immediate scroll-stopping power and sensory shock.
* **Cliffhanger Cut Scoring (0–100):** Measures unresolved tension compelling scrollers to install the app.
* **Context Clarity Scoring (0–100):** Verifies self-contained intelligibility for cold viewers.
* **Ad Conversion Pitch:** Generates the 1-line rationale explaining why the clip converts scrollers.

**Model-Agnostic Backend:** The architecture runs instantly offline via high-fidelity local heuristics (zero API cost) and connects seamlessly via a single parameter to **Google Gemini Flash**, **OpenAI GPT-4o-mini**, or custom endpoints during live interviews.

---

## 3. Acquisition Funnel: Which Promos to Post First & Why

Not all promos serve the same purpose. Rather than a flat list, our ranker stratifies outputs into an actionable **3-Tier Marketing Funnel**:

| Funnel Tier | Target Audience & Channel | Primary Characteristics | Recommended Posting Strategy & Why |
| :--- | :--- | :--- | :--- |
| **Tier 1: High-Velocity Cold Ads** | Cold Scrollers (TikTok, IG Reels, YT Shorts) | Extreme 0–3s shock; universal tropes (altar abandonment, cruel family). | **Post 1st:** Lowest CPA. Stops cold scrollers with zero context needed. |
| **Tier 2: Escalation & Retargeting** | Warm Audiences (Watched > 50% of Ad 1) | Unbearable cliffhanger cut; life-or-death ultimatum, identity twist. | **Post 2nd:** Drives app installs to unlock Episode 2 and beyond. |
| **Tier 3: Organic Episodic Promos** | Active Series Followers & Community | Character chemistry, romance development, sub-plots. | **Post Later:** Organic social posts to sustain retention. |

### Top Ranked Promos (50-Episode Benchmark)
* **Rank #1: Ep 38 (00:45.50 → 01:07.00 | 21.5s)** — Score: **80/100**. Hook: *"What if I die here?"* Cliffhanger: *"I will not give them my husband."*
* **Rank #2: Ep 36 (02:23.20 → 03:20.75 | 57.5s)** — Score: **76/100**. Hook: *"What wedding?"* Cliffhanger: *"...their dead Duke is coming home."*
* **Rank #7: Ep 1 (01:12.40 → 01:35.50 | 23.1s)** — Score: **72/100**. Altar abandonment: *"Long enough to know he was never going to marry you."*

---

## 4. Quality Checking: Where Does the Tool Pick Badly?

Automated text analysis encounters predictable failure modes. We audited all 150 extracted promos and classified **4 systemic edge cases**:

1. **FM1: Late-Show Lore Bleed (Context Trap):** High cliffhanger score in late episodes (Ep 35+) that requires deep backstory a cold TikTok scroller doesn't know (e.g., Ep 46 decree on vagrant marriage legality). *Mitigation: Restrict Tier-1 ad budget to Episodes 1–10, or insert a 2-second on-screen context overlay card.*
2. **FM2: Vertical Pacing Lag:** Clips > 40s with sparse dialogue relying on silent staring that causes instant swipe-away on vertical feeds (e.g., Ep 21 atmospheric barn scene with only 3 lines across 40s). *Mitigation: Automated rule penalizes dialogue turn density < 0.15 turns/sec; editor trims silent pauses.*
3. **FM3: Subtle Opening Setup:** Clip starts on polite conversation 4 seconds before the conflict hits, missing the critical 3-second hook window (e.g., Ep 1 cathedral entry). *Mitigation: Snip opening 4 seconds; start directly in medias res on confrontation.*
4. **FM4: Physical vs. Lexical Disconnect:** Sarcastic or deadpan lines (*"You're a genius"*) that look dramatic in script text but are delivered as humor on screen. *Mitigation: Human editor verification step before pushing to ad managers.*

### Editorial Co-Pilot Workflow
The platform does not replace editors; it serves as an **editorial co-pilot**. Instead of watching 100 minutes of video, an editor reviews pre-ranked candidates with pre-filled timestamps and rationale, making 1-click Accept/Reject/Flag decisions in under 5 minutes.

---

## 5. Production Economics & Scaling to Every Show

* **Processing Speed:** 50 episodes parsed and scored in **2.28 seconds** on standard CPU (~4.5s for 100 episodes).
* **Token Efficiency:** NMS candidate windowing reduces raw token load by **95%** (evaluates ~150 candidates vs 3,700 blocks).
* **Unit Economics:** Less than **$0.005 (half a cent)** per 50-episode show on Gemini Flash. 100 shows per year costs under **$0.50 total**.
* **Zero GPU Requirement:** Pure CPU Python parsing; parallelizable across serverless workers.

---

## 6. AI Tooling Transparency & Where AI Got It Wrong
*(Required by Assignment Brief)*
* **Tools Used:** Antigravity / Gemini for regex scaffolding, heuristic design, and candidate prompt structuring.
* **Where AI Got It Wrong:** When prompted to generate promo candidates, AI initially suggested sliding windows based on raw token lengths. This caused timestamps to cut mid-sentence and hallucinated non-existent scene breaks. We overrode this by building a deterministic AST parser that binds cuts strictly to screenplay dialogue timestamps.

---

## 7. Deliverables & Interview Readiness
* **Interactive Dashboard:** Streamlit app (`app.py`) with 50-episode browser, live ZIP/TXT uploader for new shows, parameter sliders, human review buttons, and CSV/JSON/TXT export.
* **Raw Outputs:** Full unedited datasets in `outputs/raw_promos_all_episodes.json` and `raw_promos_all_episodes.csv`.
* **Interview Live-Run:** In the live interview, upload any unseen screenplay `.zip` or connect a proprietary API key; the system runs end-to-end in seconds.
