"""Differential test: patched legacy pipeline must equal the frozen upstream byte-for-byte."""
import importlib.util
import random
from pathlib import Path

import pytest

from slugify import slugify

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("reference_legacy", ROOT / "tests" / "reference_legacy.py")
ref = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ref)


def call(fn, *args, **kwargs):
    try:
        return ("ok", fn(*args, **kwargs))
    except Exception as exc:  # compare failure contracts too
        return ("err", type(exc).__name__, str(exc))


def cases():
    rng = random.Random(20261030)
    alphabet = list("abcXYZ019 _-.,'&;#/%\t\n") + list("éüßñÇÄ影師Компβºª—") + ["\u0301", "\x00", "😀"]
    out = ["", " ", "-", "---", "a", "A", "a b", "  a  b  ", "&amp;", "&#65;", "&#x41;",
           "&#x110000;", "&#999999999999999999999;", "a'b", "a---b", "a_-_b", "1,234", "12,34",
           "Café", "影師嗎", "Компьютер", "ß", "İ", "x" * 500, "\x00a\x00", "a" * 50 + " " + "b" * 50]
    for _ in range(1200):
        n = rng.randint(0, 60)
        out.append("".join(rng.choices(alphabet, k=n)))
    return out


@pytest.mark.parametrize("text", cases())
def test_default_pipeline_matches(text):
    assert call(slugify, text) == call(ref.slugify, text)


@pytest.mark.parametrize("text", cases()[:300])
def test_options_match(text):
    for kwargs in (
        {"max_length": 10},
        {"max_length": 12, "word_boundary": True, "save_order": True},
        {"separator": "::", "max_length": 20},
        {"allow_unicode": True},
        {"lowercase": False},
        {"replacements": [("a", "4")], "replacement_stage": "pre"},
    ):
        assert call(slugify, text, **kwargs) == call(ref.slugify, text, **kwargs), (text, kwargs)


@pytest.mark.parametrize("bad", [None, 123, 1.5, object()])
def test_type_errors_match(bad):
    assert call(slugify, bad) == call(ref.slugify, bad)
