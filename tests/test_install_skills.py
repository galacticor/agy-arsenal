import os
import platform
from pathlib import Path

import install


def test_install_skill_recursive_and_chmod(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(install, "SKILLS_DST_ROOT", tmp_path / "skills")
    install.install_skill()

    orch_dir = tmp_path / "skills" / "apex-orchestrate"
    assert (orch_dir / "SKILL.md").is_file()
    assert (orch_dir / "references" / "subagent-contracts.md").is_file()
    ctl = orch_dir / "scripts" / "orch_ctl.py"
    assert ctl.is_file()
    if platform.system() != "Windows":
        assert os.access(ctl, os.X_OK)


def test_install_rules_no_frontmatter_on_fresh_gemini_md(tmp_path: Path, monkeypatch) -> None:
    cfg = tmp_path / "config"
    monkeypatch.setattr(install, "CONFIG_DIR", cfg)
    monkeypatch.setattr(install, "GEMINI_MD_PATH", cfg / "GEMINI.md")
    install.install_rules()

    text = (cfg / "GEMINI.md").read_text(encoding="utf-8")
    assert not text.startswith("---\n")
    assert install.BEGIN_MARKER in text
