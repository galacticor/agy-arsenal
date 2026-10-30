---
name: argon-architect-mode
description: Architect-Editor quota optimization and Argon-4 deep reasoning workflow. Trigger when planning complex multi-file changes to hand off from Gemini 4 Argon to Gemini Flash (3.7/3.8 Medium/High), or when forcing Gemini Flash to execute a deep architectural specification and verification checklist.
---

# Argon Architect → Flash Workhorse Workflow (`argon-architect-mode`)

Use this skill when conserving weekly **Gemini 4 Argon** quota on complex engineering, debugging, or analytical tasks, or when operating **Gemini Flash (3.7 / 3.8 Medium or High)** on a multi-file task that requires Argon-grade architectural rigor.

---

## 1. Phase A: The 1-Turn Argon Blueprint (When Running on Argon 4)

If the user asks for a **plan, blueprint, or spec** to execute later on Gemini Flash:
1. **Do NOT burn multiple turns writing boilerplate code.**
2. Inspect the critical files/schemas in a single focused batch of read-only tool calls.
3. Produce a self-contained **Implementation Manifest** (either inline or in `<artifactDir>/implementation_plan.md`) containing:
   - **Root Cause / Architectural Diagnosis**: Why the current system behaves as it does.
   - **Exact File & Symbol Manifest**: Every file path and function/class to create or modify.
   - **Step-by-Step Diff Specification**: Exact signatures, data structures, and state transitions so Flash does not have to guess.
   - **Edge Cases & Failure Modes**: 3 specific traps the executor must guard against.
   - **Deterministic Verification Commands**: Exact shell commands (`pytest`, `node --check`, dry-run commands) to prove completion.

---

## 2. Phase B: Flash High-Rigor Execution (When Running on Gemini Flash)

When executing a complex task on **Gemini Flash (3.7 / 3.8 Medium or High)**:

### Step 1 — Pre-Flight `<thinking>` Audit (Staff Principal / Argon-4 Rigor)
Before calling your first mutation tool (`edit_file` / `write_file`), explicitly verify in `<thinking>`:
- `[DECOMPOSE & INVARIANTS]`: Have I listed every requirement, negative constraint, and state invariant?
- `[ZERO-GUESSING & BLAST RADIUS]`: Have I read the exact lines around every target edit AND inspected upstream/downstream callers, shared types, and schemas?
- `[SELF-ADVERSARIAL & EDGE-CASE AUDIT]`: Where would this fail in production or under scale? Have I guarded against division-by-zero, `null`/`None`/`NaN` propagation, empty partitions, race conditions, and memory blowups?

### Step 2 — Incremental Surgical Execution
- Prefer surgical `edit_file` blocks over full-file `write_file` overwrites.
- Never leave placeholder comments (`// TODO`, `pass # implement later`).

### Step 3 — Mandatory Verification Gate
Before finishing your turn:
1. Run the verification command, test suite, or syntax check (`python3 -m py_compile`, `node --check`, unit tests, or CLI `--self-test`).
2. If an error occurs, perform **Root Cause Analysis** (read the traceback + offending lines) before patching.
