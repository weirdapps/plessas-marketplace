"""Tests for the eval-suite checks in validate_consistency.py.

These three checks exist because each one caught a defect that had been
passing review for weeks, and all three failures were silent. A validator
that cannot itself be shown to fail is the same class of thing it is meant
to catch, so each test drives the check in BOTH directions: once over a
tree that must trip it, once over a tree that must not.

The module reads two globals to find its work, ROOT and PLUGINS_DIR, and
accumulates into a module-level `errors` list. Every test builds a throwaway
plugin tree, points both globals at it, and clears the accumulator.
"""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT = Path(__file__).resolve().parent / "validate_consistency.py"


def _load() -> ModuleType:
    """Fresh module instance per test, so the `errors` list never leaks."""
    spec = importlib.util.spec_from_file_location("vc_under_test", SCRIPT)
    # Both can be None for an unloadable path. Assert rather than ignore: if the
    # script ever moves, this should say so instead of failing nine tests with an
    # AttributeError on None.
    assert spec is not None and spec.loader is not None, f"cannot load {SCRIPT}"
    mod = importlib.util.module_from_spec(spec)
    # The module inspects sys.argv at import time for --verbose. Tests must not
    # inherit pytest's own argv, or a `-v` run would flip the module into
    # verbose mode and change what it prints.
    saved, sys.argv = sys.argv, ["validate_consistency.py"]
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.argv = saved
    return mod


@pytest.fixture
def vc(tmp_path):
    """The module, pointed at an empty plugin tree under tmp_path."""
    mod = _load()
    # setattr, not attribute assignment: the module is loaded at runtime so mypy
    # has no stub for it and rejects `mod.ROOT = ...` as attr-defined.
    plugins = tmp_path / "plugins"
    plugins.mkdir()
    setattr(mod, "ROOT", tmp_path)
    setattr(mod, "PLUGINS_DIR", plugins)
    mod.errors.clear()
    mod.warnings.clear()
    return mod


def _plugin(vc, name, *, manifest_extra=""):
    d = vc.PLUGINS_DIR / name
    (d / ".claude-plugin").mkdir(parents=True)
    (d / ".claude-plugin" / "plugin.json").write_text(
        '{"name": "' + name + '", "version": "1.0.0"' + manifest_extra + "}"
    )
    return d


def _grader(plugin_dir, case, filename, body):
    g = plugin_dir / "evals" / case / "graders"
    g.mkdir(parents=True, exist_ok=True)
    (g / filename).write_text("---\n" + body.strip() + "\n---\n")


def _marketplace(vc, entries):
    mp = vc.ROOT / ".claude-plugin"
    mp.mkdir(exist_ok=True)
    (mp / "marketplace.json").write_text(
        '{"name": "t", "owner": {"name": "t"}, "plugins": ' + entries + "}"
    )


# --------------------------------------------------------------------------
# check_eval_grader_tool_names
# --------------------------------------------------------------------------


def test_namespaced_grader_is_rejected_with_the_bare_replacement(vc):
    """The five real ones looked exactly like this and passed for weeks."""
    p = _plugin(vc, "mail")
    _grader(
        p,
        "01-x",
        "never-sends.md",
        "type: tool_used\ntool: mcp__plugin_mail_outlook-bridge__outlook_send_mail\nmin: 0\nmax: 0",
    )
    vc.check_eval_grader_tool_names()
    assert len(vc.errors) == 1
    # The message must carry the fix, not just the complaint.
    assert "mcp__outlook-bridge__outlook_send_mail" in vc.errors[0]


def test_bare_grader_is_accepted(vc):
    p = _plugin(vc, "meetings")
    _grader(
        p,
        "01-x",
        "never-sends.md",
        "type: tool_used\ntool: mcp__outlook-bridge__outlook_send_mail\nmin: 0\nmax: 0",
    )
    vc.check_eval_grader_tool_names()
    assert vc.errors == []


