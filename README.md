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
| **Progressive Disclosure Blindness ("Shortcut Bias")** | Because Flash knows basic `python-pptx` / `python-docx` syntax from pre-training, it skips reading `SKILL.md` (`pptx`, `executive-slides`, `docx`) and produces generic stacked-box templates instead of consulting-grade layouts. | **`GATE 7` (`unread_skills_gate` + `<argon_pptx_design_mandate>`)**: Detects `.pptx`/`.docx`/`.xlsx` tasks, forces Flash to read the matching `SKILL.md` in Turn 1, and injects McKinsey Action Title, asymmetric 2-column grid, and `Cambria`/`Calibri` table formatting mandates. |
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

## How the Adaptive `PreInvocation` Engine Works

When `hooks/argon_reasoning_hook.py` runs before a Gemini Flash model invocation, it reads the tail of the active `transcript.jsonl` and selects the right precision prompt:

1. **State 1 — `turn_start` / `turn_start+pptx_design` (User just submitted a prompt)**
   Injects the 5-step `<argon_reasoning_protocol mode="turn_start">` rubric forcing Flash to decompose requirements, separate verified facts from assumptions, red-team its own plan, batch `read_file` on required `SKILL.md` files (`GATE 7`), and batch independent tool calls (`GATE 6`). When `.pptx` / presentation creation is detected, it also appends `<argon_pptx_design_mandate>`.
2. **State 2 — `error_recovery` (Last tool call returned a non-zero exit code / Traceback)**
   Injects `<argon_reasoning_protocol mode="error_recovery">`, forbidding blind flag guessing or superficial symptom patches and requiring a 1-sentence Root Cause Analysis in `<thinking>` first.
3. **State 3 — `unread_skills_gate` (Domain skill required by prompt has not yet been read)**
   If the prompt involves `.pptx`, `.docx`, or `.xlsx` and Flash hasn't called `read_file` on the matching `SKILL.md`, blocks generic defaults and instructs Flash to batch-read the required `SKILL.md` files immediately.
4. **State 4 — `unverified_edits` / `mid_turn` (Mid-turn tool iteration)**
   - If files were modified in the current turn (`edit_file` / `write_file`) and not yet verified via `run_command` or `read_file`, injects a compact reminder listing the exact unverified filenames.
   - Otherwise, injects a 1-sentence step anchor (~28 tokens) so Flash doesn't over-plan during routine file reads.

---

## `/` Slash Commands in Antigravity Chat

In addition to running **100% automatically** in the background whenever you select **Gemini Flash (3.7 / 3.8 Medium or High)** from the model dropdown, `agy-arsenal` installs two first-class `/` slash-command skills into `~/.gemini/config/skills/` that you can type directly in the Antigravity chat input box:

| Slash Command | When to Use It | What It Does |
| :--- | :--- | :--- |
| **`/argon-flash <task>`** | You want to run a task with Argon-Boosted Flash—**even if your main chat is currently set to Argon 4**. | - **If your main chat is on Argon 4**: Automatically defines and spawns an autonomous `argon-flash-worker` subagent (`Model: "flash"`, `[EFFORT: HIGH]`) to do all the heavy coding, `.pptx`, `.docx`, or debugging in the background at **25x lower quota cost**.<br>- **If your main chat is already on Flash**: Enforces the full 6-Gate Argon-4 Execution Protocol directly in the current session. |
| **`/argon-architect <task>`** | Complex multi-file architecture, subtle bug hunting, or executive deliverable packs. | - **Step 1 (1-Turn Argon Blueprint)**: Reads all target files in 1 parallel batch, red-teams the requirements, and writes an exact **Implementation Manifest** (`File + Line Numbers + Diff Spec + Test Command`).<br>- **Step 2 (Flash Workhorse Handoff)**: Automatically delegates the blueprint to a `Model: "flash"` subagent to execute and verify. |

---

## Repository Structure

```text
agy-arsenal/
├── plugin.json                          # Native Antigravity plugin manifest
├── hooks/
│   └── argon_reasoning_hook.py          # 3-State Adaptive PreInvocation + Stop hook (0 dependencies)
├── rules/
│   └── GEMINI.argon-flash.md            # 7 Algorithmic IF/THEN/NEVER execution gates merged into GEMINI.md
├── skills/
│   ├── argon-flash/
│   │   └── SKILL.md                     # `/argon-flash` slash command (direct or subagent launcher)
│   ├── argon-architect/
│   │   └── SKILL.md                     # `/argon-architect` slash command (1-turn blueprint -> Flash worker)
│   └── argon-architect-mode/
│       └── SKILL.md                     # Legacy/full skill alias
├── install.py                           # Cross-OS idempotent installer, status checker, and uninstaller
└── README.md
```
