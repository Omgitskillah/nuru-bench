"""These tests run inside a Nuru checkout, with this repo at nuru/evals: from Nuru's root,
`uv run pytest nuru/evals/tests`. Nuru's own test setup (nuru/tests/conftest.py: no real models,
sandbox or expert key, UTF-8 files, decision logs in tmp) applies to them too, and its helper
modules (plugin_test_vault) import as they do there."""
import importlib.util
import sys
from pathlib import Path

NURU_TESTS = Path(__file__).resolve().parents[2] / "tests"
if not (NURU_TESTS / "conftest.py").is_file():
    raise RuntimeError(f"run these from a Nuru checkout with this repo at nuru/evals (no {NURU_TESTS})")
sys.path.insert(0, str(NURU_TESTS))
_spec = importlib.util.spec_from_file_location("nuru_tests_conftest", NURU_TESTS / "conftest.py")
_nuru = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_nuru)
globals().update({name: value for name, value in vars(_nuru).items() if not name.startswith("__")})
