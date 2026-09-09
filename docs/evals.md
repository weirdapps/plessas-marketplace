# Plugin evals

`claude plugin eval` runs each plugin against real prompts twice, once with the
plugin loaded and once without, and reports the difference. That difference, not
the raw score, is the number that says whether a plugin earns its place.

This is the only thing in the repo that measures whether a plugin **helps**.
`pytest`, `plugin validate --strict` and `validate_consistency.py` all check that
the plugins are well-formed. None of them can tell you that `decks` produces a
better board deck than no plugin at all.

---

## Availability: the command is gated

`plugin eval` is in early access and enabled per organisation. On a machine that
cannot receive that rollout, the command exists but does nothing except print:

```
`plugin eval` is currently in early access
```

It exits 0 while doing so, so a CI step that only checks the exit code will go
green having run no evals at all.

This repo's machines route Claude through **Vertex**, which is one of the
categories the rollout cannot reach (alongside Bedrock, Foundry, LLM gateways,
telemetry-disabled clients and CI runners). The documented enablement variable
for exactly that case is:

```bash
export CLAUDE_CODE_WALNUT_SPIRE=1
```

Set it in the shell, in `~/.claude/settings.json` under `env`, or in managed
settings `env`. A repository-local `.claude/settings.json` will **not** work: as
of 2.1.257 repo-local `env` is ignored for this, silently.

## Second prerequisite: credentials survive the sandbox

Each case runs in a sandbox with a **sealed, replaced `HOME`**. On Vertex that
means `gcloud`'s application-default credentials at
`~/.config/gcloud/application_default_credentials.json` are no longer where the
SDK looks, and every agent run dies with:

```
API Error: Could not load the default credentials.
```

The run still completes, still scores, and still reports a cost, so this failure
looks like a plugin that scored zero. Point the SDK at the file by absolute path
before running:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/gcloud/application_default_credentials.json"
```

Keep this in the environment, not in a case file. Case files are committed and
must contain no absolute paths.

---

## Layout

The eval directory lives **below each plugin**, not at the repo root. The runner
resolves it relative to the plugin under test, and `experimental.evals` in
`plugin.json` can rename it. We use the default, `evals/`:

```text
plugins/<name>/evals/
├── 01-<slug>/                  the should-fire case
│   ├── prompt.md               frontmatter + the user prompt
│   └── graders/
│       └── <grader>.md         one file per grader; filename is the grader name
├── 02-neg-<slug>/              the adjacent should-NOT-fire case
│   └── ...
└── mocks/                      only for plugins with a bundled MCP server
    └── <server-key>/           the key from .mcp.json, e.g. outlook-bridge
        └── <tool>.md           bare tool name, no mcp__ prefix
```

`prompt.md` frontmatter accepts `max_turns`, `timeout_seconds`, `allowed_tools`,
`model`, `env`, `append_system_prompt` (execution keys) and `runs`, `tags`,
`name`, `description`, `plugins`, `expected_outcome` (top-level keys). Anything
else is a hard error naming the bad key.

Grader frontmatter takes `type:` from `regex`, `tool_order`, `tool_used`,
`file_exists`, `llm`, `baseline`, plus `weight:` and `arm:`. For `llm` and
`regex` the body of the file is the rubric or the pattern.

---

## Running them

```bash
export CLAUDE_CODE_WALNUT_SPIRE=1
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/gcloud/application_default_credentials.json"

# one plugin, both arms, one run per case (the pilot form)
claude plugin eval plugins/docs \
  --runs 1 --ablation with-without --no-scaffold --no-publish \
  --allow-tools Write Bash

