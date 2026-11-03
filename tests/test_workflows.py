"""Sicherheitsregeln für alle GitHub-Workflows (ergänzt zizmor in der CI)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

WORKFLOWS = sorted((Path(__file__).resolve().parents[1] / ".github/workflows").glob("*.yml"))
SHA_PIN = re.compile(r"^[\w.-]+/[\w.-]+(/[\w./-]+)?@[0-9a-f]{40}$")
LOCAL_REUSABLE = re.compile(r"^\./\.github/workflows/[\w-]+\.yml$")

# Einzige Jobs, die mehr als Leserechte bekommen (Workflow → Job → erlaubte Rechte).
WRITE_JOBS = {
    ("analyze.yml", "publish"): {"contents": "write"},
    ("analyze.yml", "pages"): {"contents": "read", "pages": "write", "id-token": "write"},
    ("snapshot.yml", "publish"): {"contents": "write"},
    ("snapshot.yml", "analyze"): {"contents": "write", "pages": "write", "id-token": "write"},
    ("snapshot.yml", "continue"): {"actions": "write"},
    ("pages.yml", "deploy"): {"pages": "write", "id-token": "write"},
}


def _load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    # PyYAML liest den Schlüssel "on" als True.
    data["on"] = data.pop(True, data.get("on"))
    return data


@pytest.fixture(params=WORKFLOWS, ids=lambda p: p.name)
def workflow(request):
    return request.param.name, _load(request.param)


def test_top_level_permissions_empty(workflow):
    _, wf = workflow
    assert wf.get("permissions") == {}


def test_no_dangerous_triggers(workflow):
    _, wf = workflow
    assert "pull_request_target" not in wf["on"]
    assert "workflow_run" not in wf["on"]


def test_every_job_has_permissions_concurrency_and_timeout(workflow):
    name, wf = workflow
    for job_id, job in wf["jobs"].items():
        assert "permissions" in job, f"{name}:{job_id}"
        assert "concurrency" in job, f"{name}:{job_id}"
        if "uses" in job:
            # Aufrufe wiederverwendbarer Workflows erlauben kein timeout-minutes; deren Jobs
            # haben es selbst. Nur lokale Workflows sind erlaubt.
            assert LOCAL_REUSABLE.fullmatch(job["uses"]), f"{name}:{job_id}"
            assert "secrets" not in job
        else:
            assert isinstance(job.get("timeout-minutes"), int), f"{name}:{job_id}"


def test_write_permissions_only_where_needed(workflow):
    name, wf = workflow
    for job_id, job in wf["jobs"].items():
        perms = job["permissions"]
        writes = {k: v for k, v in perms.items() if v == "write"}
        if writes:
            assert (name, job_id) in WRITE_JOBS, f"{name}:{job_id} hat Schreibrechte {writes}"
            assert perms == WRITE_JOBS[(name, job_id)], f"{name}:{job_id}"
        else:
            assert set(perms.values()) <= {"read"}, f"{name}:{job_id}"


def test_actions_pinned_to_full_sha(workflow):
    name, wf = workflow
    for job_id, job in wf["jobs"].items():
        for step in job.get("steps", []):
            if "uses" in step:
                assert SHA_PIN.fullmatch(step["uses"]), f"{name}:{job_id}: {step['uses']}"


def test_no_expressions_in_run_scripts(workflow):
    name, wf = workflow
    for job_id, job in wf["jobs"].items():
        for step in job.get("steps", []):
            assert "${{" not in step.get("run", ""), f"{name}:{job_id}: {step.get('name')}"


def test_checkouts_do_not_persist_credentials(workflow):
    name, wf = workflow
    for job_id, job in wf["jobs"].items():
        for step in job.get("steps", []):
            if step.get("uses", "").startswith("actions/checkout@"):
                assert step.get("with", {}).get("persist-credentials") is False, f"{name}:{job_id}"


def test_chaining_job_is_minimal():
    wf = _load(next(p for p in WORKFLOWS if p.name == "snapshot.yml"))
    job = wf["jobs"]["continue"]
    assert job["needs"] == ["snapshot", "publish"]
    assert job["if"] == (
        "github.ref == 'refs/heads/main' && fromJSON(needs.snapshot.outputs.count) >= 6"
    )
    assert wf["jobs"]["snapshot"]["outputs"]["count"] == "${{ steps.count.outputs.count }}"
    assert job["permissions"] == {"actions": "write"}
    steps = job["steps"]
    assert len(steps) == 1 and "uses" not in steps[0]  # kein Checkout, kein Projektcode
    assert steps[0]["run"] == 'gh workflow run snapshot.yml --repo "$REPO" --ref main'


def test_analyze_is_reusable_and_called_after_snapshots():
    analyze = _load(next(p for p in WORKFLOWS if p.name == "analyze.yml"))
    assert "workflow_call" in analyze["on"] and "schedule" in analyze["on"]
    snap = _load(next(p for p in WORKFLOWS if p.name == "snapshot.yml"))
    assert snap["jobs"]["analyze"]["uses"] == "./.github/workflows/analyze.yml"
    assert snap["jobs"]["analyze"]["needs"] == "publish"
