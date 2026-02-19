# R7 Plugin Test

Автотесты для плагина OnlyOffice Desktop Editors на базе Selenium.

Проект проверяет E2E-сценарии SQL/OLAP/File режимов и SQL Manager, используя подключение к уже запущенному OnlyOffice через remote debugging.

## Требования

- Windows.
- Python 3.12+.
- Установленный OnlyOffice Desktop Editors.
- ChromeDriver, совместимый со встроенным Chromium в OnlyOffice.
- Ручной импорт `connections_2026-01-22.json` в плагине перед SQL-сценариями.

## Быстрый старт

### CMD / PowerShell

```bat
scripts\setup_env.bat
scripts\install_chromedriver.bat
scripts\start_onlyoffice.bat 9222
scripts\run_tests.bat .venv 9222
```

`run_tests` по умолчанию запускает `test/run_all_test_cases.py`.

## Запуск тестов через скрипты

Рекомендуемый порядок:

```bat
scripts\setup_env.bat
scripts\install_chromedriver.bat
scripts\run_tests.bat .venv 9222 start
```

`install_chromedriver.bat`:
- ставит ChromeDriver по прямой ссылке на заданную версию;
- по умолчанию ставит `109.0.5414.74`;
- при необходимости передайте конкретную версию вручную:

```bat
scripts\install_chromedriver.bat 109.0.5414.74
```

Формат аргументов:

```bat
scripts\install_chromedriver.bat [version] [destination]
```

Примеры:

```bat
scripts\install_chromedriver.bat
scripts\install_chromedriver.bat 109.0.5414.74
scripts\install_chromedriver.bat 109.0.5414.74 .\chromedriver-win64
```

Если в логе есть ошибка `SessionNotCreatedException` с текстом `only supports Chrome version X` и `Current browser version is Y`, поставьте версию драйвера из ветки `Y` и повторите прогон.

- `scripts\run_tests.bat .venv 9222 start`:
  - использует `.\.venv\Scripts\python.exe`;
  - при `start` сам запускает OnlyOffice на порту `9222`;
  - запускает batch replay всех кейсов из `test_cases\`.
- если OnlyOffice уже запущен с `--remote-debugging-port=9222`, используйте:

```bat
scripts\run_tests.bat .venv 9222
```

Отчёт по последнему batch:

```bat
scripts\replay_cases_report.bat
```

Отчёт по конкретному batch:

```bat
scripts\replay_cases_report.bat artifacts\replay_cases\batch-YYYYMMDD-HHMMSS
```

## Основные директории

- `src/driver.py` - подключение Selenium к OnlyOffice.
- `src/pages/` - PageObjects и локаторы.
- `src/utils/` - таймер, логирование, визуальные проверки.
- `src/interaction_log_executor_simple.py` - упрощенный replay с роутингом по `testId`.
- `test/` - готовые тесты и примеры.
- `scripts/` - setup/run/start/install скрипты (`.bat`).
- `docs/` - документация и заметки для агентов.

## Как делать `test_cases` и куда их класть

`test/run_all_test_cases.py` берёт только файлы `*.jsonl` из корневой папки `test_cases\` (не рекурсивно).

1. Подготовьте replay-лог в формате JSONL (`interaction-log-*.jsonl`):
   - одна строка = один JSON-объект события;
   - рабочие примеры уже лежат в `test_cases\`.
2. Назовите файл понятным именем, например `sql_export_postgres.jsonl`.
3. Поместите файл в:
   - `.\test_cases\sql_export_postgres.jsonl`
4. Проверьте кейс отдельно:

```bat
.venv\Scripts\python.exe test\run_replay_simple.py --log test_cases\sql_export_postgres.jsonl --debugger-address 127.0.0.1:9222
```

5. Запустите все кейсы пакетом:

```bat
scripts\run_tests.bat .venv 9222
```

Артефакты прогона сохраняются в `artifacts\replay_cases\batch-<timestamp>\`.

## Проверка перед запуском

Проверить версию браузера OnlyOffice на debug-порту:

```powershell
(Invoke-RestMethod -Uri "http://127.0.0.1:9222/json/version").Browser
```

Проверить установленный ChromeDriver:

```bat
chromedriver-win64\chromedriver.exe --version
```

Быстрая проверка подключения Selenium к запущенному OnlyOffice:

```bat
.venv\Scripts\python.exe -c "from src.driver import DriverOnlyOffice; d=DriverOnlyOffice(debugger_address='127.0.0.1:9222'); print(d.driver.capabilities.get('browserVersion')); d.driver.quit()"
```

## Дополнительные запуски

```powershell
# pytest-сценарий полного прогона
.venv\Scripts\python.exe -m pytest test\test_full_flow.py

# replay последнего interaction-log
.venv\Scripts\python.exe -m src.interaction_log_executor

# replay конкретного лога (simple executor)
.venv\Scripts\python.exe -m src.interaction_log_executor_simple --log .\interaction-log-1771316073587.jsonl

# красивый отчет по последнему batch в artifacts/replay_cases
scripts\replay_cases_report.bat
```

## Полезные документы

- `docs/AGENT_NOTES.md` - английская памятка.
- `docs/AGENT_NOTES_RU.md` - русская памятка.
- `docs/HABR_SELENIUM_ONLYOFFICE.md` - статья-быстрый старт в формате Habr.

## Ограничения и правила

- Не хранить реальные креды в репозитории.
- Локаторы держать в PageObjects, не в тестах.
- При несовместимости версий переустанавливать `chromedriver`.
