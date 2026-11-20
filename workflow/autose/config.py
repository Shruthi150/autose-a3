from __future__ import annotations

import copy
import os
from pathlib import Path
from typing import Any

import yaml

WORKFLOW_DIR = Path(__file__).resolve().parent.parent


def load_config(path: str | os.PathLike | None = None) -> dict[str, Any]:
    p = Path(path) if path else WORKFLOW_DIR / "config.yml"
    with open(p, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    cfg = copy.deepcopy(cfg)
    # Quick per-run overrides without editing the file, e.g.
    #   AUTOSE_MODEL_REVIEWER=claude-sonnet-5-5
    for role in list(cfg["models"]):
        env = os.environ.get(f"AUTOSE_MODEL_{role.upper()}")
        if env:
            cfg["models"][role] = env
    return cfg


def prompt(name: str) -> str:
    return (WORKFLOW_DIR / "prompts" / f"{name}.md").read_text(encoding="utf-8")


def spec_skill() -> str:
    p = WORKFLOW_DIR / "skills" / "spec-skill" / "SKILL.md"
    return p.read_text(encoding="utf-8") if p.exists() else ""
