"""Tests für .github/scripts/publish-data.sh gegen ein lokales Bare-Repository."""

from __future__ import annotations

import gzip
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / ".github/scripts/publish-data.sh"

pytestmark = pytest.mark.skipif(
    shutil.which("bash") is None or shutil.which("git") is None, reason="bash/git fehlt"
)


def git(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout


@pytest.fixture
def remote(tmp_path: Path) -> Path:
    path = tmp_path / "remote.git"
    git("init", "-q", "--bare", str(path))
    return path


def publish(mode: str, incoming: Path, remote: Path) -> subprocess.CompletedProcess[str]:
    env = {
        "PATH": os.environ["PATH"],
        "HOME": str(incoming.parent),
        "DATA_REMOTE": str(remote),
        "PUBLISH_RETRY_SLEEP": "0",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
    }
    return subprocess.run(
        ["bash", str(SCRIPT), mode, str(incoming)], env=env, capture_output=True, text=True
    )


def files_on_data(remote: Path) -> list[str]:
    return sorted(git("--git-dir", str(remote), "ls-tree", "-r", "--name-only", "data").split())


def log_on_data(remote: Path) -> list[str]:
    return git("--git-dir", str(remote), "log", "--format=%s", "data").splitlines()


def gz(payload: bytes = b"{}") -> bytes:
    return gzip.compress(payload, mtime=0)


def make_incoming(tmp_path: Path, name: str, files: dict[str, bytes | str]) -> Path:
    root = tmp_path / name
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content if isinstance(content, bytes) else content.encode())
    return root


def analyze_files(day: str = "2026-11-20", **extra: bytes | str) -> dict[str, bytes | str]:
    return {
        "shopping-list.md": f"# Liste {day}\n",
        "shopping-list.json": json.dumps({"schema_version": 1, "generated_at": f"{day}T04:23:00Z"}),
        "universe.json": json.dumps({"schema_version": 1, "ids": [1]}),
        **extra,
    }


# --- Snapshot-Modus -----------------------------------------------------------------------


def test_snapshot_creates_branch_then_appends(tmp_path, remote):
    a = make_incoming(tmp_path, "a", {"snapshots/2026-11-20/0417.json.gz": gz()})
    r = publish("snapshot", a, remote)
    assert r.returncode == 0, r.stderr
    b = make_incoming(tmp_path, "b", {"snapshots/2026-11-20/0517.json.gz": gz()})
    assert publish("snapshot", b, remote).returncode == 0
    assert files_on_data(remote) == [
        "snapshots/2026-11-20/0417.json.gz",
        "snapshots/2026-11-20/0517.json.gz",
    ]
    assert log_on_data(remote) == [
        "Snapshot 2026-11-20/0517.json.gz",
        "Snapshot 2026-11-20/0417.json.gz",
    ]


def test_snapshot_unchanged_makes_no_commit(tmp_path, remote):
    a = make_incoming(tmp_path, "a", {"snapshots/2026-11-20/0417.json.gz": gz()})
    publish("snapshot", a, remote)
    r = publish("snapshot", a, remote)
    assert r.returncode == 0
    assert "Keine Änderungen" in r.stdout
    assert len(log_on_data(remote)) == 1


@pytest.mark.parametrize(
    "files",
    [
        {"snapshots/2026-11-20/0417.json.gz": gz(), "evil.sh": "x"},  # Zusatzdatei
        {"../escape.json.gz": gz()},
        {"snapshots/2026-11-20/0417.json": "{}"},  # falsche Endung
        {"snapshots/2026-11-20/0417.json.gz": b"kein gzip"},
        {"shopping-list.md": "x"},  # gehört nicht in den Snapshot-Modus
        {
            "snapshots/2026-11-20/0417.json.gz": gz(),
            "snapshots/2026-11-20/0517.json.gz": gz(),
        },  # nur genau eine Datei
        {},
    ],
)
def test_snapshot_rejects_unexpected_artifacts(tmp_path, remote, files):
    incoming = make_incoming(tmp_path, "in", files)
    incoming.mkdir(exist_ok=True)
    r = publish("snapshot", incoming, remote)
    assert r.returncode != 0
    assert "::error::" in r.stderr
    assert git("--git-dir", str(remote), "branch", "--list", "data") == ""


