---
name: apex-architect
description: >-
  Two-stage Architect -> Executor orchestrator (`/apex-architect`). Runs 1-turn parallel repo inspection, synthesizes a falsified `<implementation_manifest>` (causal trace, invariants, line-level contracts, adversarial checks), and hands off to a locked `apex-worker` (`Model: "flash"`) or escalates to `/agentspace-advisor` (Carbon).
---

# `/apex-architect` — 1-Turn Falsified Blueprint + Locked Worker Handoff

Use `/apex-architect` for complex, multi-file, or high-blast-radius tasks requiring upfront codebase synthesis before mutation. (Role boundary: two-stage Planner $\rightarrow$ Executor orchestration — use `/apex-exec` for routine direct execution; escalate to `/agentspace-advisor` (Carbon) when architecture is under-determined.)

---

## Stage 1: 1-Turn Parallel Inspection & Falsified Manifest

1. **Single-Turn Parallel Read + Worker Registration**:
   - Batch all `read_file` and `grep_search` calls across target files, callers/callees, schemas, and tests in Turn 1.
   - If delegating autonomously and `apex-worker` is not yet registered, include `define_subagent` in the same Turn 1 batch:
     ```text
     Name: "apex-worker" | EnableWriteTools: true | EnableMCPTools: true | EnableSubagentTools: false
     Description: "Contract-bound workhorse executor with invariant preservation, parallel batching, and 2-strike Carbon circuit breaker."
     SystemPrompt: "Execute the provided <implementation_manifest> verbatim. Batch reads/edits in parallel, use surgical edit_file hunks (zero TODOs), preserve every listed invariant, dry-trace the adversarial counterexample in <thinking> (<120 words), and run all verification commands. On test failure, formulate 2 hypotheses from the backward causal trace before patching. If 2 fix attempts fail or an unlisted invariant breaks, STOP and return [BLOCKED_ESCALATE_CARBON] with exact tracebacks."
     ```
2. **Architect `<thinking>` Audit (`<200 words`)**:
   - Trace `[CAUSAL_TRACE]` (`Symptom <- Transform <- Root`), test competing `[HYPOTHESES]`, lock `[INVARIANTS]` (signatures, SQL row/sum conservation, PIT cutoffs, concurrency safety), dry-trace 1 `[COUNTEREXAMPLE]`, and score `[CONFIDENCE: 0.00-1.00]`.
   - **Pre-Handoff Gate**: If `CONFIDENCE < 0.70` or $\ge 4$ coupled subsystems exhibit conflicting invariants, **ABORT Stage 2** and escalate to `/agentspace-advisor` (Carbon).
3. **Synthesize `<implementation_manifest>`**:
   - **Root Cause & Red-Team Findings**: Exact causal mechanism + prompt/math/domain traps falsified.
   - **Exact File, Symbol & Line Contracts**: Target paths, function signatures, and unambiguous surgical diff specs.
   - **Invariants & Adversarial Guardrails**: Explicit pre/post conditions and 3 concrete edge cases to preserve.
   - **Deterministic Verification Suite**: Exact commands (`pytest -q --tb=short`, `python3 -m py_compile`, `office_view_hook.py --summary-only`).

---

## Stage 2: Controlled Executor Handoff

- **Default (Autonomous Subagent Handoff — on a Frontier Model)**:
  Call `invoke_subagent` (`TypeName: "apex-worker"`, `Model: "flash"`, `Role: "Contract-Bound Apex Executor"`) with `[EFFORT: HIGH — Execute this <implementation_manifest> with parallel batching and zero invariant drift]\n` + manifest. Wait for completion and verify command outputs.
- **Local Non-Frontier Self-Split (if invoked on Flash 3.7/3.8 or Neon/Hydrogen)**:
  Emit the complete `<implementation_manifest>` in Turn 1 *before* any write tool call, then execute Stage 2 in-session strictly bound to your manifest.
- **Manual UI Handoff (if user requests `"blueprint only"`)**:
  Output `<implementation_manifest>` inline so the user can switch the model dropdown to **Flash / Neon / Hydrogen** and reply `"Execute the blueprint"`.

---

## Stage 3: Escalation Trigger to `/agentspace-advisor` (Carbon)

Immediately escalate to `/agentspace-advisor` with `[CARBON_ESCALATION]` (manifest + falsified hypotheses + raw tracebacks) if Stage 1 `CONFIDENCE < 0.70` or `apex-worker` returns `[BLOCKED_ESCALATE_CARBON]`.
