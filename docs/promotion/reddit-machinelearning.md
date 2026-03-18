# Reddit — r/MachineLearning

## Title
```
[Project] Engram-AI: Episodic memory with causal structure for LLM agents — experiences crystallize into skills via vector clustering + LLM extraction
```

## Body
```
**GitHub:** https://github.com/kajaha06251020/Engram-AI | Apache 2.0 | Python 3.10+

---

### Motivation

Existing memory systems for LLM agents largely follow a retrieval-augmented generation (RAG) paradigm: store text, embed it, retrieve by similarity. This works well for factual recall but doesn't capture the *causal structure* of agent behavior — what the agent did, in what context, and whether the outcome was good or bad.

Engram-AI models agent memory as a sequence of **experiences** with explicit valence:

```
Experience = (action, context, outcome, valence ∈ [-1.0, 1.0])
```

This is inspired by the concept of neural engrams — physical memory traces formed by experience in biological neural systems — and by reinforcement learning's notion of reward signals attached to state-action pairs.

---

### Architecture

**Storage layer:** ChromaDB with two collections — experiences (with valence metadata) and skills. Queries use cosine similarity with valence-based partitioning into `{best, avoid}`.

**Crystallization pipeline:**
1. Retrieve all experiences from ChromaDB
2. Cluster by cosine similarity (threshold-based, not k-means — k is unknown a priori)
3. For clusters with ≥ `min_experiences` items and average |valence| ≥ `min_confidence`: prompt LLM to extract a generalizable rule
4. Store as `Skill(rule, context_pattern, confidence, evidence_count)`
5. Fallback: keyword-frequency extraction when no LLM available

**Valence detection:** Three-tier pipeline — keyword matching (EN+JP lexicon) → LLM classification → default 0.3. The two-phase recording pattern (record action immediately, detect valence from subsequent human response) enables real-time operation in hook-based systems.

**Evolution:** Learned skills are serialized to agent configuration files (CLAUDE.md, AGENTS.md, system prompts) via adapter-specific formatters, with idempotent delimiter-based updates.

---

### Key design decisions

**Why not just use RL?** The system targets interactive agents where reward is human feedback, not a defined reward function. Valence is inferred from natural language, not computed.

**Why ChromaDB?** Simplicity and local-first operation. The storage layer is abstracted (`BaseStorage`) — any vector DB can be substituted.

**Why explicit crystallization instead of continuous learning?** Deliberate crystallization gives the agent (and user) a checkpoint to inspect and validate what was learned before it influences future behavior. Continuous implicit updates felt too opaque.

**Confidence decay:** Skills decay over time if not reinforced, preventing stale rules from persisting indefinitely. Prediction hit/miss tracking adjusts confidence based on real-world validation.

---

### Limitations and open questions

- Crystallization quality is strongly LLM-dependent. The keyword fallback produces functional but generic rules.
- Valence is a scalar; richer affect models (arousal, dominance) might capture more nuance but add complexity.
- No formal evaluation benchmarks yet — this is early-stage infrastructure work.
- The clustering approach is greedy and threshold-based; better clustering algorithms would improve skill quality.

---

### Install

```bash
pip install engram-forge                    # core (ChromaDB, no LLM required)
pip install "engram-forge[claude]"          # + Anthropic SDK
pip install "engram-forge[full]"            # + MCP server + dashboard
```

Interested in feedback from the ML community, particularly around the crystallization approach and whether the scalar valence model is sufficient for complex agent behavior.
```

## Flair
```
[Project]
```
