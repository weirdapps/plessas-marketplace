#!/usr/bin/env python3
"""
plessas-marketplace Consistency Validator

Cross-file consistency checks for the plessas-marketplace plugins.
Run locally or in CI to catch stale references and YAML hazards.

Usage:
    python3 scripts/validate_consistency.py
    python3 scripts/validate_consistency.py --verbose
"""

import json
import re
import sys
from fnmatch import fnmatch
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:
    # CONTRIBUTING.md tells contributors to run this before opening a PR, and
    # pyproject.toml is tooling-only with no install step, so the obvious
    # `python3 scripts/validate_consistency.py` hits a bare traceback on a
    # stock interpreter. Say what to do instead.
    sys.exit(
        "validate_consistency.py needs PyYAML and this interpreter does not have it.\n"
        "This repo has no install step, so run it one of these ways:\n"
        "    uv run --with pyyaml python scripts/validate_consistency.py --verbose\n"
        "    pip install pyyaml && python3 scripts/validate_consistency.py --verbose\n"
        "CI installs it explicitly; see .github/workflows/validate-plugins.yml."
    )

VERBOSE = "--verbose" in sys.argv
ROOT = Path(__file__).resolve().parent.parent
PLUGINS_DIR = ROOT / "plugins"
SKIP_PARTS = {"__pycache__", "node_modules", ".venv", ".pytest_cache"}

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)
# Greedy first group, so the split lands on the LAST `__`:
# mcp__plugin_mail_outlook-bridge__outlook_list_mail
#   -> ('plugin_mail_outlook-bridge', 'outlook_list_mail')
# The trailing `*` is matched so that prose like `mcp__teams-bridge__teams_*`
# is diagnosed with a copy-pasteable replacement rather than being reported as
# a reference to a tool literally named `teams_`.
MCP_TOKEN_RE = re.compile(r"mcp__([A-Za-z0-9_-]+)__([A-Za-z0-9_]+\*?)")
# An allowed-tools entry, which unlike a body reference may be a bare server
# name or carry a glob. Deliberately ONE character class covering the whole
# entry rather than a server/tool split: an earlier `mcp__([A-Za-z0-9_-]+)(?:__
# ([A-Za-z0-9_*]+))?` swallowed the separating `__` into the greedy server
# class and then failed to match the optional group, so
# `mcp__plugin_mail_outlook-bridge__*` came back as
# `mcp__plugin_mail_outlook-bridge__` with the glob silently dropped and
# matched nothing. That produced 44 false "allowed-tools omits it" warnings.
# Separators in this field are commas, whitespace and brackets, none of which
# are in the class, so a contiguous run is exactly one entry.
MCP_DECL_RE = re.compile(r"mcp__[A-Za-z0-9_*-]+")
# `mcp__*` globs the SERVER segment: legal in a deny rule, inert in an allow
# rule, which is what allowed-tools is.
UNANCHORED_MCP_GLOB_RE = re.compile(r"mcp__\*")
ARGUMENT_RE = re.compile(r"\$ARGUMENTS\b|\$[1-9]\b")
# `${CLAUDE_PLUGIN_ROOT}/mcp-server/run.sh` -> `mcp-server`
SERVER_ROOT_RE = re.compile(r"^\$\{CLAUDE_PLUGIN_ROOT\}/([^/]+)/")
# Parsed, not executed. Every tool module declares its own `name: '...'`.
TS_TOOL_NAME_RE = re.compile(r"""name:\s*['"]([a-z][a-z0-9_]*)['"]""")

errors: list[str] = []
warnings: list[str] = []


def error(msg: str) -> None:
    errors.append(msg)
    print(f"  \033[31m✗\033[0m {msg}")


def warn(msg: str) -> None:
    warnings.append(msg)
    if VERBOSE:
        print(f"  \033[33m!\033[0m {msg}")


def ok(msg: str) -> None:
    if VERBOSE:
        print(f"  \033[32m✓\033[0m {msg}")


def heading(msg: str) -> None:
    print(f"\n\033[1m{msg}\033[0m")