def test_non_mcp_graders_are_ignored(vc):
    """`tool: Skill` and `tool: Write` are not namespaced and never should be."""
    p = _plugin(vc, "decks")
    _grader(p, "01-x", "skill-fired.md", "type: tool_used\ntool: Skill\nmin: 1")
    _grader(p, "01-x", "writes-a-file.md", "type: tool_used\ntool: Write\nmin: 1")
    vc.check_eval_grader_tool_names()
    assert vc.errors == []


def test_a_plugin_with_no_evals_dir_is_not_an_error(vc):
    _plugin(vc, "docs")
    vc.check_eval_grader_tool_names()
    assert vc.errors == []


# --------------------------------------------------------------------------
# check_eval_absence_guards_have_a_control
# --------------------------------------------------------------------------


def test_all_absence_guards_and_no_control_is_rejected(vc):
    """mail and chat were both in exactly this state."""
    p = _plugin(vc, "chat")
    _grader(
        p,
        "01-x",
        "never-posts.md",
        "type: tool_used\ntool: mcp__teams-bridge__teams_send_message\nmin: 0\nmax: 0",
    )
    vc.check_eval_absence_guards_have_a_control()
    assert len(vc.errors) == 1
    assert "positive control" in vc.errors[0]


def test_one_positive_control_satisfies_the_suite(vc):
    p = _plugin(vc, "chat")
    _grader(
        p,
        "01-x",
        "never-posts.md",
        "type: tool_used\ntool: mcp__teams-bridge__teams_send_message\nmin: 0\nmax: 0",
    )
    _grader(
        p,
        "01-x",
        "mcp-matcher-control.md",
        "type: tool_used\ntool: mcp__teams-bridge__teams_list_messages\nmin: 1",
    )
    vc.check_eval_absence_guards_have_a_control()
    assert vc.errors == []


def test_a_suite_with_no_mcp_graders_is_not_required_to_have_a_control(vc):
    """decks, docs and excel have no MCP server and must not be failed for it."""
    p = _plugin(vc, "excel")
    _grader(p, "01-x", "skill-fired.md", "type: tool_used\ntool: Skill\nmin: 1")
    vc.check_eval_absence_guards_have_a_control()
    assert vc.errors == []


# --------------------------------------------------------------------------
# check_plugin_dependencies
# --------------------------------------------------------------------------


def test_dependencies_in_plugin_json_is_rejected(vc):
    """This is what made `meetings` unmeasurable: plugins=[] on every run."""
    _plugin(vc, "meetings", manifest_extra=', "dependencies": ["mail"]')
    _marketplace(vc, '[{"name": "meetings", "source": "./plugins/meetings"}]')
    vc.check_plugin_dependencies()
    assert len(vc.errors) == 1
    assert "marketplace.json" in vc.errors[0]


def test_dependencies_in_the_marketplace_entry_is_accepted(vc):
    _plugin(vc, "meetings")
    _marketplace(
        vc,
        '[{"name": "meetings", "source": "./plugins/meetings", "dependencies": ["mail"]}]',
    )
    vc.check_plugin_dependencies()
    assert vc.errors == []


# --------------------------------------------------------------------------
# check_plugin_relative_paths: prompts anchor plugin paths
# --------------------------------------------------------------------------


def _agent(plugin_dir, body, name="a.md"):
    (plugin_dir / "agents").mkdir(exist_ok=True)
    (plugin_dir / "shared").mkdir(exist_ok=True)
    (plugin_dir / "agents" / name).write_text("---\nname: a\ndescription: d\n---\n" + body)


@pytest.fixture
def no_baseline(vc):
    setattr(vc, "KNOWN_BARE_PATHS", frozenset())
    return vc


def test_bare_plugin_path_in_an_agent_is_rejected(no_baseline):
    vc = no_baseline
    _agent(_plugin(vc, "p"), "Read `shared/brand/README.md` first.\n")
    vc.check_plugin_relative_paths()
    assert len(vc.errors) == 1
    assert "shared/brand/README.md" in vc.errors[0]
    assert "${CLAUDE_PLUGIN_ROOT}/shared/brand/README.md" in vc.errors[0]


