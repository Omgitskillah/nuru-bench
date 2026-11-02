# Vault and tool-use evaluations

The general Nuru suite, argument-format probes, tier reports and safety checks live here. Laya's training, categorisation, learned-policy replay and their dedicated reports have been retired. Their history remains in Git. This cleanup does not delete local `.runs/` artifacts or model caches.

## Running

Use a Nuru checkout with this repository at `nuru/evals`. Start at that checkout's root:

```sh
uv run --locked python nuru/evals/decision_layer/run_suite.py --tests quick
uv run --locked python nuru/evals/decision_layer/run_suite.py --cases nuru/evals/decision_layer/bench4-cases.json --tests 1-37 --tiers low --repeats 3
uv run --locked python nuru/evals/decision_layer/score_runs.py nuru/evals/decision_layer/.runs/<batch>
uv run --locked python nuru/evals/decision_layer/tier_labels.py nuru/evals/decision_layer/.runs/<batch>
```

Before loading or querying a local model, reserve compute through `.runs/shared-compute/PROTOCOL.md` in Nuru. Use scratch aliases and vaults. Cloud requests require the runner's explicit `--allow-cloud` flag because note content leaves the machine.

`run_suite.py` uses a fresh scratch vault/history/index per case. Sequence turns share that case's Session until completion or a timeout; after a timeout all dependent turns are recorded as not run. The driver no longer starts or polls a learned decision server. Per-turn deadlines request cancellation; the outer process deadline kills and reaps the process group if needed.

## Cases and evidence

- The legacy 34 prompts remain the baseline. `cases.json` adds sequences, including test 38's large-table statistics fixture.
- `bench4-cases.json` retains the full benchmark's additional sequence cases.
- Per-case `vault_files` fixtures are copied into that case's vault and indexed before the request; they are baseline evidence rather than model mutations.
- Batches retain responses, calls, timing, manifests, vault changes and local audit logs under `.runs/`.

Report numerical accuracy, completion, timeouts, skipped turns, controlled stops and unauthorized writes separately. Preserve a declared scoring rule's original result; label revised scoring post-hoc and freeze it before fresh validation. Test 38's historical /5 rule and its per-number/per-question results answer different questions.

## Deterministic safeguards

`--enforce step_cap,write_checks,watch_thinking` or `--enforce all` changes only the batch's deterministic safeguard configuration. It does not fabricate calibration data or enable a learned gate. The shipped Nuru config is left unchanged.

`think_modes.py` and `format_enforcement.py` retain generic thinking/argument-format probes. `tier_labels.py` reports the cheapest tier with at least two passing repeats; it does not train or invoke a decision classifier. Contract probes and unrelated reports remain available.

Context estimates are heuristic. Record effective context and truncation evidence before attributing errors to model quality.
