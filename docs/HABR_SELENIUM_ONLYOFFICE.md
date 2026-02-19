# Selenium + OnlyOffice: практический шаблон автотеста на Python

В этой статье собран рабочий шаблон запуска Selenium для OnlyOffice Desktop Editors.  
Формат такой: сначала кратко объясняем, зачем нужен блок кода, затем показываем сам блок.  
В конце даем полный скрипт целиком, который можно сразу запускать.

## Что понадобится

1. Windows и установленный OnlyOffice Desktop Editors.
2. Python 3.10+.
3. Selenium: `pip install selenium`.
4. Совместимый `chromedriver` для встроенного Chromium в вашей версии OnlyOffice.

Если версии Chromium и `chromedriver` не совпадают, вы получите `SessionNotCreatedException`.

## Шаг 1. Подготовка окружения

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install selenium
```

## Шаг 2. Запуск OnlyOffice с remote debugging

```powershell
& "C:\Program Files\ONLYOFFICE\DesktopEditors\DesktopEditors.exe" --remote-debugging-port=9222
```

Дальше Selenium будет подключаться к этому процессу по `127.0.0.1:9222`.

## Импортируем библиотеки

Нужны Selenium-классы, исключения и простой тайминг для polling-ожиданий.

```python
import os
import time
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
```

## Функция подключения к OnlyOffice

`build_driver()` не открывает новый Chrome, а подключается к уже открытому OnlyOffice через `debuggerAddress`.

```python
DEBUGGER_ADDRESS = "127.0.0.1:9222"


def build_driver() -> webdriver.Chrome:
    options = Options()
    options.add_experimental_option("debuggerAddress", DEBUGGER_ADDRESS)
    chromedriver_path = os.getenv("CHROMEDRIVER_PATH")
    service = Service(chromedriver_path) if chromedriver_path else Service()
    return webdriver.Chrome(service=service, options=options)
```

## Поиск и клик в любом iframe

OnlyOffice часто рендерит нужный UI внутри вложенных `iframe`.  
Поэтому делаем рекурсивный обход дерева фреймов.

```python
def _click_in_tree(driver: webdriver.Chrome, by: str, value: str) -> bool:
    try:
        element = driver.find_element(by, value)
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", element
        )
        element.click()
        return True
    except NoSuchElementException:
        pass

    frames = driver.find_elements(By.CSS_SELECTOR, "iframe, frame")
    for frame in frames:
        try:
            driver.switch_to.frame(frame)
        except StaleElementReferenceException:
            continue
        try:
            if _click_in_tree(driver, by, value):
                return True
        finally:
            driver.switch_to.parent_frame()
    return False
```

## Надежный клик с timeout

`click_in_any_frame(...)` добавляет polling-ожидание и на каждой попытке начинает поиск из `default_content()`.

```python
def click_in_any_frame(
    driver: webdriver.Chrome, by: str, value: str, timeout: float = 15
) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        driver.switch_to.default_content()
        if _click_in_tree(driver, by, value):
            driver.switch_to.default_content()
            return
        time.sleep(0.2)
    raise TimeoutException(f"Element not found for click: {by}={value}")
```

## Ввод текста в любом iframe

Логика такая же, как для клика: отдельный рекурсивный поиск и отдельная обертка с таймаутом.

```python
def _type_in_tree(driver: webdriver.Chrome, by: str, value: str, text: str) -> bool:
    try:
        element = driver.find_element(by, value)
        element.clear()
        element.send_keys(text)
        return True
    except NoSuchElementException:
        pass

    frames = driver.find_elements(By.CSS_SELECTOR, "iframe, frame")
    for frame in frames:
        try:
            driver.switch_to.frame(frame)
        except StaleElementReferenceException:
            continue
        try:
            if _type_in_tree(driver, by, value, text):
                return True
        finally:
            driver.switch_to.parent_frame()
    return False


def type_in_any_frame(
    driver: webdriver.Chrome, by: str, value: str, text: str, timeout: float = 15
) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        driver.switch_to.default_content()
        if _type_in_tree(driver, by, value, text):
            driver.switch_to.default_content()
            return
        time.sleep(0.2)
    raise TimeoutException(f"Element not found for input: {by}={value}")
```

## Работа с вкладками и окнами

В Selenium вкладка/окно переключаются одинаково, через `window_handles`.  
После действий вроде экспорта может появиться новый handle.

```python
def switch_to_new_window(driver: webdriver.Chrome, old_handles: set[str], timeout: int = 10) -> str:
    def _new_handle(d):
        current = set(d.window_handles)
        diff = current - old_handles
        return next(iter(diff), None)

    new_handle = WebDriverWait(driver, timeout).until(_new_handle)
    driver.switch_to.window(new_handle)
    driver.switch_to.default_content()
    return new_handle
