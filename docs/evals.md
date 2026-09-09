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
