#!/usr/bin/env python3
"""Peak-RSS driver: run one implementation over 8000 fixed inputs, then read VmHWM."""
import importlib.util
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
impl = sys.argv[1] if len(sys.argv) > 1 else "optimized"
if impl == "baseline":
    spec = importlib.util.spec_from_file_location("reference_legacy", ROOT / "tests" / "reference_legacy.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fn = mod.slugify
else:
    from slugify import slugify as fn

rng = random.Random(20261030)
words = ["Hello", "Café", "影師嗎", "foo bar", "2024"]
for _ in range(8000):
    fn(" ".join(rng.choices(words, k=3)))
print("peak_rss_kb", next(l.split()[1] for l in open("/proc/self/status") if l.startswith("VmHWM")))
