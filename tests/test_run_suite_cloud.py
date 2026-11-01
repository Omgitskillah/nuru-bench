"""run_suite refuses a Claude batch without --allow-cloud, whether the model is chosen in the
environment or only in .env.nuru."""
import pytest


@pytest.fixture
def run_suite(monkeypatch):
    import importlib
    from pathlib import Path

    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "decision_layer"))
    return importlib.import_module("run_suite")


def test_a_claude_model_chosen_only_in_env_nuru_needs_allow_cloud(run_suite, monkeypatch, tmp_path):
    env_file = tmp_path / ".env.nuru"
    env_file.write_text("NURU_MAIN_MODEL=anthropic:claude-haiku-5-5\n")
    monkeypatch.setattr(run_suite, "ENV_NURU", env_file)
    monkeypatch.delenv("NURU_MAIN_MODEL", raising=False)
    with pytest.raises(SystemExit, match="--allow-cloud"):
        run_suite.require_cloud_opt_in(False)
    run_suite.require_cloud_opt_in(True)
    monkeypatch.setenv("NURU_MAIN_MODEL", "ollama")  # the environment overrides the file, as in Session
    run_suite.require_cloud_opt_in(False)


def test_main_refuses_a_claude_batch_from_env_nuru_before_any_setup(run_suite, monkeypatch, tmp_path):
    env_file = tmp_path / ".env.nuru"
    env_file.write_text("NURU_MAIN_MODEL=anthropic:claude-sonnet-5-5\n")
    monkeypatch.setattr(run_suite, "ENV_NURU", env_file)
    monkeypatch.delenv("NURU_MAIN_MODEL", raising=False)
    monkeypatch.setattr(run_suite, "suite_prompts", lambda: pytest.fail("the batch must not be set up"))
    monkeypatch.setattr("sys.argv", ["run_suite", "--tests", "3"])
    with pytest.raises(SystemExit, match="--allow-cloud"):
        run_suite.main()
