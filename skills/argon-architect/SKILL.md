---
name: argon-architect
description: >-
  1-Turn Argon Blueprint + Automatic Flash Subagent Handoff (`/argon-architect`). Inspects the codebase in 1 parallel turn, writes an exact Implementation Manifest, and delegates execution to an Argon-Boosted Gemini Flash (`Model: "flash"`) subagent to save 85-95% of weekly Argon quota.
---

# `/argon-architect` — 1-Turn Argon Blueprint + Flash Workhorse Handoff

When invoked via `/argon-architect`, execute the **Architect → Workhorse** hybrid pattern to solve complex tasks with minimal Argon 4 quota burn:

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
  `[EFFORT: HIGH — Execute this exact Argon-4 Implementation Manifest using parallel tool batching (GATE 6), surgical edits (GATE 3), and mandatory verification (GATE 5)]`
- **Manual Handoff (if the user explicitly asks for "blueprint only" to switch the UI model dropdown themselves)**:
  Output the complete **Implementation Manifest** in the chat so the user can switch the Antigravity model dropdown to **Gemini 3.8 Flash (Medium)** and reply `"Execute the blueprint"`.
