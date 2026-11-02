"""How many tokens Nuru's texts really cost, per tokenizer, against core.context_budget.estimate_tokens.

Run from a Nuru checkout with this repo at nuru/evals, holding the shared compute lock (it loads models):
    uv run --locked python nuru/evals/token_estimate/measure.py --out nuru/evals/token_estimate/counts-<date>.json \
        qwen3.5:4b-q8_0 granite4.2:3b-q8_0 nemotron-3.5-bolt:e4b

Each text is sent alone as one user message to /api/chat (stream false, think false, truncate false,
num_ctx 32768, num_predict 1) and its count is prompt_eval_count minus that of the message "x": the chat
template's own tokens. Each text goes with a numbered "\n<!-- i -->" tail, so no two prompts are the
same; the counts include that tail while the estimate is of the text alone. So the
counts are close, not exact (that, and tokenization isn't additive at the boundary), and a text is
counted on its own, not inside a whole conversation. The output keeps every text's count per model, the
estimate and the sha256 of the text measured, the Ollama version, each model's digest, this request
shape, and what was measured: the Nuru and bench commits (and whether either had uncommitted changes)
and the sha256 of context_budget.py, so a rerun after either changes can't pass for this calibration.
"""
import argparse
import base64
import hashlib
import json
import random
import subprocess
import urllib.request
from pathlib import Path

from core import context_budget
from core.context_budget import estimate_tokens

EVALS = Path(__file__).resolve().parents[1]
NURU = EVALS.parents[1]
OLLAMA = "http://localhost:11434"
REQUEST = {"stream": False, "think": False, "truncate": False, "options": {"num_ctx": 32768, "num_predict": 1}}


def adversarial() -> dict[str, str]:
    rng = random.Random(81)
    return {
        "adv: underscores": "_" * 2000,
        "adv: spaces": "word" + " " * 2000 + "word",
        "adv: tabs": "\t" * 2000,
        "adv: punctuation run": "!?.,;:()[]{}<>|/\\-+=*&^%$#@~`'\"" * 60,
        "adv: dashes and equals (rules)": ("-" * 80 + "\n" + "=" * 80 + "\n") * 20,
        "adv: long letter run": "a" * 2000,
        "adv: base64": base64.b64encode(rng.randbytes(1500)).decode(),
        "adv: hex hashes": "\n".join(f"{rng.getrandbits(256):064x}" for _ in range(30)),
        "adv: urls": "\n".join(f"https://example.com/path/{rng.getrandbits(40):x}/item?id={i}&ref=abc_def" for i in range(40)),
        "adv: numbers csv": "\n".join(",".join(f"{rng.uniform(-1000, 1000):.4f}" for _ in range(8)) for _ in range(60)),
        "adv: json numbers": json.dumps([{"t": i, "v": round(rng.gauss(0, 50), 3), "ok": i % 3 == 0} for i in range(120)]),
        "adv: chinese": "数据中心的温度在夜间下降，电池电压保持稳定。" * 40,
        "adv: arabic": "درجة الحرارة في الغرفة ترتفع خلال النهار وتنخفض في الليل. " * 30,
        "adv: emoji": "🔋⚡️📈🧪✅❌🙂🚀" * 100,
        "adv: accented prose": "Él está en el café, mañana irá a São Paulo; naïve façade, Zürich, Øresund. " * 25,
        "adv: python code": (NURU / "nuru" / "src" / "core" / "context_budget.py").read_text(encoding="utf-8"),
        "adv: indented markdown": "\n".join("    " * (i % 5) + f"- item {i}: value_{i}" for i in range(120)),
    }


def texts() -> dict[str, str]:
    vault = EVALS / "vaults" / "dummyVault"
    found = {p.relative_to(vault).as_posix(): p.read_text(encoding="utf-8") for p in sorted(vault.rglob("*.md"))
             if ".obsidian" not in p.parts and "Templates" not in p.parts}
    found["system.md"] = (NURU / "nuru" / "modelfiles" / "system.md").read_text(encoding="utf-8")
    soak = (EVALS / "decision_layer" / "fixtures" / "soak-test-v0.9.4-log.md").read_text(encoding="utf-8")
    found["soak table"] = soak
    for name in ("soak table", "nuru/home-lab-parts-inventory.md", "nuru/one-on-one-with-manager.md"):
        found["json: " + name] = json.dumps({"path": name, "content": found[name]}, ensure_ascii=False)
    return {**found, **adversarial()}


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def revision(repo: Path) -> dict:
    """The commit `repo` is at, and whether it has uncommitted changes (which that commit doesn't hold)."""
    def git(*args):
        return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()
    return {"commit": git("rev-parse", "HEAD"), "uncommitted_changes": bool(git("status", "--porcelain"))}


def post(path: str, body: dict) -> dict:
    request = urllib.request.Request(OLLAMA + path, json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=600) as response:
        return json.load(response)


def count(model: str, text: str) -> int:
    return post("/api/chat", {"model": model, "messages": [{"role": "user", "content": text}], **REQUEST})["prompt_eval_count"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("models", nargs="+")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    corpus = texts()
    with urllib.request.urlopen(OLLAMA + "/api/version") as response:
        version = json.load(response)["version"]
    with urllib.request.urlopen(OLLAMA + "/api/tags") as response:
        tags = {m["name"]: m["digest"] for m in json.load(response)["models"]}
    counts = {}
    for model in args.models:
        base = count(model, "x")
        counts[model] = {name: count(model, text + f"\n<!-- {i} -->") - base for i, (name, text) in enumerate(corpus.items())}
        post("/api/generate", {"model": model, "keep_alive": 0})
    rows = []
    for name, text in corpus.items():
        real = max(counts[m][name] for m in args.models)
        rows.append({"text": name, "sha256": sha256(text), "chars": len(text), "estimate": estimate_tokens(text),
                     "counts": {m: counts[m][name] for m in args.models}, "ratio": round(estimate_tokens(text) / real, 3)})
    ratios = [r["ratio"] for r in rows]
    args.out.write_text(json.dumps({
        "ollama": version, "models": {m: tags.get(m) for m in args.models},
        "request": {**REQUEST, "messages": "[{role: user, content: <text>\\n<!-- i -->}]", "baseline": "the same request with content 'x'"},
        "measured": {"nuru": revision(NURU), "bench": revision(EVALS),
                     "estimator_sha256": sha256(Path(context_budget.__file__).read_text(encoding="utf-8"))},
        "caveat": "counts include the numbered tail and the boundary with the template; the estimate is of the text alone",
        "summary": {"texts": len(rows), "min_ratio": min(ratios), "max_ratio": max(ratios),
                    "under": [r["text"] for r in rows if r["ratio"] < 1]},
        "rows": rows}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"min": min(ratios), "max": max(ratios), "under": [(r["text"], r["ratio"]) for r in rows if r["ratio"] < 1]}))


if __name__ == "__main__":
    main()
