# R7 Plugin Test

Автотесты для плагина OnlyOffice Desktop Editors на базе Selenium.

Проект проверяет E2E-сценарии SQL/OLAP/File режимов и SQL Manager, используя подключение к уже запущенному OnlyOffice через remote debugging.

## Требования

- Windows.
- Python 3.12+.
- Установленный OnlyOffice Desktop Editors.
- Ручной импорт `connections_2026-01-22.json` в плагине перед SQL-сценариями.

## Быстрый старт

### CMD / PowerShell

```bat
scripts\setup_env.bat
scripts\install_chromedriver.bat
scripts\start_onlyoffice.bat
scripts\run_tests.bat .venv
scripts\replay_cases_report.bat
```

`run_tests` по умолчанию запускает `test/run_all_test_cases.py`.

## Повторный запуск

Для повторного прогона:

1. Если OnlyOffice не запущен, сначала выполните:

```bat
scripts\start_onlyoffice.bat
```

2. Затем повторяйте:

```bat
scripts\run_tests.bat .venv
scripts\replay_cases_report.bat
```

## Как делать `test_cases` и куда их класть

`test/run_all_test_cases.py` берёт только файлы `*.jsonl` из корневой папки `test_cases\` (не рекурсивно).

1. Подготовьте replay-лог в формате JSONL (`interaction-log-*.jsonl`):
2. Назовите файл понятным именем, например `sql_export_postgres.jsonl`.
3. Поместите файл в `.\test_cases\sql_export_postgres.jsonl`

```bat
.venv\Scripts\python.exe test\run_replay_simple.py --log test_cases\sql_export_postgres.jsonl
```

5. Запустите все кейсы пакетом:

```bat
scripts\run_tests.bat .venv
```

Артефакты прогона сохраняются в `artifacts\replay_cases\batch-<timestamp>\`.

## Основные директории

- `src/driver.py` - подключение Selenium к OnlyOffice.
- `src/pages/` - PageObjects и локаторы.
- `src/utils/` - таймер, логирование, визуальные проверки.
- `src/interaction_log_executor_simple.py` - упрощенный replay с роутингом по `testId`.
- `test/` - готовые тесты и примеры.
- `scripts/` - setup/run/start/install скрипты (`.bat`).
- `docs/` - документация и заметки для агентов.
