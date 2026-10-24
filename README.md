# `agy-arsenal` — Argon-4 Reasoning Booster for Gemini Flash (3.7 / 3.8+)

Make **Gemini 3.7 / 3.8 Flash (Medium & High)** think, decompose, verify, and follow strict instructions like **Gemini 4 Argon** in Google Antigravity—while stretching your weekly Argon 4 quota by **5x–8x**.

---

## Why Gemini Flash Disappoints by Default (And How This Fixes It)

| Flash Failure Mode | Why It Happens | How `agy-arsenal` Fixes It |
| :--- | :--- | :--- |
| **Context Amnesia (Recency Bias)** | By Turn 5+, Flash ignores top-of-prompt rules in `GEMINI.md` and fixates only on the last 1–2 tool outputs. | Uses Antigravity's `PreInvocation` hook to inject an **`ephemeralMessage` at the very bottom of the context** right before Flash generates `<thinking>`, then **auto-deletes it after the turn** (0 history bloat). |
| **Impulsive / Shallow First-Pass Thinking** | Flash optimizes for low latency—jumping straight to tool calls or code on its first hunch without checking files or edge cases. | Forces an XML-framed **4-Step Argon Thinking Gate** (`[DECOMPOSE]`, `[FACT VS. ASSUMPTION]`, `[RED-TEAM]`, `[VERIFICATION]`) inside Flash's native `<thinking>` block. |
| **Over-Planning on Tool Loops** | Naive `PreInvocation` hooks inject a huge planning prompt before every `read_file` step inside a turn. | **3-State Adaptive Transcript Tailing**: Inspects the last 64KB of `transcript.jsonl` in `<2ms` to distinguish **Turn Start** vs. **Error Recovery** vs. **Mid-Turn Tool Loop**. |
| **Premature Stopping ("Fake Done")** | Flash edits a file and immediately ends its turn without testing or verifying syntax/output. | Tracks unverified file edits in the current turn and warns Flash (or mechanically blocks premature stop in `split-plane` mode). |
| **Argon Quota Waste** | Running rules/hooks when you *are* using Argon 4 wastes tokens. | **Auto-Bypasses Argon 4**: Detects when `"Gemini 4 Argon"` is selected and outputs `{}` (0 tokens added). |

---

## Quick Start (macOS, Windows, Linux)

Clone this repository on any machine and run `install.py` (uses 100% Python 3 standard library—zero `pip` dependencies):

```bash
git clone git@github.com:galacticor/agy-arsenal.git
cd agy-arsenal

# Recommended Default: 3-State Adaptive PreInvocation Hook + GEMINI.md Gates + Architect Skill
python3 install.py

# Optional Split-Plane Mode: Also enables the Stop-Hook Guard for unverified code edits
python3 install.py --mode split-plane
```

### Check Status, Self-Test, or Uninstall

```bash
# Check installation status on the current PC
python3 install.py --status

# Run offline diagnostic self-tests
python3 hooks/argon_reasoning_hook.py --self-test

# Cleanly remove agy-arsenal (preserves all your other hooks and GEMINI.md rules)
python3 install.py --uninstall
```

---

## How the 3-State Adaptive `PreInvocation` Engine Works

When `hooks/argon_reasoning_hook.py` runs before a Gemini Flash model invocation, it reads the tail of the active `transcript.jsonl` and selects one of **3 precision prompts**:

1. **State 1 — `turn_start` (User just submitted a prompt)**
   Injects the full 4-step `<argon_reasoning_protocol mode="turn_start">` rubric forcing Flash to decompose requirements, separate verified facts from assumptions, red-team its own plan, and plan verification.
2. **State 2 — `error_recovery` (Last tool call returned a non-zero exit code / Traceback)**
   Injects `<argon_reasoning_protocol mode="error_recovery">`, forbidding blind flag guessing or superficial symptom patches and requiring a 1-sentence Root Cause Analysis in `<thinking>` first.
3. **State 3 — `unverified_edits` / `mid_turn` (Mid-turn tool iteration)**
   - If files were modified in the current turn (`edit_file` / `write_file`) and not yet verified via `run_command` or `read_file`, injects a compact reminder listing the exact unverified filenames.
   - Otherwise, injects a 1-sentence step anchor (~28 tokens) so Flash doesn't over-plan during routine file reads.

---

## Repository Structure

```text
agy-arsenal/
├── hooks/
│   └── argon_reasoning_hook.py          # 3-State Adaptive PreInvocation + Stop hook (0 dependencies)
├── rules/
│   └── GEMINI.argon-flash.md            # Algorithmic IF/THEN/NEVER execution gates merged into GEMINI.md
├── skills/
│   └── argon-architect-mode/
│       └── SKILL.md                     # On-demand 1-Turn Argon Architect -> Flash Workhorse skill
├── install.py                           # Cross-OS idempotent installer, status checker, and uninstaller
└── README.md
```
