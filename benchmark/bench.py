#!/usr/bin/env python3
"""Benchmark legacy slugify: upstream reference vs. patched implementation.

Usage: python benchmark/bench.py --out benchmark/raw
Writes one JSON sample per (impl, scale, run) plus a summary on stdout.
"""
import argparse
import importlib.util
import json
import random
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

SEED = 20261030
SCALES = (500, 2000, 8000)
WARMUP = 3
RUNS = 5
WORDS = ["Hello", "World", "Python", "Café", "naïve", "2024", "Test_Case",
         "foo bar", "ÄÖÜ", "影師嗎", "Компьютер", "x" * 20]


def make_cases(n):
    rng = random.Random(SEED)
    return [" ".join(rng.choices(WORDS, k=rng.randint(1, 6))) for _ in range(n)]


def load_reference():
    spec = importlib.util.spec_from_file_location(
        "reference_legacy", ROOT / "tests" / "reference_legacy.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.slugify


def load_patched():
    from slugify import slugify
    return slugify


def summarize(samples):
    vals = sorted(samples)
    return {
        "median_s": round(statistics.median(vals), 6),
        "p25_s": round(vals[len(vals) // 4], 6),
        "p75_s": round(vals[(3 * len(vals)) // 4], 6),
        "runs": len(vals),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="benchmark/raw")
    args = ap.parse_args()
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    impls = {"baseline": load_reference(), "optimized": load_patched()}
    summary = {"seed": SEED, "warmup": WARMUP, "runs": RUNS, "scales": {}}
    for scale in SCALES:
        cases = make_cases(scale)
        for impl, fn in impls.items():
            for case in cases:
                fn(case)  # warm the code path, not timed
            samples = []
            for run in range(WARMUP + RUNS):
                t0 = time.perf_counter()
                for case in cases:
                    fn(case)
                dt = time.perf_counter() - t0
                if run >= WARMUP:
                    samples.append(dt)
                    rec = {"impl": impl, "scale": scale, "run": run - WARMUP,
                           "cases": scale, "elapsed_s": round(dt, 6),
                           "per_call_us": round(dt / scale * 1e6, 3),
                           "seed": SEED, "timer": "time.perf_counter"}
                    (out / f"{impl}-{scale}-{run - WARMUP}.json").write_text(
                        json.dumps(rec) + "\n")
            summary["scales"].setdefault(str(scale), {})[impl] = summarize(samples)
    for scale, row in summary["scales"].items():
        b = row["baseline"]["median_s"]
        o = row["optimized"]["median_s"]
        row["speedup_median"] = round(b / o, 3)
    speeds = [row["speedup_median"] for row in summary["scales"].values()]
    summary["speedup_median_across_scales"] = round(statistics.median(speeds), 3)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
