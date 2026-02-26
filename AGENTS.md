# AGENTS GUIDE — R7 Plugin Test Project

Primary audience: LLM/automation agents that need to set up, run, or extend the Selenium E2E suite for the OnlyOffice plugin.

## Quick start
1) Read `docs/AGENT_NOTES.md` (EN) or `docs/AGENT_NOTES_RU.md` (RU) for environment + test run steps.
2) Execute scripts from project root (PowerShell or CMD):
   - `scripts/setup_env.bat` — create `.venv`, install deps.
   - `scripts/install_chromedriver.bat` — fetch matching chromedriver.
   - `scripts/start_onlyoffice.bat` — launch OnlyOffice with `--remote-debugging-port=9222`.
   - `scripts/run_tests.bat` — run `test/slider_query/run_all_test_cases.py`.
   - `scripts/replay_cases_report.bat` — pretty-print latest `artifacts/replay_cases` summary.
3) Import `connections_2026-01-22.json` into the plugin manually before SQL tests.

## Repo map (agent-relevant)
- Application code: `src/` (Slider Query pages `src/pages_slider_query/*`, shared base `src/pages_common/*`, R7 Code pages `src/pages_r7_code/*`, utils in `src/utils`, driver in `src/driver.py`).
- Tests/examples: `test/` (`test/slider_query/*`, `test/r7_code/*`).
- Config/data: `connections_2026-01-22.json`.
- Scripts: `scripts/` (venv, chromedriver, OnlyOffice, runner; `.bat` only).
- Agent docs: `docs/AGENT_NOTES.md` (EN), `docs/AGENT_NOTES_RU.md` (RU), `docs/agent/` (deep dives).

## Expectations & guardrails
- Keep locators inside PageObjects; avoid embedding XPaths in tests.
- Verify chromedriver version matches embedded Chromium in OnlyOffice; reinstall if mismatch.
- Do not store real credentials; the provided connections file is for manual import/testing only.
- Avoid recreating deleted artifacts (`plugin.plugin`, plugin source missing in repo).
- **Feature lifecycle:** describe every new feature proposal in `features/*.md` first; move finalized, implemented behavior into `docs/*` only after validation.
- **Documentation hygiene:** whenever flows, scripts, or locators change, immediately update `docs/AGENT_NOTES.md` (EN), `docs/AGENT_NOTES_RU.md` (RU), and any relevant files under `docs/agent/` so instructions stay current.

## Deeper references
- Workflows & checklists: `docs/agent/workflow.md`
- Troubleshooting matrix: `docs/agent/troubleshooting.md`

## Extending
- Implement TODOs in `src/pages_slider_query/sql_manager_page.py` and add timings in `src/utils/timer.py`.
- Maintain dual-language docs (EN primary, RU secondary with `_RU` suffix).


