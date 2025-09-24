# Repository Guidelines

  ## Project Structure & Module Organization
  The application code lives under `hot_list_aggregation/`, organized by feature modules so shared helpers stay in
  `hot_list_aggregation/common/`. Configuration defaults belong in `config/`, while example datasets or fixtures
  go in `data/`. Keep new tests in `tests/` and mirror the package layout (`tests/common/test_utils.py` for
  `hot_list_aggregation/common/utils.py`) to make test discovery automatic.

  ## Build, Test, and Development Commands
  Run `python -m venv .venv` followed by `.venv\Scripts\activate` to create and enter the local environment. Install
  dependencies with `pip install -r requirements.txt`; update the file whenever pinned versions change. Execute `pytest`
  from the repo root for the full suite, or `pytest tests/service/test_hot_lists.py -k smoke` to target a subset. Use
  `python -m hot_list_aggregation.cli --help` to inspect the supported aggregation jobs during development.

  ## Coding Style & Naming Conventions
  Use 4-space indentation, type hints on public functions, and prefer f-strings for formatting. Classes follow
  PascalCase, modules stay lowercase_with_underscores, and constants use ALL_CAPS. Format code with `black .` and lint
  with `ruff check .`; both must pass before opening a pull request. Keep functions under 40 lines and extract reusable
  logic into `common/` utilities.

  ## Testing Guidelines
  Write tests with `pytest`; fixture utilities belong in `tests/conftest.py`. Name test files `test_<module>.py`
  and individual tests `test_<behavior>_when_<condition>`. Aim for ≥90% statement coverage on `hot_list_aggregation/
  ` modules; generate reports via `pytest --cov=hot_list_aggregation --cov-report=term-missing`. Tag long-running
  scenarios with `@pytest.mark.slow` so they can be skipped locally with `-m "not slow"`.

  ## Commit & Pull Request Guidelines
  Use Conventional Commit prefixes (`feat:`, `fix:`, `docs:`, etc.) with a concise, imperative summary under 72
  characters. Reference tracking issues in the body (`Refs #123`) and call out any migrations or breaking changes. Pull
  requests need: a checklist of manual/verifier tests, a short “Why” section describing the problem, screenshots or log
  excerpts for user-facing changes, and confirmation that linting and tests ran clean.

  ## Security & Configuration Tips
  Never commit personal API keys; add new secrets to `.env.example` with safe placeholders. Review default scheduler
  intervals in `config/schedules.yaml` to avoid overfetching third-party feeds. When adding dependencies, prefer
  maintained libraries and document any that require system-level packages in `docs/setup.md`.

  Let me know if you want me to tailor any sections further or adjust the tone/word count.