```

## Точка входа сценария

`main()` соединяет все предыдущие функции в один тестовый поток.

```python
def main() -> None:
    driver = build_driver()
    try:
        print("Connected to OnlyOffice")
        print("Title:", driver.title)
        print("URL:", driver.current_url)

        click_in_any_frame(driver, By.CSS_SELECTOR, "[data-testid='main-sql-mode']")
        click_in_any_frame(
            driver, By.CSS_SELECTOR, "[data-testid='sql-manager-add-query-open']"
        )
        type_in_any_frame(
            driver,
            By.CSS_SELECTOR,
            "[data-testid='dialog-menu-name-sqlreq']",
            "demo_query",
        )
        click_in_any_frame(
            driver, By.CSS_SELECTOR, "[data-testid='sql-manager-add-query-confirm']"
        )
    finally:
        driver.quit()
```

## Полный код целиком

```python
import os
import time
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


DEBUGGER_ADDRESS = "127.0.0.1:9222"


def build_driver() -> webdriver.Chrome:
    options = Options()
    options.add_experimental_option("debuggerAddress", DEBUGGER_ADDRESS)

    chromedriver_path = os.getenv("CHROMEDRIVER_PATH")
    service = Service(chromedriver_path) if chromedriver_path else Service()
    return webdriver.Chrome(service=service, options=options)


def _click_in_tree(driver: webdriver.Chrome, by: str, value: str) -> bool:
    try:
        element = driver.find_element(by, value)
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", element
        )
        element.click()
        return True
    except NoSuchElementException:
        pass

    frames = driver.find_elements(By.CSS_SELECTOR, "iframe, frame")
    for frame in frames:
        try:
            driver.switch_to.frame(frame)
        except StaleElementReferenceException:
            continue

        try:
            if _click_in_tree(driver, by, value):
                return True
        finally:
            driver.switch_to.parent_frame()

    return False


def click_in_any_frame(
    driver: webdriver.Chrome, by: str, value: str, timeout: float = 15
) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        driver.switch_to.default_content()
        if _click_in_tree(driver, by, value):
            driver.switch_to.default_content()
            return
        time.sleep(0.2)
    raise TimeoutException(f"Element not found for click: {by}={value}")


def _type_in_tree(driver: webdriver.Chrome, by: str, value: str, text: str) -> bool:
    try:
        element = driver.find_element(by, value)
        element.clear()
        element.send_keys(text)
        return True
    except NoSuchElementException:
        pass

    frames = driver.find_elements(By.CSS_SELECTOR, "iframe, frame")
    for frame in frames:
        try:
            driver.switch_to.frame(frame)
        except StaleElementReferenceException:
            continue

        try:
            if _type_in_tree(driver, by, value, text):
                return True
        finally:
            driver.switch_to.parent_frame()

    return False


def type_in_any_frame(
    driver: webdriver.Chrome, by: str, value: str, text: str, timeout: float = 15
) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        driver.switch_to.default_content()
        if _type_in_tree(driver, by, value, text):
            driver.switch_to.default_content()
            return
        time.sleep(0.2)
    raise TimeoutException(f"Element not found for input: {by}={value}")


def switch_to_new_window(driver: webdriver.Chrome, old_handles: set[str], timeout: int = 10) -> str:
    def _new_handle(d):
        current = set(d.window_handles)
        diff = current - old_handles
        return next(iter(diff), None)

    new_handle = WebDriverWait(driver, timeout).until(_new_handle)
    driver.switch_to.window(new_handle)
    driver.switch_to.default_content()
    return new_handle


def main() -> None:
    driver = build_driver()
    try:
        print("Connected to OnlyOffice")
        print("Title:", driver.title)
        print("URL:", driver.current_url)

        click_in_any_frame(driver, By.CSS_SELECTOR, "[data-testid='main-sql-mode']")
        click_in_any_frame(
            driver, By.CSS_SELECTOR, "[data-testid='sql-manager-add-query-open']"
        )
        type_in_any_frame(
            driver,
            By.CSS_SELECTOR,
            "[data-testid='dialog-menu-name-sqlreq']",
            "demo_query",
        )
        click_in_any_frame(
            driver, By.CSS_SELECTOR, "[data-testid='sql-manager-add-query-confirm']"
        )

        # Пример переключения на новое окно:
        # before = set(driver.window_handles)
        # click_in_any_frame(driver, By.CSS_SELECTOR, "[data-testid='sql-manager-export-confirm']")
        # new_handle = switch_to_new_window(driver, before)
        # print("Switched to:", new_handle)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
```

## Запуск скрипта

```powershell
python .\run_onlyoffice_selenium.py
```

## Типовые проблемы

1. `SessionNotCreatedException` - не совпала версия `chromedriver`.
2. `cannot connect to chrome at 127.0.0.1:9222` - OnlyOffice запущен без флага remote debugging или порт занят.
3. `NoSuchElementException` - элемент в другом `iframe`, а поиск идет из неверного контекста.
4. `StaleElementReferenceException` - UI перерисован, нужен повторный поиск элемента.
