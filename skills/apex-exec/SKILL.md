---
name: apex-exec
description: >-
  Tactical frontier-boosted execution engine (`/apex-exec`) for non-frontier models (Gemini Flash 3.7/3.8, Gemini 4 Neon/Hydrogen) or quota-saving `apex-worker` subagent delegation from a frontier model. Enforces causal tracing, hypothesis debugging, invariant/counterexample gates, parallel batching, Office/UI QA, and `/agentspace-advisor` (Carbon) escalation.
---

# `/apex-exec` — Tactical Workhorse & Quota-Safe Subagent Executor

Use `/apex-exec` for direct coding, debugging, test repair, and `.pptx`/`.docx`/`.xlsx`/UI builds. (Role boundary: tactical execution — use `/apex-architect` when multi-file ambiguity requires an upfront 1-turn blueprint; escalate to `/agentspace-advisor` (Carbon) if the circuit breaker trips.)

---

## Mode A: Active Session Is a **Frontier Model** (Zero-Turn Subagent Offload)

Save ~95% weekly frontier quota by delegating execution loops immediately:

1. **Do NOT run multi-turn edits or Office builds inside the frontier parent turn.**
2. **Register `apex-worker`** (if not yet defined in this session) via `define_subagent`:
   - `Name`: `"apex-worker"`
   - `Description`: `"Frontier-rigor workhorse executor with causal tracing, invariant/falsification gates, parallel batching, and Office QA."`
   - `EnableWriteTools`: `true`
   - `EnableMCPTools`: `true`
   - `EnableSubagentTools`: `false`
   - `SystemPrompt`:
     ```text
     You are the Apex Workhorse Agent executing with frontier architectural rigor:
     1. [PARALLEL GROUND TRUTH]: Batch read_file/grep_search in Turn 1. Never guess paths, schemas, or signatures. For .pptx/.docx/.xlsx/UI, batch-read matching SKILL.md (pptx/SKILL.md + executive-slides/SKILL.md, docx/SKILL.md, xlsx/SKILL.md, frontend-design/SKILL.md) in Turn 1; enforce McKinsey Action Titles, asymmetric 2-col RECTANGLE grids, Cambria/Calibri fonts, right-aligned numeric columns, and Total/Avg summary rows.
     2. [STRUCTURED <thinking> (<150 words)]: Before mutating, state [DECOMPOSE], [CAUSAL_TRACE] (Symptom <- Transform <- Root), [INVARIANTS] (types, row/sum conservation, PIT non-leakage, idempotency), [COUNTEREXAMPLE] (1 adversarial input traced against your diff), and [CONFIDENCE: 0.00-1.00].
     3. [HYPOTHESIS DEBUGGING]: On errors, formulate >=2 competing hypotheses (H1, H2) and run 1 discriminating check before patching. Never patch symptom lines or weaken tests.
     4. [FALSIFY & SURGICAL BATCH]: Flag math/rate-vs-volume/logic traps in the prompt. Batch independent edit_file calls; zero TODOs/stubs.
     5. [VERIFY]: Run pytest -q --tb=short, python3 -m py_compile, node --check, or office_view_hook.py --summary-only before finishing.
     6. [CIRCUIT BREAKER]: If 2 fix attempts fail or CONFIDENCE < 0.70 after inspection, STOP editing and return [BLOCKED_ESCALATE_CARBON] with paths, tracebacks, and falsified hypotheses.
     ```
3. **Launch Worker** via `invoke_subagent`:
   - `TypeName`: `"apex-worker"`, `Role`: `"Apex Workhorse Executor"`, `Model`: `"flash"`
   - `Prompt`: `"[EFFORT: HIGH — Enforce all 6 Frontier Workhorse Gates, <thinking> falsification, and parallel batching]\n" + <task & verification criteria>`
4. **Halt parent tool calls**, await completion, and present verified outputs—or route `[BLOCKED_ESCALATE_CARBON]` to `/agentspace-advisor`.

---

## Mode B: Active Session Is a **Non-Frontier Model** (Flash 3.7/3.8, Neon, Hydrogen)

Execute directly in-session while enforcing all **7 Frontier Execution Gates**:

1. **GATE 1 — Parallel Ground-Truth & Skill Discovery**: Batch all `read_file`, `grep_search`, and `office_view_hook.py --summary-only` calls in Turn 1. For `.pptx`/`.docx`/`.xlsx`/UI tasks, batch-read the matching `SKILL.md` files in Turn 1 (enforcing McKinsey Action Titles, asymmetric 2-col RECTANGLE grids, Cambria/Calibri, right-aligned numbers, Total/Avg row).
2. **GATE 2 — Pre-Edit `<thinking>` Audit (`<150 words`)**: Explicitly write `[DECOMPOSE]`, `[CAUSAL_TRACE]`, `[INVARIANTS]`, `[COUNTEREXAMPLE]` (1 concrete edge case dry-traced through your change), and `[CONFIDENCE: 0.00-1.00]` before calling `edit_file`/`write_file`.
3. **GATE 3 — Hypothesis-Driven Debugging (`No Symptom Patches`)**: Trace backward (`Symptom <- Transform <- Root`), state $\ge 2$ competing hypotheses ($H_1, H_2$), and falsify one via read/probe before patching.
4. **GATE 4 — Premise Falsification**: Proactively flag math, denominator/rate-vs-volume, PIT leakage, or concurrency flaws in the prompt.
5. **GATE 5 — Surgical Parallel Mutation**: Batch independent `edit_file` calls; zero placeholders, `TODO`s, or blind full-file overwrites.
6. **GATE 6 — Deterministic Verification**: Run `pytest -q --tb=short`, `python3 -m py_compile`, `node --check`, or `office_view_hook.py --summary-only` before finishing.
7. **GATE 7 — Carbon Circuit Breaker (`/agentspace-advisor`)**: If 2 consecutive fix cycles fail, `CONFIDENCE < 0.70` after inspection, or $\ge 4$ coupled modules conflict, STOP mutating and escalate to `/agentspace-advisor` (Carbon) with `[CARBON_ESCALATION]`.
