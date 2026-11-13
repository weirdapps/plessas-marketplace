"""bin/docs-py: the docs plugin's python-docx launcher.

A sandboxed session or a locked-down machine can leave the cache folder or
~/Downloads unwritable. The launcher must fall back to the per-user temp folder
and say so, or exit 2 with a message naming the folder, never produce nothing
silently.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

LAUNCHER = Path(__file__).resolve().parent.parent / "bin" / "docs-py"

pytestmark = pytest.mark.skipif(
    os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0),
    reason="needs a POSIX shell and a user that read-only permissions apply to",
)


def run(args, env_extra, cwd=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith("DOCS_")}
    env.update(env_extra)
    return subprocess.run(
        ["bash", str(LAUNCHER), *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd,
        timeout=600,
    )


@pytest.fixture
def read_only(tmp_path):
    ro = tmp_path / "read-only"
    ro.mkdir()
    ro.chmod(0o500)
    yield ro
    ro.chmod(0o700)


def test_outdir_is_downloads_when_it_can_be_written(tmp_path):
    home = tmp_path / "home"
    r = run(["outdir"], {"HOME": str(home), "TMPDIR": str(tmp_path / "t")})
    assert r.returncode == 0, r.stderr
    assert Path(r.stdout.strip()) == home / "Downloads"
    assert (home / "Downloads").is_dir()
    assert r.stderr == ""


def test_outdir_falls_back_to_the_current_folder(tmp_path, read_only):
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    r = run(["outdir"], {"HOME": str(read_only), "TMPDIR": str(tmp_path / "t")}, cwd=cwd)
    assert r.returncode == 0, r.stderr
    assert Path(r.stdout.strip()).resolve() == cwd.resolve()
    assert str(read_only / "Downloads") in r.stderr


def test_outdir_exits_2_when_nothing_can_be_written(read_only):
    r = run(["outdir"], {"HOME": str(read_only), "TMPDIR": str(read_only / "t")}, cwd=read_only)
    assert r.returncode == 2
    assert r.stdout == ""
    assert str(read_only / "Downloads") in r.stderr


def test_doctor_falls_back_to_tmpdir_when_the_cache_is_read_only(tmp_path, read_only):
    tmp = tmp_path / "t"
    r = run(["doctor"], {"DOCS_VENV_HOME": str(read_only / "venvs"), "TMPDIR": str(tmp)})
    assert f"venv home:   {tmp / 'nbg-docs'}" in r.stdout, r.stdout + r.stderr
    assert str(read_only / "venvs") in r.stderr


def test_a_missing_script_exits_2_naming_it(tmp_path):
    r = run([str(tmp_path / "nope.py")], {"DOCS_VENV_HOME": str(tmp_path / "v")})
    assert r.returncode == 2
    assert "nope.py" in r.stderr


def test_no_arguments_prints_usage_and_exits_2():
    r = run([], {})
    assert r.returncode == 2
    assert "usage: docs-py" in r.stderr


def test_a_script_runs_with_python_docx(tmp_path):
    # Builds a real environment (network on first run); tests.yml fails on any skip.
    script = tmp_path / "make.py"
    script.write_text(
        "import sys\nfrom docx import Document\nd = Document()\nd.add_paragraph('x')\n"
        "d.save(sys.argv[1])\n"
    )
    out = tmp_path / "x.docx"
    r = run([str(script), str(out)], {"DOCS_VENV_HOME": str(tmp_path / "v")})
    assert r.returncode == 0, r.stderr
    assert out.is_file()


def test_a_script_on_stdin_runs_with_python_docx(tmp_path):
    out = tmp_path / "y.docx"
    env = {k: v for k, v in os.environ.items() if not k.startswith("DOCS_")}
    env["DOCS_VENV_HOME"] = str(tmp_path / "v")
    r = subprocess.run(
        ["bash", str(LAUNCHER), "-", str(out)],
        input="import sys\nfrom docx import Document\nDocument().save(sys.argv[1])\n",
        capture_output=True,
        text=True,
        env=env,
        timeout=600,
    )
    assert r.returncode == 0, r.stderr
    assert out.is_file()