def test_symlink_in_artifact_rejected(tmp_path, remote):
    incoming = make_incoming(tmp_path, "in", {})
    (incoming / "snapshots/2026-11-20").mkdir(parents=True)
    (tmp_path / "secret").write_text("geheim")
    os.symlink(tmp_path / "secret", incoming / "snapshots/2026-11-20/0417.json.gz")
    r = publish("snapshot", incoming, remote)
    assert r.returncode != 0
    assert "Symlinks" in r.stderr


def test_oversized_file_rejected(tmp_path, remote):
    big = gz(os.urandom(3 * 1024 * 1024))
    incoming = make_incoming(tmp_path, "in", {"snapshots/2026-11-20/0417.json.gz": big})
    assert publish("snapshot", incoming, remote).returncode != 0


def test_malicious_filename_not_echoed_as_workflow_command(tmp_path, remote):
    incoming = make_incoming(tmp_path, "in", {"::add-mask::x": "x"})
    r = publish("snapshot", incoming, remote)
    assert r.returncode != 0
    assert "::add-mask::x" not in r.stderr


def test_unknown_mode_rejected(tmp_path, remote):
    incoming = make_incoming(tmp_path, "in", {"x": "y"})
    assert publish("deploy", incoming, remote).returncode != 0


# --- Analyse-Modus ------------------------------------------------------------------------


def test_analyze_writes_list_archive_and_universe(tmp_path, remote):
    incoming = make_incoming(tmp_path, "in", analyze_files())
    r = publish("analyze", incoming, remote)
    assert r.returncode == 0, r.stderr
    assert files_on_data(remote) == [
        "lists/2026-11-20.md",
        "shopping-list.json",
        "shopping-list.md",
        "universe.json",
    ]
    assert log_on_data(remote) == ["Einkaufsliste 2026-11-20"]


def test_analyze_compaction_removes_only_covered_days(tmp_path, remote):
    for i, name in enumerate(
        [
            "snapshots/2026-10-01/0017.json.gz",
            "snapshots/2026-10-01/0117.json.gz",
            "snapshots/2026-10-02/0017.json.gz",
            "snapshots/2026-11-19/0017.json.gz",
        ]
    ):
        publish("snapshot", make_incoming(tmp_path, f"s{i}", {name: gz()}), remote)

    removal = "\n".join(
        [
            "snapshots/2026-10-01/0017.json.gz",
            "snapshots/2026-10-01/0117.json.gz",
            "snapshots/2026-10-02/0017.json.gz",  # Tageswerte fehlen → bleibt
        ]
    )
    incoming = make_incoming(
        tmp_path,
        "in",
        analyze_files(**{"daily/2026-10-01.json.gz": gz(), "remove.txt": removal + "\n"}),
    )
    r = publish("analyze", incoming, remote)
    assert r.returncode == 0, r.stderr
    files = files_on_data(remote)
    assert "daily/2026-10-01.json.gz" in files
    assert "snapshots/2026-10-01/0017.json.gz" not in files
    assert "snapshots/2026-10-02/0017.json.gz" in files
    assert "snapshots/2026-11-19/0017.json.gz" in files
    assert "remove.txt" not in files
    assert log_on_data(remote)[0] == (
        "Einkaufsliste 2026-11-20, 3 Snapshots zu Tageswerten verdichtet"
    )
    # Historie ist linear (keine Force-Pushes): jeder Commit hat genau einen Vorgänger.
    parents = git("--git-dir", str(remote), "log", "--format=%p", "data").splitlines()
    assert all(len(p.split()) == 1 for p in parents[:-1]) and parents[-1] == ""


@pytest.mark.parametrize(
    "removal",
    ["shopping-list.md", "../../etc/passwd", "snapshots/2026-10-01/../../x.json.gz", "-rf"],
)
def test_analyze_rejects_bad_removals(tmp_path, remote, removal):
    incoming = make_incoming(tmp_path, "in", analyze_files(**{"remove.txt": removal + "\n"}))
    assert publish("analyze", incoming, remote).returncode != 0


def test_analyze_requires_shopping_list(tmp_path, remote):
    files = analyze_files()
    del files["shopping-list.md"]
    assert publish("analyze", make_incoming(tmp_path, "in", files), remote).returncode != 0


def test_analyze_rejects_invalid_json(tmp_path, remote):
    files = analyze_files()
    files["universe.json"] = "{kaputt"
    assert publish("analyze", make_incoming(tmp_path, "in", files), remote).returncode != 0


def test_analyze_rejects_bad_date(tmp_path, remote):
    files = analyze_files()
    files["shopping-list.json"] = json.dumps({"generated_at": "../../x"})
    assert publish("analyze", make_incoming(tmp_path, "in", files), remote).returncode != 0
