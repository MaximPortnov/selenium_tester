# Памятка для LLM-агента — R7 Plugin Tests (RU)

> Основная (английская) версия: `docs/AGENT_NOTES.md`.

## 1. Назначение
- End-to-end сценарии Selenium для плагина OnlyOffice (режимы SQL/OLAP/File и интерфейс SQL Manager).
- Агент должен уметь: подготовить окружение, запустить OnlyOffice с remote debugging, прогнать тесты, помогать расширять Page Object’ы.

## 2. Структура репозитория
- `test/driver.py` — подключение к запущенному Chrome/OnlyOffice через `debuggerAddress=127.0.0.1:9222`; ищет chromedriver в `chromedriver-win64/chromedriver.exe` или `CHROMEDRIVER_PATH`.
- `src/pages_slider_query/*.py` — Page Object слой для Slider Query (`home_page`, `editor_page`, `plugin_page`, `olap_mode_page`, `sql_mode_page`, `sql_manager_page`).
- `src/pages_r7_code/*.py` — Page Object слой для R7 Code.
  - `src/pages_r7_code/r7_code_page.py` содержит проверенные кликабельные локаторы кнопок (activity bar, toolbar, settings, dialogs).
- `src/pages_common/base_page.py` — общий `BasePage` для обоих плагинов.
- `test/slider_query/*` — replay-профиль и раннеры для Slider Query.
- `test/r7_code/*` — пакет тестов для сценариев R7 Code.
- `test_cases/slider_query/*` — JSONL replay-кейсы для пакетного прогона Slider Query.
- `test_cases/r7_code/*` — резерв под JSONL replay-кейсы для R7 Code.
- `test/slider_query/run_replay_simple.py` — лаунчер replay с проектным профилем роутов для `src.interaction_log_executor_simple`.
- `test/slider_query/run_all_test_cases.py` — пакетный прогон всех `test_cases/slider_query/*.jsonl` с раздельными логами по кейсам.
- `utils/replay_cases_report.py` + `scripts/replay_cases_report.bat` — красивый отчет по последнему batch в `artifacts/replay_cases`.
- `src/utils/timer.py` — таймер (`Timer.start()`, `mark()`, `step()`, `summary()`).
- `src/utils/logging_utils.py` — настройка логов (консоль + файл `artifacts/logs/run-<ts>.log`, env `LOG_LEVEL`/`LOG_DIR`).
- `src/utils/visual.py` — `assert_screenshot` (baseline/actual/diff в `artifacts/visual`, env `VISUAL_MODE=update`).
- `src/interaction_log_executor.py` — исполнитель JSONL-логов (`InteractionLogExecutor`) с обработчиками по `event/action` и хуками по `seq`.
- `connections_2026-01-22.json` — тестовые подключения; импортировать вручную в плагин.
- `scripts/` — настройка venv, chromedriver, запуск OnlyOffice, запуск тестов.
- `.vscode/launch.json` — отладка текущего файла в VS Code.

## 3. Подготовка окружения
1) Установите Python 3.12+ (Windows).  
2) `scripts/setup_env.bat` — создаёт `.venv`, обновляет pip, ставит зависимости из `requirements.txt`.  
3) `scripts/install_chromedriver.bat` — устанавливает chromedriver в `chromedriver-win64/` (совместим с `driver.py`):
   - без автоопределения;
   - версия по умолчанию: `109.0.5414.74`;
   - можно передать явную версию, например `scripts\install_chromedriver.bat 109.0.5414.74`.  
4) Убедитесь, что OnlyOffice Desktop Editors установлены. Если путь иной, установите переменную `ONLYOFFICE_PATH`.

Опционально: вынесите настройки в `.env` в корне репо (используют логирование/визуальные проверки):
```
LOG_LEVEL=INFO
LOG_DIR=artifacts/logs
LOG_ROOT=oo
VISUAL_MODE=update
VISUAL_DIR=artifacts/visual
```

## 4. Запуск OnlyOffice с remote debugging
- `scripts/start_onlyoffice.bat 9222` запускает DesktopEditors с флагом `--remote-debugging-port`.
- Проверьте, что порт 9222 свободен и процесс жив.

## 5. Импорт тестовых подключений
- В менеджере соединений плагина импортируйте `connections_2026-01-22.json`.  
- Файл предназначен только для ручного использования; реальные креды не коммитим.

## 6. Запуск тестов
Пример:
```bat
scripts\setup_env.bat
scripts\install_chromedriver.bat
scripts\start_onlyoffice.bat 9222
scripts\run_tests.bat .venv 9222
```
Если OnlyOffice уже запущен с нужным портом, запускать повторно не нужно.

Если Selenium падает с `SessionNotCreatedException` и несовпадением версий драйвера/браузера,
повторно выполните `scripts\install_chromedriver.bat <driver_version>` и перезапустите тесты.

Запуск replay без pytest:
```powershell
python -m src.interaction_log_executor --log .\interaction-log-1770560528478.jsonl
```
Полезные флаги:
- `--dry-parse` (только парсинг, без Selenium)
- `--no-prepare` (пропустить стандартные pre-step: открытие ячейки и панели плагина)

Запуск всех replay-кейсов из `test_cases/slider_query/` с логами в `artifacts/replay_cases/...`:
```powershell
python .\test\slider_query\run_all_test_cases.py
```

## 7. Правила для агента
- Не хранить пароли открыто; файл соединений закодирован, но не зашифрован.
- Локаторы держать в Page Object’ах, а не в тестах.
- Перед запуском убедиться, что версия chromedriver совпадает с встроенным Chromium/OnlyOffice.
- Удалять артефакты вида `plugin.plugin`; исходников плагина в репо нет.
- Жизненный цикл фич: каждую новую фичу сначала описывать в `features/*.md`; в `docs/*` переносить только после реализации и валидации.

## 8. Дальнейшие задачи
- При необходимости метрик используйте `Timer` из `src/utils/timer.py` для замеров вкладок/шагов (`start()` → `mark()/step()` → `summary()`).
- Закрыть TODO в `sql_manager_page.py` (верхняя левая панель, сценарии экспорта/импорта).
- Поддерживать отдельные файлы документации RU/EN.

## 9. Troubleshooting
- `src/interaction_log_executor.py` — исполнитель JSONL-логов в порядке строк файла с fail-fast политикой (первая ошибка останавливает прогон).
- Клавиатурные события (`keydown`, `keyup`, `keypress`) по умолчанию пропускаются.
- В v1 лог не обрезается по последней `seq`-сессии: выполняется весь файл по порядку.
- `SessionNotCreatedException`: почти всегда несовместимая версия chromedriver — переустановите через `install_chromedriver.bat`.
- Не находятся элементы: убедитесь, что активна нужная вкладка/iframe; используйте `find_element_in_frames`.
- Порт 9222 занят: завершите процесс или запустите на другом порту и передайте `debugger_address` в `DriverOnlyOffice`.



