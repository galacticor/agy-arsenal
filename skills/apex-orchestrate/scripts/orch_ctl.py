#!/usr/bin/env python3
"""Deterministic Git merge-back, scope guard, and log firewall for `/apex-orchestrate`."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def _run_git(cwd: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        text=True,
        capture_output=True,
        shell=False,
    )


def _repo_root(cwd: Path) -> tuple[bool, Path]:
    res = _run_git(cwd, ["rev-parse", "--show-toplevel"])
    if res.returncode == 0 and res.stdout.strip():
        return True, Path(res.stdout.strip())
    return False, cwd.resolve()


def _state_dir(root: Path, run_id: str) -> Path:
    return root / ".apex-orch" / run_id


def _load_state(sdir: Path) -> dict:
    state_file = sdir / "state.json"
    if state_file.is_file():
        return json.loads(state_file.read_text(encoding="utf-8"))
    return {}


def _save_state(sdir: Path, state: dict) -> None:
    sdir.mkdir(parents=True, exist_ok=True)
    (sdir / "state.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def _ensure_git_exclude(root: Path) -> None:
    res = _run_git(root, ["rev-parse", "--git-dir"])
    if res.returncode != 0 or not res.stdout.strip():
        return
    git_dir = Path(res.stdout.strip())
    if not git_dir.is_absolute():
        git_dir = root / git_dir
    exclude_file = git_dir / "info" / "exclude"
    exclude_file.parent.mkdir(parents=True, exist_ok=True)
    existing = exclude_file.read_text(encoding="utf-8") if exclude_file.is_file() else ""
    lines = [ln.strip() for ln in existing.splitlines()]
    if ".apex-orch/" not in lines:
        sep = "\n" if existing and not existing.endswith("\n") else ""
        exclude_file.write_text(existing + sep + ".apex-orch/\n", encoding="utf-8")


def cmd_init(args: argparse.Namespace) -> int:
    cwd = Path.cwd()
    is_git, root = _repo_root(cwd)
    base_sha = ""
    dirty_files: list[str] = []

    if is_git:
        head = _run_git(root, ["rev-parse", "HEAD"])
        if head.returncode == 0:
            base_sha = head.stdout.strip()
        status = _run_git(root, ["status", "--porcelain"])
        if status.returncode == 0:
            dirty_files = [ln for ln in status.stdout.splitlines() if ln.strip()]
        _ensure_git_exclude(root)

    sdir = _state_dir(root, args.run_id)
    sdir.mkdir(parents=True, exist_ok=True)

    spec_content = ""
    if args.spec_file:
        spec_content = Path(args.spec_file).read_text(encoding="utf-8")
    elif args.spec_text:
        spec_content = args.spec_text
    (sdir / "spec.md").write_text(spec_content, encoding="utf-8")

    state = {
        "run_id": args.run_id,
        "is_git": is_git,
        "base_sha": base_sha,
        "dirty_tracked_files": dirty_files,
        "integrated_refs": [],
    }
    _save_state(sdir, state)

    out = {
        "is_git": is_git,
        "base_sha": base_sha,
        "dirty_tracked_files": dirty_files,
        "scratch_dir": f".apex-orch/{args.run_id}",
    }
    print(json.dumps(out))
    return 0


def _matches_owned(path: str, owned_prefixes: list[str]) -> bool:
    norm = path.strip("/")
    for prefix in owned_prefixes:
        p = prefix.strip("/")
        if not p:
            continue
        if norm == p or norm.startswith(p + "/"):
            return True
    return False


def cmd_integrate(args: argparse.Namespace) -> int:
    is_git, root = _repo_root(Path.cwd())
    if not is_git:
        print(json.dumps({"status": "error", "message": "Not inside a Git repository"}))
        return 1

    sdir = _state_dir(root, args.run_id)
    state = _load_state(sdir)
    base_sha = state.get("base_sha", "")

    ref_res = _run_git(root, ["rev-parse", "--verify", args.ref])
    if ref_res.returncode != 0:
        print(json.dumps({"status": "error", "message": f"Invalid ref: {args.ref}"}))
        return 1
    resolved_sha = ref_res.stdout.strip()

    diff_range = f"{base_sha}..{resolved_sha}" if base_sha else f"{resolved_sha}~1..{resolved_sha}"
    touched_res = _run_git(root, ["diff", "--name-only", diff_range])
    if touched_res.returncode != 0:
        print(json.dumps({"status": "error", "message": touched_res.stderr.strip()}))
        return 1
    touched = [ln.strip() for ln in touched_res.stdout.splitlines() if ln.strip()]

    owned_list = [p.strip() for p in args.owned.split(",") if p.strip()]
    unauthorized = [f for f in touched if not _matches_owned(f, owned_list)]
    if unauthorized:
        print(json.dumps({"status": "scope_violation", "unauthorized_files": unauthorized}))
        return 1

    cp = _run_git(root, ["cherry-pick", "--no-commit", diff_range if base_sha else resolved_sha])
    if cp.returncode != 0:
        conf_res = _run_git(root, ["diff", "--name-only", "--diff-filter=U"])
        conflicts = [ln.strip() for ln in conf_res.stdout.splitlines() if ln.strip()]
        _run_git(root, ["cherry-pick", "--abort"])
        _run_git(root, ["reset", "HEAD"])
        print(json.dumps({"status": "conflict", "conflicting_files": conflicts}))
        return 1

    _run_git(root, ["reset", "HEAD"])
    existing_touched = [f for f in touched if (root / f).exists()]
    if existing_touched:
        _run_git(root, ["add", "-N", "--", *existing_touched])
    refs = state.setdefault("integrated_refs", [])
    if args.ref not in refs:
        refs.append(args.ref)
    _save_state(sdir, state)

    print(json.dumps({"status": "integrated", "task_id": args.task_id, "ref": resolved_sha, "touched_files": touched}))
    return 0


def cmd_gate(args: argparse.Namespace) -> int:
    is_git, root = _repo_root(Path.cwd())
    sdir = _state_dir(root, args.run_id)
    sdir.mkdir(parents=True, exist_ok=True)

    cmd = args.cmd
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        print(json.dumps({"status": "error", "message": "No gate command provided"}))
        return 1

    proc = subprocess.run(
        cmd,
        cwd=str(root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=False,
    )
    log_path = sdir / "gate.log"
    log_path.write_text(proc.stdout or "", encoding="utf-8")

    diff_stat = ""
    diff_path = sdir / "combined.diff"
    if is_git:
        stat_res = _run_git(root, ["diff", "--stat", "HEAD"])
        diff_stat = stat_res.stdout.strip()
        diff_res = _run_git(root, ["diff", "HEAD"])
        diff_path.write_text(diff_res.stdout or "", encoding="utf-8")
    else:
        diff_path.write_text("", encoding="utf-8")

    tail = ""
    if proc.returncode != 0 and proc.stdout:
        lines = proc.stdout.splitlines()
        tail = "\n".join(lines[-40:])
        if len(tail) > 1500:
            tail = tail[-1500:]

    out = {
        "exit_code": proc.returncode,
        "diff_stat": diff_stat[:500],
        "log_path": f".apex-orch/{args.run_id}/gate.log",
        "diff_path": f".apex-orch/{args.run_id}/combined.diff",
        "tail": tail,
    }
    payload = json.dumps(out)
    if len(payload) > 2500:
        out["tail"] = out["tail"][-800:]
        payload = json.dumps(out)
    print(payload)
    return proc.returncode


def cmd_cleanup(args: argparse.Namespace) -> int:
    is_git, root = _repo_root(Path.cwd())
    sdir = _state_dir(root, args.run_id)
    state = _load_state(sdir)

    if is_git:
        if args.rollback and not state.get("dirty_tracked_files"):
            _run_git(root, ["checkout", "--", "."])
            _run_git(root, ["clean", "-fd"])
        branches_to_delete = {
            ref for ref in state.get("integrated_refs", []) if ref.startswith(f"apex/{args.run_id}/")
        }
        br_res = _run_git(root, ["branch", "--list", f"apex/{args.run_id}/*"])
        if br_res.returncode == 0:
            for ln in br_res.stdout.splitlines():
                name = ln.strip().lstrip("* ").strip()
                if name.startswith(f"apex/{args.run_id}/"):
                    branches_to_delete.add(name)
        for ref in sorted(branches_to_delete):
            _run_git(root, ["branch", "-D", ref])

    if sdir.exists():
        shutil.rmtree(sdir)
    parent = root / ".apex-orch"
    if parent.exists() and not any(parent.iterdir()):
        parent.rmdir()

    print(json.dumps({"status": "cleaned", "run_id": args.run_id}))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic helper for /apex-orchestrate")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init")
    p_init.add_argument("--run-id", required=True)
    p_init.add_argument("--spec-text", default="")
    p_init.add_argument("--spec-file", default="")

    p_int = sub.add_parser("integrate")
    p_int.add_argument("--run-id", required=True)
    p_int.add_argument("--task-id", required=True)
    p_int.add_argument("--ref", required=True)
    p_int.add_argument("--owned", required=True)

    p_gate = sub.add_parser("gate")
    p_gate.add_argument("--run-id", required=True)
    p_gate.add_argument("cmd", nargs=argparse.REMAINDER)

    p_clean = sub.add_parser("cleanup")
    p_clean.add_argument("--run-id", required=True)
    p_clean.add_argument("--rollback", action="store_true")

    args = parser.parse_args()
    if args.command == "init":
        return cmd_init(args)
    if args.command == "integrate":
        return cmd_integrate(args)
    if args.command == "gate":
        return cmd_gate(args)
    if args.command == "cleanup":
        return cmd_cleanup(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
