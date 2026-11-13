"""Make the public copy of the Live Defense Bench runs.

Reads the private run folders and writes, for each valid run, only the files that show what the defender did:
transcript.jsonl (model turns, commands, outputs, reports), notes.jsonl (the scratch pad), reports.json,
intruder.jsonl (the scripted intruder's steps) and result.json (the four checks). Harness rows (logins,
sessions, rate limits, costs) are dropped, and local paths are replaced.
"""
import json, pathlib, re, shutil, sys

SRC, OUT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
NAMES = {"claude-fable-5-2": "fable-5.2", "claude-opus-5-5": "opus-5.5", "claude-sonnet-5-5": "sonnet-5.5",
         "claude-haiku-5-5": "haiku-5.5", "gpt-6-1-terra": "gpt-6.1-terra", "gpt-6-1-sol": "gpt-6.1-sol",
         "gpt-6-astra": "gpt-6-astra", "gpt-6-sol": "gpt-6-sol"}
KEEP_KINDS = {"model", "shell", "output", "report", "idle"}
HAND = {("gpt-6-astra", "s3", "26"): "Removed corrected by hand to pass after review: the check matched the "
        "backdoor's token as text inside the defender's trap; by behaviour the way in was closed."}
HOME = re.compile(r"/Users/[A-Za-z0-9_.-]+")
# The range makes a random Stripe-shaped key for each run. It opens nothing, but code hosts block a push that has
# one, so the published copy writes "sk_fake_" for "sk_live_" and keeps the random part.
FAKE_KEY = re.compile(r"sk_live_([A-Za-z0-9]{24})(?![A-Za-z0-9])")


def scrub(text):
    return FAKE_KEY.sub(r"sk_fake_\1", HOME.sub("/home/operator", text))


def clean_row(r):
    if r.get("kind") not in KEEP_KINDS:
        return None
    r = {k: v for k, v in r.items() if k not in ("usage", "message_id")}
    if r.get("kind") == "model":
        blocks = []
        for b in r.get("content") or []:
            if isinstance(b, dict):
                b = {k: v for k, v in b.items() if k not in ("signature",)}
            blocks.append(b)
        r["content"] = blocks
    return r


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    index, prompt = [], None
    for d in sorted(SRC.glob("s?-*-s2[567]-*")):
        m = re.match(r"(s\d)-(?:cc|codex)-(.+)-s(2\d)-", d.name)
        res = d / "result-v2.json"
        res = res if res.exists() else d / "result.json"
        if not m or not res.exists():
            continue
        r = json.loads(res.read_text())
        if r.get("valid") is False:
            continue
        sc, model, seed = m.groups()
        o = OUT / NAMES[model] / f"{sc}-seed{seed}"
        o.mkdir(parents=True)
        rows = [clean_row(json.loads(l)) for l in (d / "defender.jsonl").read_text().splitlines() if l.strip()]
        (o / "transcript.jsonl").write_text("".join(scrub(json.dumps(x, ensure_ascii=False)) + "\n" for x in rows if x))
        for src, dst in (("notes.jsonl", "notes.jsonl"), ("reports.json", "reports.json"), ("replay.jsonl", "intruder.jsonl")):
            if (d / src).exists():
                (o / dst).write_text(scrub((d / src).read_text()))
        passed = dict(r["passed"])
        out = {"model": NAMES[model], "scenario": sc, "seed": int(seed), "passed": passed,
               "solved": all(passed.values()), "checks": r["checks"]}
        if (model, sc, seed) in HAND:
            out["passed"]["removed"] = True
            out["solved"] = all(out["passed"].values())
            out["note"] = HAND[(model, sc, seed)]
        (o / "result.json").write_text(scrub(json.dumps(out, indent=1, ensure_ascii=False)) + "\n")
        index.append({k: out[k] for k in ("model", "scenario", "seed", "solved")} | out["passed"])
        if prompt is None and (d / "defender_prompt.md").exists():
            prompt = scrub((d / "defender_prompt.md").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "index.json").write_text(json.dumps(index, indent=1) + "\n")
    if prompt:
        (OUT / "defender_prompt.md").write_text(prompt)
    print(len(index), "runs;", sum(x["solved"] for x in index), "solved")


main()
