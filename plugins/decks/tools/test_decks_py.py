"""bin/decks-py when its folders cannot be written.

A sandboxed Claude Code session (and a plugin eval run) protects the plugin data
folder under ~/.claude, and a locked-down machine can make the cache folder
read-only. The launcher must then fall back to the per-user temp folder and say
so, or exit 2 with a message naming the folder, never produce nothing silently.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

LAUNCHER = Path(__file__).resolve().parent.parent / "bin" / "decks-py"

pytestmark = pytest.mark.skipif(
    os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0),
    reason="needs a POSIX shell and a user that read-only permissions apply to",
)


def run(args: list[str], env_extra: dict[str, str]) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("DECKS_")}
    env.update(env_extra)
    return subprocess.run(
        ["bash", str(LAUNCHER), *args], capture_output=True, text=True, env=env, timeout=60
    )


@pytest.fixture
def read_only(tmp_path):
    ro = tmp_path / "read-only"
    ro.mkdir()
    ro.chmod(0o500)
    yield ro
    ro.chmod(0o700)


def test_workdir_uses_the_data_folder_when_it_is_writable(tmp_path):
    data = tmp_path / "data"
    r = run(["workdir", str(data), "202611131200_card_revenue"], {"TMPDIR": str(tmp_path / "t")})
    assert r.returncode == 0, r.stderr
    work = Path(r.stdout.strip())
    assert work == data / "work" / "202611131200_card_revenue"
    assert (work / "images").is_dir()
    assert r.stderr == ""


def test_workdir_falls_back_to_tmpdir_when_the_data_folder_is_read_only(tmp_path, read_only):
    tmp = tmp_path / "t"
    r = run(["workdir", str(read_only / "data"), "202611131200_card_revenue"], {"TMPDIR": str(tmp)})
    assert r.returncode == 0, r.stderr
    work = Path(r.stdout.strip())
    assert work == tmp / "nbg-decks" / "work" / "202611131200_card_revenue"
    assert (work / "images").is_dir()
    assert str(read_only / "data") in r.stderr and str(work) in r.stderr


def test_workdir_falls_back_when_the_data_folder_is_empty(tmp_path):
    # An unset ${CLAUDE_PLUGIN_DATA} arrives as "".
    tmp = tmp_path / "t"
    r = run(["workdir", "", "deck"], {"TMPDIR": str(tmp)})
    assert r.returncode == 0, r.stderr
    assert Path(r.stdout.strip()) == tmp / "nbg-decks" / "work" / "deck"


def test_workdir_exits_2_naming_both_folders_when_nothing_is_writable(tmp_path, read_only):
    r = run(["workdir", str(read_only / "data"), "deck"], {"TMPDIR": str(read_only / "tmp")})
    assert r.returncode == 2
    assert r.stdout == ""
    assert str(read_only / "data") in r.stderr and str(read_only / "tmp") in r.stderr


@pytest.mark.parametrize("bad", ["", "../escape", "a/b", "."])
def test_workdir_refuses_a_deck_id_that_is_not_one_folder_name(tmp_path, bad):
    r = run(["workdir", str(tmp_path / "data"), bad], {"TMPDIR": str(tmp_path / "t")})
    assert r.returncode == 2
    assert "deck id" in r.stderr


def test_environments_fall_back_to_tmpdir_when_the_cache_folder_is_read_only(tmp_path, read_only):
    tmp = tmp_path / "t"
    r = run(["doctor"], {"DECKS_VENV_HOME": str(read_only / "venvs"), "TMPDIR": str(tmp)})
    assert f"venv home:     {tmp / 'nbg-decks'}" in r.stdout, r.stdout + r.stderr
    assert str(read_only / "venvs") in r.stderr


def test_environments_stay_in_a_writable_cache_folder(tmp_path):
    home = tmp_path / "venvs"
    r = run(["doctor"], {"DECKS_VENV_HOME": str(home), "TMPDIR": str(tmp_path / "t")})
    assert f"venv home:     {home}" in r.stdout, r.stdout + r.stderr
    assert "falling back" not in r.stderr