def _is_skipped(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    return any(p.startswith(".") or p in SKIP_PARTS for p in rel.parts)


def _plugin_dirs() -> list[Path]:
    return [d for d in sorted(PLUGINS_DIR.iterdir()) if d.is_dir() and not d.name.startswith("_")]


def _split_frontmatter(path: Path) -> tuple[dict | None, str, str | None]:
    """Return (frontmatter mapping, body, reason it is None).

    The mapping is None when there is no frontmatter or it does not parse.
    Callers that already have another check covering that case ignore the
    reason; callers that are the only check report it."""
    text = path.read_text()
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, text, "no '---' frontmatter block"
    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        # Flattened: PyYAML's message is multi-line and the line/column in it
        # is the whole point of reading it.
        detail = " ".join(str(e).split())
        return None, m.group(2), f"frontmatter is not valid YAML: {detail}"
    if not isinstance(data, dict):
        return None, m.group(2), "frontmatter is not a YAML mapping"
    return data, m.group(2), None


def _declared_mcp_tools(value: object) -> set[str]:
    """Pull the `mcp__...` entries out of an `allowed-tools` value.

    The docs say the field "accepts a space- or comma-separated string, or a
    YAML list", and entries like `Bash(git add *)` and
    `Skill(document-skills:xlsx)` contain both spaces and commas inside
    parentheses. Splitting on either separator therefore mangles them. Scan
    for the tokens we care about instead of trying to tokenise the whole
    field."""
    if value is None:
        return set()
    text = " ".join(str(v) for v in value) if isinstance(value, list) else str(value)
    # `mcp__*` is dropped, not kept: Claude Code skips an unanchored allow glob,
    # so it pre-approves nothing and must not be allowed to suppress a coverage
    # warning. check_allowed_tools_coverage warns about it separately.
    return {d for d in MCP_DECL_RE.findall(text) if d != "mcp__*"}


def _is_declared(tool: str, declared: set[str]) -> bool:
    """All four documented allow-rule shapes, per code.claude.com/docs/en/permissions:
    `mcp__server` (every tool on that server), `mcp__server__*` (same thing,
    wildcard spelling), `mcp__server__get_*` (prefix glob), and the exact
    tool name. Only the server segment has to be glob-free."""
    for d in declared:
        if d == tool:
            return True
        if "*" in d and fnmatch(tool, d):
            return True
        # Bare server name: `mcp__plugin_mail_outlook-bridge` covers all of it.
        if "__" not in d.removeprefix("mcp__") and tool.startswith(d + "__"):
            return True
    return False


def _bundled_mcp_servers() -> dict[str, tuple[str, Path]]:
    """Map each bundled server's ONLY valid token prefix to (server, tools dir).

    Claude Code namespaces an MCP server bundled by a plugin as
    `mcp__plugin_<plugin>_<server>__<tool>`. The bare `mcp__<server>__<tool>`
    spelling reads more naturally and is what this repo used everywhere until
    2026-09-09, but it does not resolve to anything at runtime. Servers
    configured at user scope (second-brain and friends) do stay bare, which is
    why an unrecognised prefix has to be ignored rather than corrected.

    Everything here is derived from the manifests, never hardcoded: the plugin
    name from plugin.json, the server name from the .mcp.json key, and the
    server directory from the path in that server's launch args. A rename in
    any of the three keeps this correct instead of leaving it stale."""
    out: dict[str, tuple[str, Path]] = {}
    for plugin_dir in _plugin_dirs():
        mcp_json = plugin_dir / ".mcp.json"
        pjson = plugin_dir / ".claude-plugin" / "plugin.json"
        if not mcp_json.exists() or not pjson.exists():
            continue
        plugin = json.loads(pjson.read_text()).get("name", plugin_dir.name)
        for server, spec in json.loads(mcp_json.read_text()).get("mcpServers", {}).items():
            server_dir = plugin_dir / "mcp-server"
            for arg in spec.get("args", []):
                m = SERVER_ROOT_RE.match(str(arg))
                if m:
                    server_dir = plugin_dir / m.group(1)
                    break
            out[f"plugin_{plugin}_{server}"] = (server, server_dir / "src" / "tools")
    return out


def _server_tool_names(tools_dir: Path) -> set[str]:
    names: set[str] = set()
    for ts in sorted(tools_dir.glob("*.ts")):
        names.update(TS_TOOL_NAME_RE.findall(ts.read_text()))
    return names


def _rglob(base: Path, pattern: str) -> list[Path]:
    """rglob, minus the vendored trees it would otherwise wander into."""
    if not base.is_dir():
        return []
    return sorted(p for p in base.rglob(pattern) if not set(p.parts) & SKIP_PARTS)


def _command_files() -> list[Path]:
    """Every command file at ANY depth, not just plugins/<x>/commands/.

    The one-level glob this used to use could not see
    plugins/decks/bundled/creative/commands/, which is three real commands the
    marketplace ships. rename-guard.yml and validate-plugins.yml had the same
    blind spot, and a deprecated `Task` in allowed-tools sat green in CI
    because of it."""
    return [p for d in _plugin_dirs() for p in _rglob(d, "commands/*.md")]


def _agent_files() -> list[Path]:
    """Agent-shaped prompt files at any depth, plus AGENT.md.

    Deliberate scope note. Claude Code only DISCOVERS agents in a plugin's own
    agents/ directory, so of the files this returns only plugins/*/agents/*.md
    are loaded as plugin agents at runtime. Anything matched deeper, such as a
    bundled agents/ tree, and any AGENT.md (a filename this repo has used for
    an agent definition sitting outside agents/), is a prompt file some
    pipeline reads by path. Those are included anyway: they are agent
    definitions in every respect that matters to a reader, their frontmatter
    should stay well-formed, and nothing else validates them at all. So this
    check is about the files staying parseable, not about runtime discovery,
    and it stays widened even when no such file currently exists."""
    files: list[Path] = []
    for plugin_dir in _plugin_dirs():
        files.extend(_rglob(plugin_dir, "agents/*.md"))
        files.extend(_rglob(plugin_dir, "AGENT.md"))
    return sorted(set(files))


def _prompt_files() -> list[Path]:
    """Every markdown file that becomes a prompt: commands, agents, skills.

    Also the repo-root shared/ trees, because shared/claude-md-template/ ships
    tool names to users the same way a command does."""
    files = _command_files() + _agent_files()
    for plugin_dir in _plugin_dirs():
        files.extend(_rglob(plugin_dir / "skills", "*.md"))
    files.extend(_rglob(ROOT / "shared", "*.md"))
    return sorted(set(files))


def check_manifests() -> None:
    heading("Plugin manifests")

    mp_path = ROOT / ".claude-plugin" / "marketplace.json"
    if not mp_path.exists():
        error("marketplace.json not found")
        return

    with open(mp_path) as f:
        marketplace = json.load(f)
    registered = {p["name"] for p in marketplace.get("plugins", [])}

    for plugin_dir in sorted(PLUGINS_DIR.iterdir()):
        if not plugin_dir.is_dir() or plugin_dir.name.startswith("_"):
            continue

        pjson = plugin_dir / ".claude-plugin" / "plugin.json"
        if not pjson.exists():
            error(f"{plugin_dir.name}: missing .claude-plugin/plugin.json")
            continue

        with open(pjson) as f:
            data = json.load(f)

        for field in ("name", "version", "description"):
            if field not in data:
                error(f"{plugin_dir.name}/plugin.json: missing '{field}'")

        name = data.get("name", plugin_dir.name)
        if name not in registered:
            error(f"{name}: not registered in marketplace.json")
        else:
            ok(f"{name}: manifest valid, registered in marketplace")

    for name in registered:
        if not (PLUGINS_DIR / name).is_dir():
            error(f"marketplace.json lists '{name}' but plugin directory missing")


def check_command_files() -> None:
    heading("Command files")

    for plugin_dir in _plugin_dirs():
        md_files = _rglob(plugin_dir, "commands/*.md")
        if not md_files:
            warn(f"{plugin_dir.name}: no command files under commands/")
        for cmd_file in md_files:
            with open(cmd_file) as f:
                first_line = f.readline().strip()
            if first_line != "---":
                error(f"{cmd_file.relative_to(ROOT)}: missing frontmatter")
            else:
                ok(f"{cmd_file.relative_to(ROOT)}: frontmatter present")


def check_command_frontmatter_yaml() -> None:
    """Catch YAML hazards: argument-hint with brackets/pipes/colons must be quoted."""
    heading("Command frontmatter YAML safety")

    fm_pattern = re.compile(r"^---\n(.*?)\n---", re.DOTALL)

    for cmd_file in _command_files():
        m = fm_pattern.match(cmd_file.read_text())
        if not m:
            continue
        try:
            yaml.safe_load(m.group(1))
            ok(f"{cmd_file.relative_to(ROOT)}: YAML parses")
        except yaml.YAMLError as e:
            error(f"{cmd_file.relative_to(ROOT)}: YAML parse error: {' '.join(str(e).split())}")


def check_python_tools() -> None:
    heading("Python tools")

    for py_path in sorted(ROOT.rglob("*.py")):
        if _is_skipped(py_path):
            continue
        if py_path.name.startswith("test_"):
            continue
        try:
            compile(py_path.read_text(), str(py_path), "exec")
            ok(f"{py_path.relative_to(ROOT)}: valid syntax")
        except SyntaxError as e:
            error(f"{py_path.relative_to(ROOT)}: syntax error at line {e.lineno}")


def check_brand_system_sync() -> None:
    """No-drift guard: the marketplace-root brand-system mirror must equal the
    canonical decks copy. Fix with scripts/sync_brand_system.sh --apply."""
    heading("Brand-system tree sync (no-drift guard)")
    canonical = PLUGINS_DIR / "decks" / "shared" / "brand-system"
    mirror = ROOT / "shared" / "brand-system"
    if not canonical.is_dir():
        # sync_brand_system.sh exits 2 here. Nothing to compare against, and
        # no way to repair it, so warn and move on.
        warn("brand-system: canonical tree (decks) missing; skipping sync check")
        return
    if not mirror.is_dir():
        # This used to warn and return, which meant deleting the mirror
        # outright passed the no-drift guard while changing one byte of it
        # failed. sync_brand_system.sh --check reports drift for every file in
        # this case; match it.
        error(
            "brand-system: mirror (shared/brand-system) missing entirely; run scripts/sync_brand_system.sh"
        )
        return
    canon = {p.name: p.read_text() for p in canonical.glob("*.md")}
    mir = {p.name: p.read_text() for p in mirror.glob("*.md")}
    for name in sorted(set(canon) - set(mir)):
        error(
            f"brand-system: '{name}' in canonical (decks) but missing from mirror (shared/) — run scripts/sync_brand_system.sh"
        )
    for name in sorted(set(mir) - set(canon)):
        error(
            f"brand-system: '{name}' in mirror (shared/) but not in canonical (decks) — run scripts/sync_brand_system.sh"
        )
    for name in sorted(set(canon) & set(mir)):
        if canon[name] != mir[name]:
            error(
                f"brand-system: '{name}' differs between canonical (decks) and mirror (shared/) — run scripts/sync_brand_system.sh --apply"
            )
        else:
            ok(f"brand-system: {name} in sync")


def check_plugin_versions() -> None:
    """plugin.json and marketplace.json must agree. Claude Code reads the
    version from plugin.json and silently ignores the marketplace.json one, so
    a disagreement is invisible at runtime and wrong in the listing: the worst
    combination."""
    heading("Version agreement (plugin.json vs marketplace.json)")

    mp_path = ROOT / ".claude-plugin" / "marketplace.json"
    if not mp_path.exists():
        return  # check_manifests already reported this

    with open(mp_path) as f:
        marketplace = json.load(f)
    listed = {p["name"]: p.get("version") for p in marketplace.get("plugins", [])}

    for plugin_dir in _plugin_dirs():
        pjson = plugin_dir / ".claude-plugin" / "plugin.json"
        if not pjson.exists():
            continue  # check_manifests already reported this
        with open(pjson) as f:
            data = json.load(f)
        name = data.get("name", plugin_dir.name)
        own = data.get("version")
        theirs = listed.get(name)
        if name not in listed:
            continue  # check_manifests already reported this
        if own != theirs:
            error(
                f"{name}: plugin.json says version '{own}' but marketplace.json says "
                f"'{theirs}'. Claude Code uses plugin.json and ignores the other."
            )
        else:
            ok(f"{name}: version {own} agrees in both manifests")


def check_command_frontmatter_fields() -> None:
    """description / argument-hint / allowed-tools.

    rename-guard.yml checks allowed-tools in bash on push; having it here too
    means a local run catches it before the push rather than after."""
    heading("Command frontmatter fields")

    for cmd_file in _command_files():
        rel = cmd_file.relative_to(ROOT)
        fm, body, _reason = _split_frontmatter(cmd_file)
        if fm is None:
            continue  # missing/unparseable frontmatter is already reported

        for field in ("description", "allowed-tools"):
            if not fm.get(field):
                error(f"{rel}: frontmatter has no '{field}'")

        # argument-hint is only meaningful for a command that consumes input.
        # /chat-inbox takes none and references no $ARGUMENTS, so demanding a
        # hint there would force someone to invent one. Error only where the
        # body actually reads arguments the user gets no hint about; note the
        # rest quietly.
        if not fm.get("argument-hint"):
            if ARGUMENT_RE.search(body):
                error(
                    f"{rel}: body reads $ARGUMENTS but frontmatter has no "
                    f"'argument-hint', so the user gets no prompt for them"
                )
            else:
                warn(f"{rel}: no 'argument-hint' (body takes no arguments)")
        if fm.get("description") and fm.get("allowed-tools"):
            ok(f"{rel}: frontmatter fields present")


def check_mcp_tool_references() -> None:
    """Two guaranteed runtime failures, both errors.

    1. The bare `mcp__<server>__<tool>` spelling for a server this repo
       bundles. That token does not exist; see _bundled_mcp_servers().
    2. A correctly scoped reference to a tool the server does not register.

    A prefix belonging to neither is left alone: it is a user-scope server
    such as second-brain, whose tool list is not in this repo."""
    heading("MCP tool references")

    scoped = _bundled_mcp_servers()
    if not scoped:
        error("no bundled MCP servers found; expected at least one plugins/*/.mcp.json")
        return
    # server name -> the prefix a reference to it must actually use
    bare_to_scoped = {server: prefix for prefix, (server, _) in scoped.items()}

    available: dict[str, set[str]] = {}
    for prefix, (server, tools_dir) in sorted(scoped.items()):
        if not tools_dir.is_dir():
            error(f"{server}: tool directory missing at {tools_dir.relative_to(ROOT)}")
            continue
        names = _server_tool_names(tools_dir)
        if not names:
            # Loud on purpose. Silently parsing zero tools would turn every
            # reference below into a free pass.
            error(
                f"{server}: parsed no tool names from {tools_dir.relative_to(ROOT)}/*.ts "
                f"(has the registration shape changed? see TS_TOOL_NAME_RE)"
            )
            continue
        available[prefix] = names
        ok(f"mcp__{prefix}__: {len(names)} tools registered")

    for path in _prompt_files():
        rel = path.relative_to(ROOT)
        for prefix, tool in sorted(set(MCP_TOKEN_RE.findall(path.read_text()))):
            if prefix in bare_to_scoped:
                error(
                    f"{rel}: mcp__{prefix}__{tool} uses the bare server name, which does "
                    f"not exist at runtime. A plugin-bundled server is namespaced: use "
                    f"mcp__{bare_to_scoped[prefix]}__{tool}"
                )
            elif prefix in available:
                if tool.endswith("*"):
                    # A prose wildcard ("the mcp__..._teams_* tools"). The
                    # prefix is what matters; there is no single tool to look up.
                    ok(f"{rel}: mcp__{prefix}__{tool} is a wildcard reference")
                elif tool not in available[prefix]:
                    error(f"{rel}: mcp__{prefix}__{tool} is not a tool that server registers")
                else:
                    ok(f"{rel}: mcp__{prefix}__{tool} exists")
            # else: user-scope server, not ours to judge


def check_allowed_tools_coverage() -> None:
    """MCP tools a command body calls should be listed in its allowed-tools.

    A WARNING, not an error, and the distinction matters. Per the Claude Code
    docs, allowed-tools PRE-APPROVES tools for the turn that invokes the
    command; it does not restrict which tools are callable. So an omission
    costs the user an extra permission prompt in the middle of a command, not
    a failure, and it is not a security hole. The reverse case (declared but
    never called) is deliberately not flagged: prose mentions a tool without
    emitting the token often enough that reporting it would be pure noise."""
    heading("allowed-tools coverage")

    for cmd_file in _command_files():
        rel = cmd_file.relative_to(ROOT)
        fm, body, _reason = _split_frontmatter(cmd_file)
        if fm is None:
            continue
        raw_allowed = fm.get("allowed-tools")
        # `mcp__*` reads like "every MCP tool" and grants nothing. The docs are
        # explicit: an allow glob must sit after a literal, glob-free
        # `mcp__<server>__` prefix, and "an unanchored allow glob such as
        # `"*"`, `"B*"`, or `"mcp__*"` is skipped with a warning and doesn't
        # auto-approve anything". Silently granting nothing is worse than not
        # writing it, so say so. (Deny rules DO accept `mcp__*`; this is only
        # about the allow position, which is what allowed-tools is.)
        if raw_allowed and UNANCHORED_MCP_GLOB_RE.search(str(raw_allowed)):
            warn(
                f"{rel}: allowed-tools contains an unanchored 'mcp__*'. Claude Code "
                f"skips it and it pre-approves nothing; name a server, as in "
                f"mcp__plugin_mail_outlook-bridge__*"
            )
        declared = _declared_mcp_tools(raw_allowed)
        # Wildcard prose ("the mcp__..._teams_* tools") names no single tool,
        # so there is nothing for allowed-tools to be missing.
        used = {f"mcp__{s}__{t}" for s, t in MCP_TOKEN_RE.findall(body) if not t.endswith("*")}
        missing = sorted(t for t in used if not _is_declared(t, declared))
        for tool in missing:
            warn(f"{rel}: body calls {tool} but allowed-tools omits it (extra permission prompt)")
        if used and not missing:
            ok(f"{rel}: allowed-tools covers all {len(used)} MCP tools used")


def check_agent_files() -> None:
    """Agent definitions had no validation at all before this. See
    _agent_files() for which files count and why."""
    heading("Agent files")

    for agent_file in _agent_files():
        rel = agent_file.relative_to(ROOT)
        fm, _body, reason = _split_frontmatter(agent_file)
        if fm is None:
            error(f"{rel}: {reason}")
            continue
        for field in ("name", "description"):
            if not fm.get(field):
                error(f"{rel}: frontmatter has no '{field}'")
        if fm.get("name") and fm.get("description"):
            ok(f"{rel}: name + description present")


def check_skill_files() -> None:
    """Structural checks only. validate-plugins.yml already enforces the
    description floor, the Greek-script requirement and the negative boundary
    in bash; duplicating those here would mean two places to edit."""
    heading("Skill files")

    for plugin_dir in _plugin_dirs():
        skills_dir = plugin_dir / "skills"
        if not skills_dir.is_dir():
            continue
        for skill_dir in sorted(d for d in skills_dir.iterdir() if d.is_dir()):
            skill_file = skill_dir / "SKILL.md"
            rel = skill_file.relative_to(ROOT)
            if not skill_file.exists():
                error(f"{skill_dir.relative_to(ROOT)}: no SKILL.md")
                continue
            fm, _body, reason = _split_frontmatter(skill_file)
            if fm is None:
                error(f"{rel}: {reason}")
                continue
            for field in ("name", "description"):
                if not fm.get(field):
                    error(f"{rel}: frontmatter has no '{field}'")
            name = fm.get("name")
            if name and name != skill_dir.name:
                error(
                    f"{rel}: frontmatter name '{name}' does not match its directory "
                    f"'{skill_dir.name}'"
                )
            elif name and fm.get("description"):
                ok(f"{rel}: name matches directory, description present")


def main() -> None:
    print("\033[1m\nplessas-marketplace — Consistency Validator\033[0m")
    print("=" * 52)

    check_manifests()
    check_plugin_versions()
    check_command_files()
    check_command_frontmatter_yaml()
    check_command_frontmatter_fields()
    check_agent_files()
    check_skill_files()
    check_mcp_tool_references()
    check_allowed_tools_coverage()
    check_python_tools()
    check_brand_system_sync()

    print("\n" + "=" * 52)
    if errors:
        print(f"\033[31m{len(errors)} error(s)\033[0m, {len(warnings)} warning(s)")
        sys.exit(1)
    print(f"\033[32mAll checks passed\033[0m ({len(warnings)} warning(s))")


if __name__ == "__main__":
    main()
