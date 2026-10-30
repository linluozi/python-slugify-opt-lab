# python-slugify-opt-lab

`python-slugify` turns arbitrary text into URL slugs. This repo benchmarks and patches one hotspot in its frozen legacy pipeline: `_transliterate()` called `import_module()` on **every** non-ASCII string, re-running the whole import machinery each time. The patch caches the resolved backend module, keyed by backend name and guarded by importer identity so mocked/importer-swapped calls still behave exactly as before.

Upstream: https://github.com/un33k/python-slugify

## Benchmark (5 timed runs, 3 warmups, seed 20261030)

| scale (calls) | baseline median | optimized median | speedup |
| --- | --- | --- | --- |
| 500 | 24.615 ms | 4.985 ms | **4.94x** |
| 2000 | 101.538 ms | 20.084 ms | **5.06x** |
| 8000 | 413.362 ms | 82.056 ms | **5.04x** |

Median speedup across scales: **5.04x**. Relative standard deviation is <1% at every scale (p25/p75 are within ~0.5% of the median), so no GC/cache noise note is needed. Raw samples: `benchmark/raw/<impl>-<scale>-<run>.json` (30 files).

## Differential test

`tests/test_diff.py` compares the patched pipeline against a byte-for-byte copy of the upstream `_legacy.py` (`tests/reference_legacy.py`). It runs 1226 default-pipeline inputs (random + empty, single char, extreme numbers, non-ASCII, NUL, 500-char input, entity edge cases) plus 300 inputs under 6 option sets, i.e. **3026 differential pairs, 0 mismatches**. Comparison is exact `==` on the return value (or exact exception type + message); no approximate matching.

Result: `1530 passed` for the differential file; full suite `1663 passed, 5 skipped, 136 subtests passed`.

## Gates (all commands run from repo root after `pip install pytest text-unidecode`)

| gate | result | reproduce |
| --- | --- | --- |
| G1 upstream tests green | 133 passed, 5 skipped, 0 failed (unchanged upstream suite) | `python -m pytest -q --ignore=tests/test_diff.py` |
| G2 differential identical | 3026 pairs, 0 mismatches | `python -m pytest -q tests/test_diff.py` |
| G3 median speedup ≥1.15x | 5.04x | `python benchmark/bench.py --out benchmark/raw` |
| G4 largest scale ≥0.95x | 5.04x at 8000 calls | same as G3 |
| G5 peak RSS ≤1.10x | 16708 KB vs 16668 KB = 1.002x | `python benchmark/rss.py optimized` vs `python benchmark/rss.py baseline` |

## Reproduce

```bash
python3 -m venv .venv && .venv/bin/pip install -q pytest text-unidecode
.venv/bin/python benchmark/bench.py --out benchmark/raw
.venv/bin/python -m pytest -q
```

## Environment

- CPU: AMD EPYC 7K62 48-Core Processor (4 vCPU), 3723 MB RAM
- Python 3.12.3, pytest 9.2.0, text-unidecode 1.3
- Seed 20261030, timer `time.perf_counter()`, 3 warmups + 5 timed runs per scale
