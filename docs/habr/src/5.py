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
CHROMEDRIVER_PATH = r"..\..\..\chromedriver-win64\chromedriver.exe"
CREATION_CELL_XPATH = "//div[@class='document-creation-grid']/div[@data-id='cell']"
PLUGINS_TAB_XPATH = "//ul[@role='tablist']/li[@data-layout-name='toolbar-plugins']/a"
PLUGIN_BUTTON_XPATH = (
    "//section[@id='plugins-panel']/div/span/button"
    "[descendant::*[text()='Слайдер'] and descendant::*[text()='Данные']]"
)
STARTUP_CLOSE_XPATH = "//div[@class='tool close']"


def build_driver() -> webdriver.Chrome:
    options = Options()
    options.add_experimental_option("debuggerAddress", DEBUGGER_ADDRESS)
    service = Service(CHROMEDRIVER_PATH)
    return webdriver.Chrome(service=service, options=options)


def find_element_in_frames(driver: webdriver.Chrome, by: str, value: str):
    driver.switch_to.default_content()

    def rec():
        try:
            return driver.find_element(by, value)
        except NoSuchElementException:
            pass

        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            try:
                driver.switch_to.frame(iframe)
                found = rec()
                if found:
                    return found
                driver.switch_to.parent_frame()
            except StaleElementReferenceException:
                driver.switch_to.parent_frame()
            except Exception:
                driver.switch_to.parent_frame()
        return None

    return rec()


def click_in_any_frame(
    driver: webdriver.Chrome, by: str, value: str, timeout: float = 15
) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        element = find_element_in_frames(driver, by, value)
        if element is not None:
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", element
            )
            driver.execute_script("arguments[0].click();", element)
            driver.switch_to.default_content()
            return
        time.sleep(0.2)
    raise TimeoutException(f"Element not found for click: {by}={value}")


def _try_switch_to_new_window(
    driver: webdriver.Chrome, old_handles: set[str], timeout: int = 8
) -> bool:
    try:
        new_handle = WebDriverWait(driver, timeout).until(
            lambda d: next(iter(set(d.window_handles) - old_handles), None)
        )
    except TimeoutException:
        return False
    driver.switch_to.window(new_handle)
    driver.switch_to.default_content()
    return True


def open_spreadsheet_editor(driver: webdriver.Chrome) -> None:
    before = set(driver.window_handles)
    try:
        click_in_any_frame(driver, By.XPATH, CREATION_CELL_XPATH, timeout=2)
    except TimeoutException:
        return
    _try_switch_to_new_window(driver, before, timeout=8)


def open_plugin_panel(driver: webdriver.Chrome) -> None:
    click_in_any_frame(driver, By.XPATH, PLUGINS_TAB_XPATH, timeout=2)
    click_in_any_frame(driver, By.XPATH, PLUGIN_BUTTON_XPATH, timeout=8)
    try:
        click_in_any_frame(driver, By.XPATH, STARTUP_CLOSE_XPATH, timeout=1)
    except TimeoutException:
        pass
    driver.switch_to.default_content()


def prepare_plugin_home(driver: webdriver.Chrome) -> None:
    open_spreadsheet_editor(driver)

    try:
        open_plugin_panel(driver)
    except TimeoutException:
        click_in_any_frame(driver, By.XPATH, PLUGINS_TAB_XPATH, timeout=2)
        open_plugin_panel(driver)


def main() -> None:
    driver = build_driver()
    try:
        prepare_plugin_home(driver)
        print("Plugin panel is opened")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
