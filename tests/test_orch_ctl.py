import json
import subprocess
import sys
from pathlib import Path

ORCH_CTL = Path(__file__).resolve().parent.parent / "skills" / "apex-orchestrate" / "scripts" / "orch_ctl.py"


def _run_ctl(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ORCH_CTL), *args],
        cwd=str(cwd),
        text=True,
        capture_output=True,
        shell=False,
    )


def _git(cwd: Path, *args: str) -> str:
    res = subprocess.run(["git", *args], cwd=str(cwd), text=True, capture_output=True, check=True)
    return res.stdout.strip()


def _init_repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")
    (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "other.py").write_text("y = 2\n", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "init")
    return tmp_path


def test_init_and_exclude_idempotent(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    res1 = _run_ctl(repo, "init", "--run-id", "r1", "--spec-text", "hello")
    assert res1.returncode == 0
    data = json.loads(res1.stdout)
    assert data["is_git"] is True
    assert data["dirty_tracked_files"] == []

    res2 = _run_ctl(repo, "init", "--run-id", "r1", "--spec-text", "hello")
    assert res2.returncode == 0
    exclude = (repo / ".git" / "info" / "exclude").read_text(encoding="utf-8")
    assert exclude.count(".apex-orch/") == 1


def test_integrate_scope_firewall_and_merge(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _run_ctl(repo, "init", "--run-id", "r2", "--spec-text", "test")

    _git(repo, "checkout", "-b", "apex/r2/t1")
    (repo / "other.py").write_text("y = 99\n", encoding="utf-8")
    _git(repo, "add", "other.py")
    _git(repo, "commit", "-m", "bad")
    bad_sha = _git(repo, "rev-parse", "HEAD")

    _git(repo, "checkout", "-")
    res_bad = _run_ctl(repo, "integrate", "--run-id", "r2", "--task-id", "t1", "--ref", bad_sha, "--owned", "app.py")
    assert res_bad.returncode != 0
    assert json.loads(res_bad.stdout)["status"] == "scope_violation"

    _git(repo, "checkout", "-b", "apex/r2/t2")
    (repo / "app.py").write_text("x = 42\n", encoding="utf-8")
    _git(repo, "add", "app.py")
    _git(repo, "commit", "-m", "good")
    good_sha = _git(repo, "rev-parse", "HEAD")

    _git(repo, "checkout", "-")
    res_good = _run_ctl(repo, "integrate", "--run-id", "r2", "--task-id", "t2", "--ref", good_sha, "--owned", "app.py")
    assert res_good.returncode == 0
    assert (repo / "app.py").read_text(encoding="utf-8") == "x = 42\n"


def test_gate_caps_stdout(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _run_ctl(repo, "init", "--run-id", "r3", "--spec-text", "gate")
    res = _run_ctl(repo, "gate", "--run-id", "r3", "--", sys.executable, "-c", "print('line\\n' * 200); raise SystemExit(1)")
    assert res.returncode == 1
    assert len(res.stdout) <= 2500
    data = json.loads(res.stdout)
    assert data["exit_code"] == 1
    assert (repo / ".apex-orch" / "r3" / "gate.log").is_file()
