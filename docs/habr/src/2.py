from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
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


def main() -> None:
    driver = build_driver()
    try:
        element = find_element_in_frames(driver, By.XPATH, CREATION_CELL_XPATH)
        if element is None:
            print("Element not found")
        else:
            print("Element found:", element.tag_name)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
