---
name: apex-think
description: >-
  Ambient frontier reasoning kernel for non-frontier models (Gemini Flash 3.7/3.8, Gemini 4 Neon/Hydrogen) and quota-saving blueprint synthesis. Enforces structured thinking, causal tracing, hypothesis-driven debugging, invariant checking, counterexample falsification, uncertainty calibration, and circuit-breaker escalation to /agentspace-advisor (Carbon).
---

# Frontier Reasoning Kernel (`/apex-think`)

Auto-apply this cognitive protocol on complex multi-file edits, SQL/analytical pipelines, concurrency, or root-cause debugging. (Role boundary: pure reasoning & verification kernel — use `/apex-exec` for direct worker/Office execution, `/apex-architect` for 1-turn subagent handoff, and `/agentspace-advisor` when blocked.)

## 0. Model-Aware Harness Routing (Low vs. Medium)

Route tasks after a 1-turn read-only triage (`F` = touched files, `M` = disjoint parallel modules, `R` = risk/novelty `0|1`, `S` = consecutive failure strikes):
- **T0 (`F == 1`, `LOC <= 40`, `R == 0`):** Direct `/apex-exec` (`edit_file` + deterministic test/compile gate). Skip `/apex-orchestrate`.
- **T1 (`2 <= F <= 3`, `M == 1`, `R == 0`):**
  - On **Hydrogen/Neon Low:** `/apex-think` -> **`/apex-architect`** (local 1-turn manifest + `flash` worker, zero Agentspace latency).
  - On **Hydrogen/Neon Medium:** `/apex-think` -> `/apex-exec` directly.
- **T2 (`R == 1` or `S >= 2` — hard problem-solving / 2-strike fail):** `/apex-think` -> **`/agentspace-advisor` (Carbon)** -> `/apex-exec`.
- **T3 (`F >= 4` and `M >= 2` disjoint):**
  - **Standard (`R == 0`):** `/apex-think` -> `/apex-orchestrate` (`2-4` worktrees).
  - **Complex (`R == 1` or cross-module coupling):** `/apex-think` -> **`/agentspace-advisor` (Carbon)** (lock shared interfaces & disjoint ownership) -> **`/apex-orchestrate`** (`2-4` worktrees).

---

## 1. Mandatory Pre-Mutation `<thinking>` Protocol (`<200 words`)

Before your first `edit_file`/`write_file` call—and after any failed command—write concrete values (never yes/no rubber stamps) in `<thinking>`:

```text
[DECOMPOSE] Deliverables: <exact outputs> | Non-goals/Constraints: <untouched boundaries>
[CAUSAL_TRACE] Symptom <- Intermediate Transform <- Root Producer (verified via read/grep; never patch crash symptoms)
[HYPOTHESES] H1: <cause A> | H2: <cause B> | Discriminating Check: <1 read/command to falsify H1 or H2 before editing>
[INVARIANTS] Must preserve: <API/type signatures | SQL row-count & sum conservation | point-in-time (as_of) non-leakage | lock/idempotency order>
[COUNTEREXAMPLE] Adversarial input: <empty/0-row, None/NaN, duplicate key, boundary timestamp, race, or rate-vs-volume skew> -> Trace result: <pass/fail>
[CALIBRATE] CONFIDENCE: <0.00-1.00> | UNVERIFIED: <paths, columns, or behaviors still unconfirmed>
```

---

## 2. Execution & Diagnostic Discipline

1. **Parallel Ground-Truth First**: Batch all `read_file` and `grep_search` calls (target lines + upstream callers + downstream consumers) in Turn 1. Any unverified path, schema column, or function signature forces `CONFIDENCE < 0.70` until read.
2. **Hypothesis-Driven Error Recovery**: On non-zero exit or test failure, NEVER blind-retry, swallow exceptions (`except Exception: pass`), or weaken test assertions. Formulate $H_1, H_2$ from the exact traceback line, run 1 read/diagnostic probe to falsify one hypothesis, then patch the root producer.
3. **Anti-Sycophancy & Premise Falsification**: Challenge flawed prompt assumptions (Simpson's paradox, rate-vs-volume mix shifts, survivorship/future leakage, off-by-one window bounds) with concrete counterexamples before mutating code.
4. **Surgical Parallel Edits**: Batch independent `edit_file` hunks; zero `TODO`s, stubs, or unnecessary full-file overwrites.
5. **Deterministic Verification Gate**: Run `pytest -q --tb=short`, `python3 -m py_compile`, `node --check`, or query invariant checks before concluding.

---

## 3. Hard Circuit Breaker → Escalate to `/agentspace-advisor` (Carbon)

Immediately **STOP mutating files** and invoke/recommend `/agentspace-advisor` when ANY trigger fires:
1. **2-Strike Failure**: 2 consecutive fix/verification cycles fail on the same underlying defect.
2. **Epistemic Floor**: `CONFIDENCE < 0.70` persists after reading local files, schemas, and tests.
3. **High-Blast-Radius Conflict**: Changes span $\ge 4$ coupled modules, async/locking state machines, auth/token boundaries, or irreconcilable invariants.

Emit a compact `[CARBON_ESCALATION]` packet containing: (1) Exact target paths & line ranges, (2) Falsified hypotheses ($H_1, H_2$) + raw tracebacks, and (3) The exact invariant conflict or architectural decision needed from Carbon.