# the full suite as authored (runs: 3 per case)
claude plugin eval plugins/docs --ablation with-without --no-publish
```

Results land in `plugins/<name>/evals/results/<timestamp>/` as
`aggregate-result.json` plus a self-contained `report.html`. **`results/` is
disposable output, not source.** Add `--json <path>` to write the machine-readable
result somewhere else; note that `--json` suppresses the console summary table.

`--allow-tools` is an operator grant, separate from the case's `allowed_tools`.
A tool needs to be in **both** to be callable: `allowed_tools` declares it,
`--allow-tools` un-gates it. The grant applies to both arms, which is what keeps
the comparison fair.

---

## Reading the ablation delta

The runner reports three numbers per case: `with`, `without`, and `Δ`.

| Pattern | What it means |
| --- | --- |
| `with` high, `without` low | The plugin is doing the work. This is the result you want. |
| `with` high, `without` high | The base model already handles it. The plugin is not adding measurable value **on this grader** — either the grader is generic, or the plugin genuinely is not needed here. |
| `with` low, `without` low | **A broken case, not a broken plugin.** Almost always a missing tool, an under-set `max_turns`/`timeout_seconds`, or a grader checking a surface the run never produces. Fix the case before drawing any conclusion. |
| `with` low, `without` high | The plugin actively made things worse. Rare and worth stopping for. |

A `tool_used: Skill` grader on the plugin under test is a **plugin-fired
indicator, not part of the score**. The runner marks it `with-only` and excludes
it from both arms, because it can never move Δ (the skill cannot fire in the
arm where the plugin is not loaded). It is displayed so you can tell "the skill
fired and the answer was still wrong" from "the skill never fired". Never let it
be a case's only grader.

To assert a tool was **not** called, `min: 0`, `max: 0` **and** `arm: both` are
all required. Omitting `min` leaves it at 1; omitting `arm` on `tool: Skill`
makes the grader display-only, so it silently stops being an assertion.

---

## What a case must not do

**Never name the skill, the plugin or the command in the prompt.** A prompt that
says "use the presentations skill" measures nothing except whether the model can
follow an instruction. Every prompt here is worded the way someone who has never
read the SKILL.md would say it: "The board sits on Thursday and I have to take
them through why card revenue is running behind", not "create a presentation".

**Never lift a prompt from the SKILL.md.** Its `description` field lists example
phrasings. Testing those measures the routing table against itself.

**Never let a case touch a real service.** Every plugin with a bundled MCP server
has a full mock set under `evals/mocks/<server>/`, one file per tool, covering
every tool the server exposes and not just the ones the happy path calls. Three
independent guards keep sends from escaping:

1. `--mocks record` is the default. It substitutes the mock set for the real
   server, so the server never starts and never authenticates.
2. Every send/mutate tool is mocked with `error: true`, so an attempted call
   fails inside the harness instead of reaching a service.
3. Each such case carries a scored `tool_used` grader with `min: 0, max: 0,
   arm: both` on the send tool, so an attempt is a visible test failure.

Guard 3 must name the **fully namespaced** tool, which inside the sandbox is
`mcp__plugin_<plugin>_<server>__<tool>`, for example
`mcp__plugin_mail_outlook-bridge__outlook_send_mail`.

Do **not** implement that guard as a `regex` with `match: not_contains` over
`target: trace`. The trace opens with a `system/init` event listing every
available tool by name, so the pattern matches the tool *inventory* and the
grader fails on runs where nothing was called. That mistake was made here first
and produced a false "it sent mail" on six consecutive runs that had called only
`Glob` and `ToolSearch`.

**Do not grade the plugin's house rules against `last_message`.** The last
message is Claude's conversational prose about the artifact, not the artifact.
A "no em-dashes" regex over it fails on the sentence describing a document that
itself contains no em-dashes. Grade house rules against `trace` (did the run
commit to the standard) or against the created file via
`{source: file, path: ...}`.

---

## The judge

`--judge-model` defaults to `haiku`. That is a **tier alias**, and this repo's
machines remap the tier aliases to Opus 5:

```
ANTHROPIC_DEFAULT_HAIKU_MODEL=claude-opus-5[1m]
```

So the "cheap haiku judge" is Opus 5 here. It works, and it is not worth fighting
because the judge is a rounding error: across the measured runs the judge was
**1 to 3 per cent** of total cost. The agent runs are the entire bill. Do not
pass a bare `sonnet`/`haiku` alias to `--judge-model` hoping to save money on a
Vertex machine: models at or below 4.6 need `europe-west1` while the run inherits
`CLOUD_ML_REGION=eu`, and the mispairing returns 429.

Each `llm` grader is judged three times and reported as `PASS PASS PASS`. A split
vote is the signal that the rubric is ambiguous.

---

## Cost

Measured on this repo, 2026-09-09, Claude Code 2.1.265, Opus 5 on Vertex:

| Scope | Cost | Wall clock |
| --- | --- | --- |
| One case, one run, both arms | $0.20 to $3.00 | 40 s to 8 min |
| All 12 cases, one run, both arms (the pilot) | **$11.78** | ~17 min at 3 suites in parallel |
| All 12 cases, `runs: 3`, both arms (the full suite) | **~$35** | ~50 min at 3 suites in parallel |

The spread per case is wide and it tracks how much work the plugin does. The two
cheapest cases are negatives that resolve in 2 to 3 turns (~$0.20 each). The most
expensive is `docs/01-letter-to-regulator` at $2.98, because the plugin actually
builds the document. Suites run their own cases serially, so parallelism has to
come from running plugins concurrently. Three at a time is comfortable; six at a
time was not tested against Vertex rate limits.

Always pass `--max-cost-usd` in automation. It aborts and reports partial results
with exit 2, and the overrun is bounded to a single agent run.

---

## Known limits

- **Binary artifacts cannot be graded directly.** `.pptx`, `.docx`, `.xlsx` and
  `.pdf` are opaque to every grader type. An `llm` grader pointed at a PNG/JPEG
  via `{source: file, path}` does see it as an image, so the way to grade a
  rendered slide is to have the case export one. These cases grade the trace and
  the last message instead, which measures the decision and the standard applied,
  not pixel fidelity. Pixel fidelity is `nbg_validate.py`'s job.
- **The sandbox has no project toolchain.** No `python-docx`, no `pptxgenjs`, no
  network install. Plugins that need them adapt (the `docs` run emitted Word XML
  instead of `.docx`), which is realistic behaviour but is not the production path.
- **`--scaffold` runs author-supplied bash as you.** Every command here passes
  `--no-scaffold`, and no case ships a `scaffold_script`. Keep it that way in CI.
- **`results/` accumulates.** Each run writes a timestamped directory with an
  HTML report. Prune it; it is not source.

---

## Gotchas

Each of these cost real money to discover. Verified against Claude Code 2.1.266
on 2026-09-09 unless noted.

### The plugin may not be loaded at all, and nothing on the surface says so

`plugin validate --strict`, `plugin details` and the eval's own banner
(`Plugin under test: "meetings" version "1.1.0" at ...`) all report a healthy
plugin that the runtime went on to **disable**. They read the manifest; they do
not observe the session.

**The only thing that tells the truth is line 1 of `out/trace.jsonl`**, the
`system/init` event. Check two fields:

```bash
python3 -c 'import json;o=json.loads(open("<temp>/out/trace.jsonl").readline());
print(o["plugins"], o.get("plugin_errors"))'
```

`plugins: []` means the plugin did not load, and every "with" arm number in that
run is a bare model. Read it on **every** run before reading any score.

### A hard `dependencies` entry makes a plugin unevaluable in isolation

The scaffold loads the target plugin and nothing else, and the sandbox replaces
`HOME`, so user-scope installed plugins are invisible inside it. A
`"dependencies": ["mail"]` in the manifest therefore can never be satisfied:

```json
{"plugin": "meetings@inline", "type": "dependency-unsatisfied",
 "message": "Dependency \"mail\" is not installed ..."}
