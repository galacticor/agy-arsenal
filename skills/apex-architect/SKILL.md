---
name: apex-architect
description: >-
  Two-stage Architect -> Executor orchestrator (`/apex-architect`). Runs 1-turn parallel repo inspection, synthesizes a falsified `<implementation_manifest>` (causal trace, invariants, line-level contracts, adversarial checks), and hands off to a locked `apex-worker` (`Model: "flash"`) or escalates to `/agentspace-advisor` (Carbon).
---

# `/apex-architect` — 1-Turn Falsified Blueprint + Locked Worker Handoff

Use `/apex-architect` for complex, multi-file, or high-blast-radius tasks requiring upfront codebase synthesis before mutation. (Role boundary: two-stage Planner $\rightarrow$ Executor orchestration — use `/apex-exec` for routine direct execution; escalate to `/agentspace-advisor` (Carbon) when architecture is under-determined.)

---

## Stage 1: Schema-Locked Verbatim Inspection & Falsified Manifest

1. **Pre-Read Worker Registration + Verbatim Parallel Read**:
   - **Schema Lock First**: If delegating autonomously on a Frontier model and `apex-worker` is not yet registered, call `define_subagent` **alone in Turn 0** *before* reading repo files (batching `define_subagent` with `read_file` mutates Turn 2's tool header and invalidates all Turn 1 file-read caches):
     ```text
     Name: "apex-worker" | EnableWriteTools: true | EnableMCPTools: true | EnableSubagentTools: false
     Description: "Contract-bound workhorse executor with invariant preservation, parallel batching, and 2-strike Carbon circuit breaker."
     SystemPrompt: "Execute the provided <implementation_manifest> verbatim. Batch reads/edits in parallel, use surgical edit_file hunks (zero TODOs), preserve every listed invariant, dry-trace the adversarial counterexample in <thinking> (<120 words), and run all verification commands. On test failure, formulate 2 hypotheses from the backward causal trace before patching. If 2 fix attempts fail or an unlisted invariant breaks, STOP and return [BLOCKED_ESCALATE_CARBON] with exact tracebacks."
     ```
   - **Verbatim Ground Truth (Zero Lossy Summaries)**: Batch `read_file` and `grep_search` across exact target files, upstream callers, downstream consumers, SQL schemas, and tests. *(Only if candidate scope exceeds `>15` unknown files, run a fast locator grep/scout to return exact `path:start-end` coordinates, then read those verbatim slices directly in Architect.)*
2. **Architect `<thinking>` Audit (`<200 words`)**:
   - Trace `[CAUSAL_TRACE]` (`Symptom <- Transform <- Root`), test competing `[HYPOTHESES]`, lock `[INVARIANTS]` (signatures, SQL row/sum conservation, PIT cutoffs, concurrency safety), dry-trace 1 `[COUNTEREXAMPLE]`, and score `[CONFIDENCE: 0.00-1.00]`.
   - **Pre-Handoff Gate**: If `CONFIDENCE < 0.70` or $\ge 4$ coupled subsystems exhibit conflicting invariants, **ABORT Stage 2** and escalate to `/agentspace-advisor` (Carbon).
3. **Synthesize `<implementation_manifest>`**:
   - **Root Cause & Red-Team Findings**: Exact causal mechanism + prompt/math/domain traps falsified.
   - **Exact File, Symbol & Line Contracts**: Target paths, function signatures, and unambiguous surgical diff specs.
   - **Invariants & Adversarial Guardrails**: Explicit pre/post conditions and 3 concrete edge cases to preserve.
   - **Deterministic Verification Suite**: Exact commands (`pytest -q --tb=short`, `python3 -m py_compile`, `office_view_hook.py --summary-only`).

---

## Stage 2: Cache-Safe Executor Handoff & Two-Tier Verification

- **Persist Manifest First**: Write `<implementation_manifest>` to `.apex-orch/manifest.md` (or pass inline if `<1,500` tokens) so zero contract detail is ever truncated or lost across retries/escalations.
- **Default (Autonomous Subagent Handoff — on a Frontier Model)**:
  1. **Tier 1 Wave (`<180s` Target to Preserve Warm Architect Cache)**: Call `invoke_subagent` (`TypeName: "apex-worker"`, `Model: "flash"`, `Role: "Contract-Bound Apex Executor"`) with `[EFFORT: HIGH — Execute this <implementation_manifest> with parallel batching and zero invariant drift]\n` + manifest, instructing the worker to apply all edits and run **compile + targeted unit/caller invariant checks (`<180s`)** so Architect wakes inside the `300s` KV-cache window.
  2. **Tier 2 Mandatory Full-Suite Outer Gate**: Immediately upon worker pass, run the **full cross-module regression/invariant suite** redirected to `.apex-orch/gate.log` (printing only exit code + failing summary tail) before accepting completion.
- **Local Non-Frontier Self-Split (if invoked on Flash 3.7/3.8 or Neon/Hydrogen)**:
  Emit the complete `<implementation_manifest>` in Turn 1 *before* any write tool call, execute edits in-session strictly bound to your manifest, and run both Tier 1 and Tier 2 verification gates.
- **Manual UI Handoff (if user requests `"blueprint only"` or when Tier 1 build unavoidably exceeds `240s`)**:
  Save `.apex-orch/manifest.md` and output `<implementation_manifest>` inline so the user can switch the model dropdown to **Flash / Neon / Hydrogen** and reply `"Execute .apex-orch/manifest.md"`.

---

## Stage 3: Escalation Trigger to `/agentspace-advisor` (Carbon)

Immediately escalate to `/agentspace-advisor` with `[CARBON_ESCALATION]` (manifest + falsified hypotheses + raw tracebacks) if Stage 1 `CONFIDENCE < 0.70` or `apex-worker` returns `[BLOCKED_ESCALATE_CARBON]`.
