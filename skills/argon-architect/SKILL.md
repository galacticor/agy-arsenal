---
name: argon-architect
description: >-
  1-Turn Argon Blueprint + Automatic Flash Subagent Handoff (`/argon-architect`). Inspects the codebase in 1 parallel turn, writes an exact Implementation Manifest, and delegates execution to an Argon-Boosted Gemini Flash (`Model: "flash"`) subagent to save 85-95% of weekly Argon quota.
---

# `/argon-architect` — 1-Turn Argon Blueprint + Flash Workhorse Handoff

When invoked via `/argon-architect`, execute the **Architect → Workhorse** hybrid pattern to solve complex tasks with minimal Argon 4 quota burn:

---

## Step 0: Quota Break-Even Gate (Prevent Subagent Overhead on Trivial Tasks)

- **Fast-Path Rule (`<= 2` Tool Turns)**: If the task is a trivial 1-file edit (`<30` lines changed) with no multi-file debugging, test-fix loop, or `.pptx`/`.docx`/`.xlsx` generation, **DO NOT spawn a subagent** (spawning costs 2 Argon turns: launch + wakeup). Execute the edit and verification directly in 1–2 turns.
- **Subagent Handoff (`>= 3` Tool Turns)**: For all multi-file changes, bug investigations, test suites, or Office document builds, proceed to Step 1.

---

## Step 1: 1-Turn Parallel Inspection & Architectural Blueprint

1. **Batch All Inspection Reads in 1 Turn (`GATE 6`)**:
   - Call `read_file` / `grep_search` in parallel across all relevant target files in a single turn.
2. **Formulate the Implementation Manifest**:
   - **Root Cause & Red-Team Analysis**: Identify the exact bugs, architectural bottlenecks, or analytical traps.
   - **Exact File & Line-Number Diff Plan**: Specify the exact functions, signatures, and logic changes required so the executor has zero ambiguity.
   - **Verification Suite**: Define the exact test or CLI verification command (`pytest`, `unittest`, `office_view_hook.py --summary-only`, etc.).

---

## Step 2: Delegate Execution to `Model: "flash"` Subagent (or Output Blueprint)

- **Default (Autonomous Handoff)**:
  Immediately spawn a `Model: "flash"` subagent (`invoke_subagent` with `TypeName: "self"`, `Model: "flash"`, `Role: "Argon-Boosted Flash Executor"`) and pass the **Implementation Manifest** prefixed with:
  ```text
  [EFFORT: HIGH — Execute this exact Argon-4 Implementation Manifest using parallel tool batching (GATE 6), surgical edits (GATE 3), and mandatory verification (GATE 5).
  REQUIRED COMPLETION RECEIPT: In your final reply, return ONLY:
  1. Files modified (with clickable file:// line ranges)
  2. Exact verification command(s) run, exit code, and concise PASS/FAIL output
  3. Any edge-case findings or remaining blockers.]
  ```
- **Manual Handoff (if the user explicitly asks for "blueprint only" to switch the UI model dropdown themselves)**:
  Output the complete **Implementation Manifest** in the chat so the user can switch the Antigravity model dropdown to **Gemini 3.8 Flash (Medium)** and reply `"Execute the blueprint"`.

---

## Step 3: Risk-Tiered Sign-Off & Bounded Loop (Upon Subagent Wakeup)

When the Flash subagent finishes and wakes up the Argon main agent:
1. **Default `0`-Tool Sign-Off (When Receipt & Deterministic Tests Pass)**:
   - **Never re-run passing `run_command` tests** that the subagent already executed.
   - For standard refactors, boilerplate, or deterministically tested changes where the **Completion Receipt** confirms exit code `0` / `PASS`, sign off and present the results immediately in **0 tool calls**.
2. **Scoped Spot-Check Allowed for High-Complexity / Critical Logic**:
   - If the task involves subtle algorithmic logic, concurrency/security invariants, or executive prose/layout where unit tests cannot guarantee semantic fidelity—or if the subagent's receipt looks ambiguous—you **may** perform a single batched `read_file` using `StartLine`/`EndLine` targeting **only the modified line ranges** reported in the receipt (avoid dumping full files).
3. **Bounded Follow-Up Loop (Max 1 Retry via `send_message`)**:
   - If the receipt or your scoped spot-check reveals a bug, failed test, or spec drift, **DO NOT** spawn a new subagent. Call `send_message` targeting the **existing** subagent's `conversationId` with a concise corrective delta (unless it is a `<10`-line 1-edit tweak that is faster to apply directly).