```

There is no `plugin eval` flag that adds a second plugin to the arm, and the one
escape hatch that looks like it should work does not. A case may declare
`plugins: [...]` naming extra plugin directories, but they are fenced:

```
plugins entry "../../../mail" resolves to .../plugins/mail, outside the
containment root .../plugins/meetings (the enclosing plugin for a target inside
one you control, else the directory you ran 'claude plugin eval' against).
Only plugins under it can be loaded from case.yaml.
```

When the target *is* a plugin directory, the containment root is that plugin, so
a sibling under `plugins/` can never be added. Relative, absolute and
repo-rooted spellings all fail; the first three fail as "does not exist" and
only a path that actually resolves reports the containment error.

Note this also disables the plugin's skills, so its `tool_used: Skill` grader
reports `Skill called 0x` while the score table still prints a plausible-looking
number.

**Do not "fix" this by deleting the `dependencies` entry.** That reads like the
obvious unblock and it is the wrong trade. Per the plugin-dependencies reference,
the key is not a load-time gate in production. It is what makes Claude Code
resolve and install `mail` automatically when someone installs `meetings`, enable
it transitively at the same scope, and refuse `claude plugin disable mail` while
`meetings` still needs it (the error even prints the chained command to disable
both in the right order). Removing it degrades every real install so that one
harness can print a number.

The supported way to satisfy a dependency from a local checkout is to pass both
plugins on one command line:

```bash
claude --plugin-dir ./plugins/mail --plugin-dir ./plugins/meetings
```

"The local copy of the dependency satisfies your plugin's dependency entry, even
when the entry names a marketplace." `claude plugin eval` does not expose
`--plugin-dir`, so that route is open to a hand-driven session and closed to this
harness.

**The fix is to declare the dependency in the marketplace entry instead of the
plugin manifest.** A plugin can depend on another "by listing them in
`plugin.json` or in its marketplace entry", and the two are equivalent for a
marketplace install. Only the manifest copy travels into the eval sandbox,
because the sandbox loads the plugin directory as `<name>@inline` and never
reads `marketplace.json`. So moving the array from
`plugins/meetings/.claude-plugin/plugin.json` to the `meetings` entry in
`.claude-plugin/marketplace.json` keeps auto-install, transitive enable and the
disable guard for every real user, and leaves nothing unsatisfiable in the
sandbox.

Verified on `03-put-that-somewhere-i-can-find-it`, trace line 1:

```text
before  with: plugins=[]                       errors=[dependency-unsatisfied]
after   with: plugins=[{"name":"meetings",...}] errors=[]
              skills=[..., "meetings:meeting-workflows", ...]
        without: plugins=[]                     (no meeting-workflows)
