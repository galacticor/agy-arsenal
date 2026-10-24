#!/usr/bin/env python3
"""
Argon-4 Reasoning Booster Hook for Google Antigravity (Gemini Flash 3.7 / 3.8+)

Bridges the reasoning, instruction-following, and verification gap between
Gemini Flash (Medium/High) and Gemini 4 Argon using Antigravity's `PreInvocation`
ephemeral message injection and optional `Stop` verification guard.

Key Architectural Features:
1. Recency-Biased Ephemeral Injection (`ephemeralMessage`):
   Injects instructions at the very bottom of the prompt (0 tokens away from
   Flash's `<thinking>` generation) and automatically drops them after the turn
   so conversation history never bloats.
2. 3-State Adaptive Context Detection (via tailing `transcriptPath`):
   - STATE 1 (TURN_START): Full 4-Step Argon Architectural & Red-Team Rubric
     when the user submits a new prompt.
   - STATE 2 (ERROR_RECOVERY): Root-Cause Analysis gate when the previous tool
     call returned a non-zero exit code, traceback, or error.
   - STATE 3 (MID_TURN_LOOP): Ultra-compact (<35 tokens) verification &
     unverified-edit tracker during multi-step tool loops (prevents over-planning
     on simple `read_file` steps).
3. Model-Aware Bypass:
   Automatically detects if Gemini 4 Argon is the active model and stays silent
   (0 token overhead) unless `AGY_FORCE_ARGON_HOOK=1` is set.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

CODE_EXTENSIONS = (
    ".py", ".js", ".ts", ".tsx", ".jsx", ".swift", ".go", ".rs",
    ".java", ".kt", ".c", ".cpp", ".h", ".cs", ".rb", ".php",
    ".sh", ".zsh", ".bash", ".sql", ".html", ".css",
)

EDIT_TOOLS = {"edit_file", "write_file", "replace_file_content", "multi_replace_file_content"}
VERIFY_TOOLS = {"run_command", "read_file", "view_file", "grep_search"}

# ---------------------------------------------------------------------------
# Injected Ephemeral Prompts (XML-Framed for Gemini Flash Attention Locking)
# ---------------------------------------------------------------------------

PROMPT_TURN_START = """<argon_reasoning_protocol mode="turn_start">
MANDATORY PRE-ACTION THINKING GATE (Argon-4 Rigor Mode):
Before emitting ANY tool call or response, work through these 4 steps inside your `<thinking>` block:
1. [DECOMPOSE & CONSTRAINTS]: List every explicit requirement, implicit edge case, and negative constraint from the user request and active rules.
2. [FACT VS. ASSUMPTION]: Separate what you HAVE verified in files/schemas from what you are ASSUMING. NEVER guess file paths, APIs, CLI flags, or column names—inspect first.
3. [RED-TEAM / DEVIL'S ADVOCATE]: Identify the #1 way your initial hypothesis or implementation could fail or miss an edge case, and design against it. If the user's premise has a flaw, state it clearly.
4. [ZERO-LAZINESS & VERIFICATION]: Write complete, production-grade logic (no `// TODO` placeholders, no blind full-file overwrites when surgical `edit_file` applies). Plan how you will verify the result before ending your turn.
</argon_reasoning_protocol>"""

PROMPT_ERROR_RECOVERY = """<argon_reasoning_protocol mode="error_recovery">
MANDATORY ERROR RECOVERY GATE:
The previous tool step produced an error or non-zero exit code.
- NEVER blindly retry with guessed flags or slap on a superficial symptom patch.
- In `<thinking>`, state: (1) the exact root cause from the error output, and (2) what file/doc/state you must inspect to verify the fix before mutating code.
</argon_reasoning_protocol>"""

PROMPT_MID_TURN_UNVERIFIED_EDITS = """<argon_reasoning_protocol mode="unverified_edits">
VERIFICATION GATE ACTIVE — Unverified file modification(s) in this turn: {files}
- In `<thinking>`, state in 1 sentence what the last tool output proved vs. what remains unverified.
- DO NOT end your turn (`NO_TOOL_CALL`) until you have verified your changes (via execution, syntax/lint check, or inspecting the resulting state).
</argon_reasoning_protocol>"""

PROMPT_MID_TURN_CLEAN = """<argon_reasoning_protocol mode="mid_turn">
STEP ANCHOR: In `<thinking>`, state in 1 concise sentence what the previous tool output proved and what specific question the next action answers. Never guess uninspected code/data.
</argon_reasoning_protocol>"""


def tail_jsonl_lines(path: str, max_bytes: int = 65536) -> list[dict[str, Any]]:
    """Read the last `max_bytes` of a JSONL transcript file and parse valid JSON lines."""
    if not path or not os.path.isfile(path):
        return []
    try:
        file_size = os.path.getsize(path)
        with open(path, "rb") as f:
            if file_size > max_bytes:
                f.seek(file_size - max_bytes)
                raw = f.read().decode("utf-8", errors="ignore")
                # Drop potentially partial first line
                lines = raw.splitlines()[1:]
            else:
                raw = f.read().decode("utf-8", errors="ignore")
                lines = raw.splitlines()
        parsed: list[dict[str, Any]] = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    parsed.append(obj)
            except Exception:
                continue
        return parsed
    except Exception:
        return []


def detect_active_model(payload: dict[str, Any], steps: list[dict[str, Any]]) -> str:
    """
    Determine the active model name from the hook payload or recent `<USER_SETTINGS_CHANGE>`
    tags in the transcript.
    """
    model_name = str(payload.get("modelName") or "").strip()
    # Scan recent USER_INPUT steps in reverse for explicit model selection changes
    for step in reversed(steps):
        if step.get("type") == "USER_INPUT":
            content = str(step.get("content") or "")
            matches = re.findall(
                r"changed setting `Model Selection` from .+ to ([^\.\n]+)",
                content,
            )
            if matches:
                return matches[-1].strip()
    return model_name


def is_argon_model(model_str: str) -> bool:
    """Return True if the active model is explicitly Gemini 4 Argon."""
    if os.environ.get("AGY_FORCE_ARGON_HOOK", "").strip() in ("1", "true", "yes"):
        return False
    lowered = model_str.lower()
    return "argon" in lowered


def extract_tool_arg_path(args: dict[str, Any]) -> str:
    """Extract target file path from a tool call's args dict."""
    for key in ("Path", "TargetFile", "AbsolutePath", "file_path", "path"):
        val = args.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip().strip('"').strip("'")
    return ""


def analyze_current_turn(steps: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Analyze steps since the most recent `USER_INPUT` in the transcript.
    Returns:
      - is_turn_start: True if the very last step is USER_INPUT (or transcript is empty)
      - last_tool_errored: True if the latest tool result shows a failure/error
      - unverified_files: List of basenames modified since the last verification tool call
      - unverified_code_files: List of code file basenames modified since the last verification tool call
      - forced_continues_in_turn: Count of Stop-hook continuations already injected this turn
    """
    result = {
        "is_turn_start": True,
        "last_tool_errored": False,
        "unverified_files": [],
        "unverified_code_files": [],
        "forced_continues_in_turn": 0,
    }
    if not steps:
        return result

    # Find index of the last real USER_INPUT step
    last_user_idx = -1
    for i in range(len(steps) - 1, -1, -1):
        if steps[i].get("type") == "USER_INPUT" and steps[i].get("source") == "USER_EXPLICIT":
            last_user_idx = i
            break

    turn_steps = steps[last_user_idx + 1 :] if last_user_idx >= 0 else steps
    if not turn_steps:
        result["is_turn_start"] = True
        return result

    result["is_turn_start"] = False

    unverified_all: list[str] = []
    unverified_code: list[str] = []

    for step in turn_steps:
        stype = step.get("type", "")
        content = str(step.get("content") or "")
        if "AGY-STOP-GUARD:" in content:
            result["forced_continues_in_turn"] += 1

        if stype == "PLANNER_RESPONSE":
            tool_calls = step.get("tool_calls") or []
            if isinstance(tool_calls, list):
                for tc in tool_calls:
                    if not isinstance(tc, dict):
                        continue
                    tname = str(tc.get("name") or "")
                    targs = tc.get("args") or {}
                    if not isinstance(targs, dict):
                        targs = {}

                    if tname in EDIT_TOOLS:
                        fpath = extract_tool_arg_path(targs)
                        bname = os.path.basename(fpath) if fpath else tname
                        # Ignore scratch/artifact markdown files for code verification tracking
                        is_artifact = "/brain/" in fpath.replace("\\", "/") and fpath.endswith(".md")
                        if not is_artifact:
                            if bname not in unverified_all:
                                unverified_all.append(bname)
                            if fpath.lower().endswith(CODE_EXTENSIONS) and bname not in unverified_code:
                                unverified_code.append(bname)
                    elif tname in VERIFY_TOOLS:
                        # A verification/inspection tool ran after prior edits
                        if tname == "run_command":
                            unverified_all.clear()
                            unverified_code.clear()
                        elif tname in ("read_file", "view_file"):
                            fpath = extract_tool_arg_path(targs)
                            bname = os.path.basename(fpath) if fpath else ""
                            if bname in unverified_all:
                                unverified_all.remove(bname)
                            if bname in unverified_code:
                                unverified_code.remove(bname)

    # Check if the latest step(s) since the last PLANNER_RESPONSE had a tool error
    last_planner_idx = -1
    for i in range(len(turn_steps) - 1, -1, -1):
        if turn_steps[i].get("type") == "PLANNER_RESPONSE":
            last_planner_idx = i
            break

    if last_planner_idx >= 0:
        recent_outputs = turn_steps[last_planner_idx + 1 :]
        for out_step in recent_outputs:
            if out_step.get("status") == "ERROR":
                result["last_tool_errored"] = True
                break
            out_text = str(out_step.get("content") or "")
            # Detect non-zero command exit or Python/JS traceback
            exit_match = re.search(r"Command exited with code (\d+)", out_text)
            if exit_match and exit_match.group(1) != "0":
                result["last_tool_errored"] = True
                break
            if "Traceback (most recent call last):" in out_text or "SyntaxError:" in out_text:
                result["last_tool_errored"] = True
                break

    result["unverified_files"] = unverified_all
    result["unverified_code_files"] = unverified_code
    return result


def handle_pre_invocation(payload: dict[str, Any]) -> dict[str, Any]:
    """Handle Antigravity `PreInvocation` hook event."""
    transcript_path = str(payload.get("transcriptPath") or "")
    steps = tail_jsonl_lines(transcript_path)
    active_model = detect_active_model(payload, steps)

    # Stay completely silent on Gemini 4 Argon (0 token overhead)
    if is_argon_model(active_model):
        return {}

    turn_state = analyze_current_turn(steps)

    if turn_state["is_turn_start"]:
        msg = PROMPT_TURN_START
    elif turn_state["last_tool_errored"]:
        msg = PROMPT_ERROR_RECOVERY
    elif turn_state["unverified_files"]:
        files_str = ", ".join(turn_state["unverified_files"][:5])
        msg = PROMPT_MID_TURN_UNVERIFIED_EDITS.format(files=files_str)
    else:
        msg = PROMPT_MID_TURN_CLEAN

    return {
        "injectSteps": [
            {
                "ephemeralMessage": msg
            }
        ]
    }


def handle_stop(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Handle Antigravity `Stop` hook event (optional Split-Plane mode).
    Only forces a single continuation if:
      1. Active model is NOT Argon 4
      2. terminationReason == "NO_TOOL_CALL"
      3. Code files were edited in this turn without a subsequent `run_command` or `read_file`
      4. We haven't already forced a continuation in this turn (`executionNum <= 1`)
    """
    term_reason = str(payload.get("terminationReason") or "")
    exec_num = int(payload.get("executionNum") or 1)
    if term_reason != "NO_TOOL_CALL" or exec_num > 1:
        return {"decision": "allow"}

    transcript_path = str(payload.get("transcriptPath") or "")
    steps = tail_jsonl_lines(transcript_path)
    active_model = detect_active_model(payload, steps)

    if is_argon_model(active_model):
        return {"decision": "allow"}

    turn_state = analyze_current_turn(steps)
    if turn_state["forced_continues_in_turn"] > 0:
        return {"decision": "allow"}

    unverified_code = turn_state["unverified_code_files"]
    if unverified_code:
        files_list = ", ".join(unverified_code[:5])
        return {
            "decision": "continue",
            "reason": (
                f"AGY-STOP-GUARD: You modified code file(s) ({files_list}) without running "
                "a verification step afterward. Please verify syntax/execution or test your "
                "changes before concluding the turn."
            ),
        }

    return {"decision": "allow"}


def run_self_test() -> int:
    """Run offline diagnostic tests verifying all hook states."""
    print("Running Argon-4 Reasoning Booster Hook self-test...\n")

    # 1. Argon bypass check
    res_argon = handle_pre_invocation({"modelName": "Gemini 4 Argon (High)"})
    assert res_argon == {}, f"Expected empty dict for Argon, got {res_argon}"
    print("  [PASS] Argon 4 Model Bypass -> 0 tokens injected ({})")

    # 2. Flash Turn-Start check
    res_start = handle_pre_invocation({"modelName": "Gemini 3.8 Flash (Medium)"})
    injected = res_start.get("injectSteps", [{}])[0].get("ephemeralMessage", "")
    assert 'mode="turn_start"' in injected, "Expected turn_start prompt"
    print("  [PASS] Flash Turn-Start -> Full 4-Step Argon Reasoning Protocol injected")

    # 3. Simulated transcript checks (Error Recovery & Unverified Code Edits)
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as tf:
        tf_path = tf.name
        tf.write(json.dumps({"step_index": 0, "source": "USER_EXPLICIT", "type": "USER_INPUT", "content": "Fix app.py"}) + "\n")
        tf.write(json.dumps({
            "step_index": 1,
            "source": "MODEL",
            "type": "PLANNER_RESPONSE",
            "tool_calls": [{"name": "edit_file", "args": {"Path": "/tmp/app.py"}}],
        }) + "\n")
        tf.write(json.dumps({"step_index": 2, "source": "MODEL", "type": "GENERIC", "content": "Edited /tmp/app.py"}) + "\n")

    try:
        res_mid = handle_pre_invocation({"modelName": "Gemini 3.7 Flash", "transcriptPath": tf_path})
        mid_msg = res_mid.get("injectSteps", [{}])[0].get("ephemeralMessage", "")
        assert 'mode="unverified_edits"' in mid_msg and "app.py" in mid_msg
        print("  [PASS] Flash Mid-Turn Unverified Edit -> Tracks `app.py` for verification")

        res_stop = handle_stop({
            "modelName": "Gemini 3.7 Flash",
            "terminationReason": "NO_TOOL_CALL",
            "executionNum": 1,
            "transcriptPath": tf_path,
        })
        assert res_stop.get("decision") == "continue"
        print("  [PASS] Stop Guard -> Catches unverified `app.py` edit on NO_TOOL_CALL")

        # Append a failing command output
        with open(tf_path, "a", encoding="utf-8") as tf:
            tf.write(json.dumps({
                "step_index": 3,
                "source": "MODEL",
                "type": "PLANNER_RESPONSE",
                "tool_calls": [{"name": "run_command", "args": {"CommandLine": "python3 /tmp/app.py"}}],
            }) + "\n")
            tf.write(json.dumps({
                "step_index": 4,
                "source": "MODEL",
                "type": "GENERIC",
                "content": "Command exited with code 1\nTraceback (most recent call last):\nSyntaxError: invalid syntax",
            }) + "\n")

        res_err = handle_pre_invocation({"modelName": "Gemini 3.7 Flash", "transcriptPath": tf_path})
        err_msg = res_err.get("injectSteps", [{}])[0].get("ephemeralMessage", "")
        assert 'mode="error_recovery"' in err_msg
        print("  [PASS] Flash Error Recovery -> Injects Root-Cause Analysis gate on non-zero exit")
    finally:
        os.remove(tf_path)

    print("\nAll self-tests passed!")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Argon-4 Reasoning Hook for Gemini Flash")
    parser.add_argument(
        "--event",
        choices=["pre", "stop", "auto"],
        default="auto",
        help="Hook lifecycle event type (default: auto-detect from stdin JSON)",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run built-in unit/diagnostic tests",
    )
    args = parser.parse_args()

    if args.self_test:
        sys.exit(run_self_test())

    try:
        raw = sys.stdin.read()
        if not raw.strip():
            print("{}")
            return
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            print("{}")
            return

        event = args.event
        if event == "auto":
            if "terminationReason" in payload or "fullyIdle" in payload:
                event = "stop"
            else:
                event = "pre"

        if event == "stop":
            out = handle_stop(payload)
        else:
            out = handle_pre_invocation(payload)

        print(json.dumps(out))
    except Exception:
        # Fail-open so a hook error never bricks the agent loop
        print("{}")


if __name__ == "__main__":
    main()
