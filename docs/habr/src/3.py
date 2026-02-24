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


DEBUGGER_ADDRESS = "127.0.0.1:9222"
CHROMEDRIVER_PATH = r"..\..\..\chromedriver-win64\chromedriver.exe"
CREATION_CELL_XPATH = "//div[@class='document-creation-grid']/div[@data-id='cell']"


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


def main() -> None:
    driver = build_driver()
    try:
        click_in_any_frame(driver, By.XPATH, CREATION_CELL_XPATH)
        print("Clicked creation cell")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