```

That is the difference between an ablation whose two arms are the same
configuration and one that actually measures something. If you add a dependent
plugin later, declare it in the marketplace entry from the start.

### Mocks are served in BOTH arms

A mocked MCP server is registered as a standalone stand-in, independent of the
plugin, and appears in the `without` arm too. So the ablation never measures
"has tools versus has no tools", only the plugin's own components. Combined
with the point above, a disabled plugin makes the two arms byte-identical and
every Δ is sampling noise.

Two consequences of the standalone registration:

- **Inside the sandbox the mocked tools are named bare**, `mcp__<server>__<tool>`
  (for example `mcp__outlook-bridge__outlook_list_mail`), not the
  `mcp__plugin_<plugin>_<server>__<tool>` form a plugin-bundled server gets in a
  normal session. That is what `system/init` lists and what the calls are logged
  under. The runner has been seen resolving a grader's bare `tool:` both ways:
  the 2026-09-09T00-26 `meetings` aggregate recorded it expanded to
  `mcp__plugin_mail_outlook-bridge__outlook_send_mail`, later runs the same day
  recorded it bare. An expanded name can never match a bare trace, and a
  `min: 0, max: 0` guard that never matches passes silently. Do not assume a
  passing guard fired: cross-check `out/mock-calls.jsonl`, which logs the tool
  name and the input of every mock call actually made.
- The runner prints `not granted (missing --allow-tools grant, or a malformed
  entry): mcp__<server>__*` for the case's `allowed_tools` entry even though the
  mocked tools are served anyway. Alarming, harmless.

### `--runs`, and why `runsPerCase` in the JSON cannot be trusted

`--runs` defaults to the case's `runs:` value, falling back to 3, so a case that
says `runs: 1` runs **once** unless you override it. Always pass `--runs`
explicitly.

`aggregate-result.json` reports the count in a field called `runsPerCase`, and
that field has been observed disagreeing with reality in both directions on
cases whose frontmatter says `runs: 1`:

| Invocation | `runsPerCase` | entries in `arms.with` |
| --- | --- | --- |
| 2026-09-09T00-26, cases 01/02 | 3 | 1 |
| 2026-09-09 measurement, `--runs 3` | 1 | 3 |

Count `len(arms.with)`. Never read `runsPerCase`.

### `--case` takes `*` and nothing else

`--case '0[35]*'` matches zero cases and reports exactly what a deliberately
bogus glob reports:

```
No eval cases found matching --case "0[35]*" under .../plugins/meetings.
```

Character classes, braces and alternation are not honoured. For a subset, run
one invocation per case, or use `--tag` (repeatable) if the tags separate them.

### Always pass `--keep-temp`

Without it the sandbox is deleted and all the CLI retains is `tracePath`,
pointing at a directory that no longer exists. With it you get:

- `out/trace.jsonl`, line 1 for plugin load state and the rest for the transcript
- `out/mock-calls.jsonl`, one line per mock call with its **input arguments**,
  the fastest way to see what the run actually asked each tool for
- `out/mocks/`, the stand-in config that was generated

Kept directories are sealed at mode `000`. Open with
`chmod 700 <dir> <dir>/sealed`, and do not run `git` anywhere inside one.

### `~/Downloads` does not exist for a grader

The run's cwd is a sandboxed temp dir under a replaced `HOME`. A skill that
writes to `~/Downloads/...` succeeds, into the sandbox's `HOME`, and a
`file_exists` grader pointed at the real path finds nothing. Grade the write
with `tool_used: Write` plus a `regex` over `target: trace` for the filename
pattern, which is what `excel/03` does.

### `tool_used: Skill` is an indicator, not a score

Under `--ablation with-without` it is marked `with-only` and excluded from both
arms, because the skill cannot fire in the arm without the plugin. Read its
explanation string (`Skill called 0x`), never its contribution to the number,
and never let it be a case's only grader. Every other grader type defaults to
`arm: both` and **is** scored, including `llm`.

### Environment: two exports, both mandatory

```bash
export CLAUDE_CODE_WALNUT_SPIRE=1
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/gcloud/application_default_credentials.json"
```

The first un-gates the early-access command on a Vertex client; without it the
command prints one line and exits 0. The second survives the sealed `HOME`,
which is where `gcloud`'s ADC otherwise goes missing. Neither can live in a
repo-local `.claude/settings.json`.

---

## Writing mocks that do not lie

A `fixed` responder returns one canned body for **every** call. `{{input.<field>}}`
interpolates a field of the call into that body, and that is the whole of its
input-awareness: it cannot select a different record per id, folder or date
range.

The failure mode this creates is worse than returning nothing. Echoing
`{{input.id}}` into a record that is *not* the requested one stamps the
requested id onto someone else's message, and the run reads the wrong body
believing it is the right one. `outlook_get_mail` did exactly that here: every
call came back as the Anna Vidal audit mail wearing whatever id had been asked
for.

Two ways out:

1. **Over-return, and say so.** Return the whole store and open the body with a
   `_mock` field stating which arguments the stand-in ignores and what was
   actually requested. The model filters client-side, and it can see that the
   result is not a selection. Deterministic and free. This is what the
   `meetings` mocks do, and a run was observed reading the disclosure and
   correctly discounting the result.
2. **`type: agent` in `mocks/<server>/_server.md`**, with `tools: [...]` and a
   prose description of the fake world. An LLM plays the server and *can*
   dispatch on input. It costs one model call per tool call (budget
   `4 × max_turns`), and it can invent, which is fatal for any grader that tests
   whether the run invented anything. Answers can be pinned into
   `<eval dir>/.replay/` for determinism. A per-tool `<tool>.md` overrides
   `_server.md` for that tool, so delete the file for any tool the agent should
   answer.

Also: **save `_tools.json`.** Without `mocks/<server>/_tools.json` the runner
warns that the tools are `served with a permissive schema and no description`,
so the model sees a name and nothing else. For a server in this repo you can
capture the real `tools/list` with no credentials by driving
`mcp-server/run.sh` over stdio with an `initialize` + `tools/list` exchange.

**A mock is a fixture, and a fixture that contradicts the case is a broken
test.** Before trusting a low score, check that the corpus actually contains
what the prompt refers to: `meetings/05` tested tense ambiguity about a meeting
that did not exist in the calendar, and `meetings/04` asked for the user's own
sent mail from a store whose `outlook_list_folders` advertised a Sent Items
folder that no tool could return anything from.
