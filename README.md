# Live Defense Bench: run transcripts

The cleaned records of the 120 graded runs behind the article
[Live Defense Bench](https://kalligator.com/research/live-defense-bench): 8 models, 5 scenarios, 3 runs each.
The benchmark code is in [live-defense-bench](https://github.com/nwang783/live-defense-bench).

## Layout

```
runs/
  index.json               one row per run: model, scenario, seed, the four checks, solved
  defender_prompt.md       the prompt that every defender got
  <model>/<scenario>-seed<N>/
    transcript.jsonl       what the defender did, in order
    notes.jsonl            the defender's scratch pad (at_s = seconds into the shift)
    reports.json           the reports that the defender sent
    intruder.jsonl         the scripted intruder's steps and whether each one worked
    result.json            the four checks and the facts behind them
```

A row of `transcript.jsonl` has a time `t` (Unix seconds) and a `kind`:

| kind | content |
|---|---|
| `model` | what the model said and the tool calls it made |
| `shell` | a command the model ran, and on which host |
| `output` | what the host printed back |
| `report` | a report: `under_attack`, `attacker_ips`, `hosts_reached`, `summary` |
| `idle` | the harness told the model that the shift is still running |

## What to know before you use it

- Every person, password, key, token and address of Larkspur Cycles is fiction. Secret scanners will flag
  some of these values. They open nothing.
- We removed the harness rows (logins, sessions, rate limits, costs) and replaced local paths. The range makes a
  random Stripe-shaped key for each run, and we wrote `sk_fake_` for its `sk_live_` prefix, because code hosts
  block a push that has one. We changed nothing else in what the models said or did.
- The GPT models ran through a tool that records commands and results but no reasoning text. Most reasoning
  blocks of the Claude models are empty too. The scratch pad notes are the best view of why a model acted.
- GPT-6 Sol ran with the provider's cyber access program, and every other model ran with standard access.
- One result is corrected by hand after review (GPT-6 Astra, s3, seed 26). Its `result.json` has a `note`.
- `clean_runs.py` is the script that made this copy from the private run folders.

License: MIT.
