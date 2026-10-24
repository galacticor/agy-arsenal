#!/usr/bin/env python3
"""
Cross-Platform Installer & Manager for `agy-arsenal` (Argon-4 Reasoning Mode for Gemini Flash).

Works on macOS, Linux, and Windows.
Safely merges:
  1. `hooks/argon_reasoning_hook.py` -> `~/.gemini/config/argon_reasoning_hook.py` + `~/.gemini/config/hooks.json`
  2. `rules/GEMINI.argon-flash.md`   -> `~/.gemini/config/GEMINI.md` (via idempotent HTML marker comments)
  3. `skills/argon-architect-mode`   -> `~/.gemini/config/skills/argon-architect-mode/SKILL.md`
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
CONFIG_DIR = Path.home() / ".gemini" / "config"

HOOK_SCRIPT_SRC = REPO_ROOT / "hooks" / "argon_reasoning_hook.py"
HOOK_SCRIPT_DST = CONFIG_DIR / "argon_reasoning_hook.py"
HOOKS_JSON_PATH = CONFIG_DIR / "hooks.json"

RULES_SRC = REPO_ROOT / "rules" / "GEMINI.argon-flash.md"
GEMINI_MD_PATH = CONFIG_DIR / "GEMINI.md"

SKILL_SRC_DIR = REPO_ROOT / "skills" / "argon-architect-mode"
SKILL_DST_DIR = CONFIG_DIR / "skills" / "argon-architect-mode"

HOOK_KEY = "argon-reasoning-booster"
BEGIN_MARKER = "<!-- BEGIN AGY-ARSENAL: ARGON-FLASH -->"
END_MARKER = "<!-- END AGY-ARSENAL: ARGON-FLASH -->"


def resolve_python_cmd() -> str:
    """Return a reliable Python 3 command path for the current OS."""
    if platform.system() == "Darwin" and Path("/opt/homebrew/bin/python3").is_file():
        return "/opt/homebrew/bin/python3"
    if sys.executable:
        return sys.executable
    return "python" if platform.system() == "Windows" else "python3"


def build_hook_entry(mode: str) -> dict:
    """Build the `hooks.json` configuration block for the requested mode."""
    py_cmd = resolve_python_cmd()
    script_path = str(HOOK_SCRIPT_DST)
    # Quote paths if they contain spaces (common on Windows)
    py_str = f'"{py_cmd}"' if " " in py_cmd else py_cmd
    script_str = f'"{script_path}"' if " " in script_path else script_path

    entry: dict = {
        "enabled": True,
        "PreInvocation": [
            {
                "type": "command",
                "command": f"{py_str} {script_str} --event pre",
                "timeout": 10,
            }
        ],
    }
    if mode == "split-plane":
        entry["Stop"] = [
            {
                "type": "command",
                "command": f"{py_str} {script_str} --event stop",
                "timeout": 10,
            }
        ]
    return entry


def install_hook(mode: str) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(HOOK_SCRIPT_SRC, HOOK_SCRIPT_DST)
    if platform.system() != "Windows":
        os.chmod(HOOK_SCRIPT_DST, 0o755)

    hooks_data: dict = {}
    if HOOKS_JSON_PATH.is_file():
        try:
            hooks_data = json.loads(HOOKS_JSON_PATH.read_text(encoding="utf-8"))
            if not isinstance(hooks_data, dict):
                hooks_data = {}
        except Exception as e:
            print(f"  [WARN] Could not parse existing hooks.json ({e}); backing up.")
            shutil.copy2(HOOKS_JSON_PATH, HOOKS_JSON_PATH.with_suffix(".json.bak"))
            hooks_data = {}

    hooks_data[HOOK_KEY] = build_hook_entry(mode)
    HOOKS_JSON_PATH.write_text(json.dumps(hooks_data, indent=2) + "\n", encoding="utf-8")
    print(f"  [OK] Installed hook `{HOOK_KEY}` (mode={mode}) in {HOOKS_JSON_PATH}")


def install_rules() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    rule_block = RULES_SRC.read_text(encoding="utf-8").strip()

    if not GEMINI_MD_PATH.is_file():
        content = "---\ntrigger: always_on\n---\n\n" + rule_block + "\n"
        GEMINI_MD_PATH.write_text(content, encoding="utf-8")
        print(f"  [OK] Created {GEMINI_MD_PATH} with Argon-Flash rules")
        return

    existing = GEMINI_MD_PATH.read_text(encoding="utf-8")
    if BEGIN_MARKER in existing and END_MARKER in existing:
        before = existing.split(BEGIN_MARKER)[0].rstrip()
        after = existing.split(END_MARKER, 1)[1].lstrip()
        updated = f"{before}\n\n{rule_block}\n"
        if after:
            updated += f"\n{after}\n"
    else:
        updated = existing.rstrip() + "\n\n" + rule_block + "\n"

    GEMINI_MD_PATH.write_text(updated, encoding="utf-8")
    print(f"  [OK] Merged Argon-Flash rules into {GEMINI_MD_PATH}")


def install_skill() -> None:
    SKILL_DST_DIR.mkdir(parents=True, exist_ok=True)
    for item in SKILL_SRC_DIR.iterdir():
        if item.is_file():
            shutil.copy2(item, SKILL_DST_DIR / item.name)
    print(f"  [OK] Installed skill `argon-architect-mode` to {SKILL_DST_DIR}")


def uninstall_all() -> None:
    print("Uninstalling `agy-arsenal` from ~/.gemini/config/...")
    if HOOKS_JSON_PATH.is_file():
        try:
            hooks_data = json.loads(HOOKS_JSON_PATH.read_text(encoding="utf-8"))
            if isinstance(hooks_data, dict) and HOOK_KEY in hooks_data:
                del hooks_data[HOOK_KEY]
                HOOKS_JSON_PATH.write_text(json.dumps(hooks_data, indent=2) + "\n", encoding="utf-8")
                print(f"  [OK] Removed `{HOOK_KEY}` from {HOOKS_JSON_PATH}")
        except Exception as e:
            print(f"  [WARN] Failed to update {HOOKS_JSON_PATH}: {e}")

    if HOOK_SCRIPT_DST.is_file():
        HOOK_SCRIPT_DST.unlink()
        print(f"  [OK] Removed {HOOK_SCRIPT_DST}")

    if GEMINI_MD_PATH.is_file():
        existing = GEMINI_MD_PATH.read_text(encoding="utf-8")
        if BEGIN_MARKER in existing and END_MARKER in existing:
            before = existing.split(BEGIN_MARKER)[0].rstrip()
            after = existing.split(END_MARKER, 1)[1].lstrip()
            cleaned = before + ("\n\n" + after if after else "\n")
            GEMINI_MD_PATH.write_text(cleaned, encoding="utf-8")
            print(f"  [OK] Removed Argon-Flash rule block from {GEMINI_MD_PATH}")

    if SKILL_DST_DIR.exists():
        shutil.rmtree(SKILL_DST_DIR)
        print(f"  [OK] Removed skill directory {SKILL_DST_DIR}")

    print("Uninstall complete.")


def print_status() -> None:
    print("=== agy-arsenal Installation Status ===")
    print(f"Target Config Dir : {CONFIG_DIR}")
    print(f"Hook Script       : {'INSTALLED' if HOOK_SCRIPT_DST.is_file() else 'MISSING'} ({HOOK_SCRIPT_DST})")

    hook_mode = "NOT REGISTERED"
    if HOOKS_JSON_PATH.is_file():
        try:
            hooks_data = json.loads(HOOKS_JSON_PATH.read_text(encoding="utf-8"))
            entry = hooks_data.get(HOOK_KEY)
            if isinstance(entry, dict):
                if not entry.get("enabled", True):
                    hook_mode = "DISABLED"
                elif "Stop" in entry and "PreInvocation" in entry:
                    hook_mode = "ACTIVE (split-plane: PreInvocation + Stop Guard)"
                elif "PreInvocation" in entry:
                    hook_mode = "ACTIVE (smart-pre: 3-State Adaptive PreInvocation)"
        except Exception:
            hook_mode = "ERROR READING hooks.json"
    print(f"hooks.json Status : {hook_mode}")

    rules_installed = False
    if GEMINI_MD_PATH.is_file():
        text = GEMINI_MD_PATH.read_text(encoding="utf-8")
        rules_installed = BEGIN_MARKER in text and END_MARKER in text
    print(f"GEMINI.md Rules   : {'INSTALLED' if rules_installed else 'MISSING'} ({GEMINI_MD_PATH})")
    print(f"Architect Skill   : {'INSTALLED' if (SKILL_DST_DIR / 'SKILL.md').is_file() else 'MISSING'} ({SKILL_DST_DIR})")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Install, update, inspect, or remove the Argon-4 Reasoning Booster for Gemini Flash."
    )
    parser.add_argument(
        "--mode",
        choices=["smart-pre", "split-plane"],
        default="smart-pre",
        help=(
            "Hook enforcement mode: 'smart-pre' (Recommended default: 3-state adaptive PreInvocation hook) "
            "or 'split-plane' (adds Stop hook blocking unverified code edits)."
        ),
    )
    parser.add_argument("--status", action="store_true", help="Show current installation status")
    parser.add_argument("--uninstall", action="store_true", help="Cleanly remove agy-arsenal from ~/.gemini/config")
    args = parser.parse_args()

    if args.status:
        print_status()
        return

    if args.uninstall:
        uninstall_all()
        return

    print(f"Installing `agy-arsenal` (mode={args.mode}) into {CONFIG_DIR}...")
    install_hook(args.mode)
    install_rules()
    install_skill()

    print("\nVerifying installed hook with self-test...")
    subprocess.run([resolve_python_cmd(), str(HOOK_SCRIPT_DST), "--self-test"], check=True)
    print("\nDone! Your Antigravity setup is now upgraded.")
    print_status()


if __name__ == "__main__":
    main()
