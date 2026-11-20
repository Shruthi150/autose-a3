"""Run state. One JSON file, uploaded as a workflow artifact after every job,
so that later jobs (rework) and humans can see exactly what happened."""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

STAGES = ["requirements", "design", "implementation", "testing", "release", "review"]


class StageFailed(Exception):
    """A stage could not pass its check. Carries the stage and the reason."""

    def __init__(self, stage: str, reason: str):
        super().__init__(f"{stage}: {reason}")
        self.stage = stage
        self.reason = reason


class BudgetExceeded(StageFailed):
    pass


@dataclass
class RunState:
    repo: str = ""
    run_id: str = ""
    run_url: str = ""
    issue_number: int = 0
    issue_title: str = ""
    base_sha: str = ""
    branch: str = ""
    head_sha: str = ""
    pr_number: int = 0
    pr_url: str = ""
    stages: dict[str, dict[str, Any]] = field(default_factory=dict)
    tokens: dict[str, int] = field(default_factory=lambda: {"input": 0, "output": 0})
    events: list[dict[str, Any]] = field(default_factory=list)
    reviews: list[dict[str, Any]] = field(default_factory=list)
    failed_stage: str = ""
    failure_reason: str = ""
    status: str = "running"  # running | ok | failed

    # -- bookkeeping ---------------------------------------------------
    def stage(self, name: str) -> dict[str, Any]:
        return self.stages.setdefault(name, {"status": "pending", "attempts": 0})

    def event(self, stage: str, kind: str, detail: str = "") -> None:
        self.events.append(
            {"t": round(time.time(), 1), "stage": stage, "kind": kind, "detail": detail[:2000]}
        )
        print(f"[autose] {stage:<15} {kind:<10} {detail[:200]}", flush=True)

    def mark(self, name: str, status: str, **extra: Any) -> None:
        st = self.stage(name)
        st["status"] = status
        st.update(extra)

    def add_tokens(self, inp: int, out: int) -> None:
        self.tokens["input"] += inp
        self.tokens["output"] += out

    @property
    def total_tokens(self) -> int:
        return self.tokens["input"] + self.tokens["output"]

    # -- persistence ---------------------------------------------------
    def save(self, out_dir: str | os.PathLike) -> None:
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        (Path(out_dir) / "state.json").write_text(
            json.dumps(asdict(self), indent=2), encoding="utf-8"
        )

    @classmethod
    def load(cls, out_dir: str | os.PathLike) -> "RunState":
        p = Path(out_dir) / "state.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        known = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**known)