def test_bare_path_inside_a_code_block_is_rejected(no_baseline):
    vc = no_baseline
    _agent(_plugin(vc, "p"), "```bash\npython3 shared/tool.py deck.pptx\n```\n")
    vc.check_plugin_relative_paths()
    assert len(vc.errors) == 1


def test_repo_relative_plugins_path_is_rejected(no_baseline):
    vc = no_baseline
    _agent(_plugin(vc, "p"), "See plugins/p/shared/x.md.\n")
    vc.check_plugin_relative_paths()
    assert len(vc.errors) == 1
    assert "plugins/p/shared/x.md" in vc.errors[0]


def test_anchored_home_and_url_paths_are_accepted(no_baseline):
    vc = no_baseline
    _agent(
        _plugin(vc, "p"),
        "Read `${CLAUDE_PLUGIN_ROOT}/shared/x.md`, write ${CLAUDE_PLUGIN_DATA}/shared/y.md,\n"
        "see ~/.claude/plugins/cache/m/p/1.0.0/shared/z.md and\n"
        "https://github.com/o/r/tree/master/plugins/p/shared.\n",
    )
    vc.check_plugin_relative_paths()
    assert vc.errors == []


def test_a_fixed_baseline_entry_must_be_deleted(vc):
    setattr(vc, "KNOWN_BARE_PATHS", frozenset({("plugins/p/agents/a.md", "shared/old.md")}))
    _agent(_plugin(vc, "p"), "Nothing bare here.\n")
    vc.check_plugin_relative_paths()
    assert len(vc.errors) == 1
    assert "no longer bare" in vc.errors[0]


def test_a_baselined_bare_path_is_tolerated(vc):
    setattr(vc, "KNOWN_BARE_PATHS", frozenset({("plugins/p/agents/a.md", "shared/old.md")}))
    _agent(_plugin(vc, "p"), "Still reads `shared/old.md`.\n")
    vc.check_plugin_relative_paths()
    assert vc.errors == []


# --------------------------------------------------------------------------
# check_asset_references: every indexed asset filename exists
# --------------------------------------------------------------------------


def _assets(plugin_dir, files, index_body, index_rel="icons/INDEX.md"):
    for f in files:
        p = plugin_dir / "assets" / f
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"x")
    idx = plugin_dir / "assets" / index_rel
    idx.parent.mkdir(parents=True, exist_ok=True)
    idx.write_text(index_body)


def test_missing_asset_name_is_rejected(vc):
    d = _plugin(vc, "p")
    _assets(d, ["icons/basics/Arrow_left.png"], "| `Arrow left.png` | back |\n")
    vc.check_asset_references()
    assert len(vc.errors) == 1
    assert "Arrow left.png" in vc.errors[0]


def test_asset_names_match_by_basename_or_relative_path(vc):
    d = _plugin(vc, "p")
    _assets(
        d,
        ["icons/basics/Arrow_left.png", "icons/money/Coin.svg"],
        "| `Arrow_left.png` | back |\n| `money/Coin.svg` | coins |\n| `sets/*.svg` | glob |\n",
    )
    vc.check_asset_references()
    assert vc.errors == []


def test_asset_library_names_resolve_against_the_assets_tree(vc):
    d = _plugin(vc, "p")
    _assets(d, ["logos/NBG.png"], "| `NBG.png` | emblem |\n", index_rel="logos/INDEX.md")
    lib = d / "shared" / "brand-system" / "asset-library.md"
    lib.parent.mkdir(parents=True)
    lib.write_text("| `logos/NBG.png` | ok |\n| `logos/Missing.png` | gone |\n")
    vc.check_asset_references()
    assert len(vc.errors) == 1
    assert "Missing.png" in vc.errors[0]
