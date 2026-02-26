# LLM Agent Playbook — R7 Plugin Tests (EN)

> Russian version: see `docs/AGENT_NOTES_RU.md`.

## 1. Purpose
- End-to-end Selenium scenarios for the OnlyOffice plugin (SQL/OLAP/File modes and SQL Manager UI).
- The agent must: prepare the environment, launch OnlyOffice with remote debugging, run tests, and help extend Page Objects.

## 2. Repository map
- `test/driver.py` — attaches to running Chrome/OnlyOffice via `debuggerAddress=127.0.0.1:9222`; finds chromedriver in `chromedriver-win64/chromedriver.exe` or `CHROMEDRIVER_PATH`.
- `src/pages_slider_query/*.py` — Page Objects for Slider Query (`home_page`, `editor_page`, `plugin_page`, `olap_mode_page`, `sql_mode_page`, `sql_manager_page`).
- `src/pages_r7_code/*.py` — Page Objects for R7 Code.
  - `src/pages_r7_code/r7_code_page.py` includes verified clickable button locators (activity bars, toolbar, settings, dialogs).
- `src/pages_common/base_page.py` — shared `BasePage` for both plugins.
- `test/slider_query/*` — Slider Query replay profile and runners.
- `test/r7_code/*` — R7 Code test package (new scenarios go here).
- `test_cases/slider_query/*` — JSONL replay cases for Slider Query batch runner.
- `test_cases/r7_code/*` — reserved JSONL replay cases for R7 Code.
- `test/slider_query/run_replay_simple.py` — replay launcher with project routes profile for `src.interaction_log_executor_simple`.
- `test/slider_query/run_all_test_cases.py` — batch runner for all `test_cases/slider_query/*.jsonl` with isolated logs per case.
- `utils/replay_cases_report.py` + `scripts/replay_cases_report.bat` — pretty report for latest `artifacts/replay_cases` batch summary.
- `src/utils/timer.py` — timing helper (`Timer.start()`, `mark()`, `step()`, `summary()`).
- `src/utils/logging_utils.py` — logger setup (console + file `artifacts/logs/run-<ts>.log`, env `LOG_LEVEL`/`LOG_DIR`).
- `src/utils/visual.py` — `assert_screenshot` (visual baseline/actual/diff under `artifacts/visual`, env `VISUAL_MODE=update`).
- `src/interaction_log_executor.py` — JSONL action replay helper (`InteractionLogExecutor`) with per-action handlers and seq hooks.
- `connections_2026-01-22.json` — test connections; import manually in the plugin.
- `scripts/` — setup venv, chromedriver, OnlyOffice, test runner (see below).
- `.vscode/launch.json` — VS Code debug current file.

## 3. Environment setup
1) Install Python 3.12+ (Windows).  
2) `scripts/setup_env.bat` — create `.venv`, upgrade pip, install `requirements.txt`.  
3) `scripts/install_chromedriver.bat` — install chromedriver to `chromedriver-win64/` (compatible with `driver.py`):
   - no auto-detection;
   - default version is `109.0.5414.74`;
   - explicit version is supported, e.g. `scripts\install_chromedriver.bat 109.0.5414.74`.  
4) Ensure OnlyOffice Desktop Editors are installed. If the path differs, set `ONLYOFFICE_PATH`.

Optional: put settings in `.env` at repo root (used by logging/visual):
```
LOG_LEVEL=INFO
LOG_DIR=artifacts/logs
LOG_ROOT=oo
VISUAL_MODE=update
VISUAL_DIR=artifacts/visual
```

## 4. Launch OnlyOffice with remote debugging
- `scripts/start_onlyoffice.bat 9222` starts DesktopEditors with `--remote-debugging-port`.
- Verify port 9222 is free and the process stays alive.

## 5. Import test connections
- In the plugin’s connection manager, import `connections_2026-01-22.json`.  
- For manual use only; do not commit real credentials.

## 6. Run tests
Example:
```bat
scripts\setup_env.bat
scripts\install_chromedriver.bat           # first time or version change
scripts\start_onlyoffice.bat 9222          # keep it running
scripts\run_tests.bat .venv 9222           # runs test/slider_query/run_all_test_cases.py via .venv
```
If OnlyOffice is already running on the port, skip step 3.

If Selenium reports `SessionNotCreatedException` with driver/browser version mismatch,
rerun `scripts\install_chromedriver.bat <driver_version>` and retry tests.

Run interaction replay without pytest:
```powershell
python -m src.interaction_log_executor --log .\interaction-log-1770560528478.jsonl
```
Useful flags:
- `--dry-parse` (parse only, no Selenium)
- `--no-prepare` (skip default pre-steps: open cell + plugin panel)

Run all replay cases from `test_cases/slider_query/` and collect logs in `artifacts/replay_cases/...`:
```powershell
python .\test\slider_query\run_all_test_cases.py
```

## 7. Guardrails for LLM
- Do not store plain credentials; `connections_2026-01-22.json` is encoded, not encrypted.
- Keep locators inside Page Objects, not in tests.
- Ensure chromedriver version matches the embedded Chromium/OnlyOffice before running tests.
- Remove artifacts like `plugin.plugin`; plugin source is not in this repo.
- Feature lifecycle: for each new feature, create/update a spec in `features/*.md` first; after implementation + validation, transfer stable instructions into `docs/*`.

## 8. Next steps
- Use `Timer` from `src/utils/timer.py` to log load times for tabs/actions (`start()` → `mark()/step()` → `summary()`).
- Finish TODOs in `sql_manager_page.py` (upper-left panel, extra export/import flows).
- Maintain RU/EN docs in separate files.

## 9. Troubleshooting
- `src/interaction_log_executor.py` replays JSONL action logs in file order using fail-fast behavior (first error stops replay).
- Keyboard events (`keydown`, `keyup`, `keypress`) are skipped by default.
- v1 does not cut log by latest `seq` session; full file order is replayed.
- `SessionNotCreatedException`: usually chromedriver version mismatch — reinstall via `install_chromedriver.bat`.
- Elements not found: check correct tab/iframe; use `find_element_in_frames` from `driver.py`.
- Port 9222 busy: kill conflicting process or run OnlyOffice on another port and pass `debugger_address` to `DriverOnlyOffice`.



