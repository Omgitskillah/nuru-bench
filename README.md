# nuru-bench

Nuru's benchmark and evals: the vault test suite, its scorers and cases, the sample vault, the steward/planner/tool evals and their write-ups. They were split out of [Nuru](https://github.com/Omgitskillah/Nuru) (`nuru/evals/`, history kept), so that cloning or installing Nuru doesn't bring them along.

## Getting it into a Nuru checkout

The suite runs against Nuru, so it lives inside a Nuru checkout at `nuru/evals`, as a submodule. That submodule is marked `update = none`, which means `git clone --recursive` and `git submodule update --init --recursive` skip it. Fetch it explicitly:

```sh
git submodule update --init --checkout nuru/evals
```

If an older checkout still has a `nuru/evals` folder (untracked `.runs/` batches left behind after the evals were removed from Nuru), the submodule can't check out into it. Use Nuru's `tools/fetch_bench.py` instead, from the checkout's root:

```sh
uv run --locked python tools/fetch_bench.py
```

It moves the old folder to a new, uniquely named backup under `.runs/` (on the same disk, and never deleted), checks the submodule out, then moves each `.runs/` folder back to where it was. An existing `.runs/` is never overwritten: that one stays in the backup, and the script says so. If the checkout fails, the old folder goes back as it was.

## What's here

- `decision_layer/`: the vault suite.
  - `run_suite.py` runs prompts through Nuru, one fresh scratch vault per case.
  - `score_runs.py` scores them.
  - `cases.json` holds the numbered sequence cases.
  - `bench4-cases.json` is the case file the full bench runs use: 35–37 and the multi-turn 101–112.
  - `fixtures/` holds notes that only one case needs, copied into that case's vault (`vault_files`).
  - See [decision_layer/README.md](decision_layer/README.md).
- `vaults/dummyVault/`: the sample vault every suite run copies; `NURU_EVAL_VAULT` overrides it.
- `multi_turn/`, `model_bakeoff/`, `tool_checks/`, `vault_steward/`, `obsidian_remote/`: the other evals.
- `token_estimate/`: how many tokens Nuru's texts really cost per tokenizer, against Nuru's estimate (`core/context_budget.py`): `measure.py` and its dated `counts-*.json`.
- `tools/coverage_check.py`: the coverage rule CI holds the bench's changed modules to.
- `tests/`: the bench's own tests (runner, scorers, manifest, cases). They use Nuru's test setup (`nuru/tests/conftest.py`) through `tests/conftest.py`.
- `*.md` at the top: the dated write-ups of earlier checks.

## Running

From the root of the Nuru checkout:

```sh
uv run --locked pytest nuru/evals/tests                      # the bench's tests, no model
caffeinate -i uv run python nuru/evals/decision_layer/run_suite.py --tests quick
caffeinate -i uv run python nuru/evals/decision_layer/run_suite.py \
  --cases nuru/evals/decision_layer/bench4-cases.json --tests 1-37 --tiers low --repeats 3
```

Batches go to `decision_layer/.runs/` (ignored). Before any run that loads a local model, take the shared compute lock (`.runs/shared-compute/PROTOCOL.md` in the Nuru checkout).

## CI

[`.github/workflows/tests.yml`](.github/workflows/tests.yml) checks out Nuru's `main`, puts this repo at `nuru/evals` and runs `tests/` on Ubuntu. It then holds the modules listed in `tools/coverage_check.py` to Nuru's rule: above 90% of their lines, and all of them in a module of at most 150; add a module there when you change its code. A manual run can also do the 1K/10K stewardship scale evaluation, which used to be an option in Nuru's CI.
