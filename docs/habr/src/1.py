from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


DEBUGGER_ADDRESS = "127.0.0.1:9222"
CHROMEDRIVER_PATH = r"..\..\..\chromedriver-win64\chromedriver.exe"


def build_driver() -> webdriver.Chrome:
    options = Options()
    options.add_experimental_option("debuggerAddress", DEBUGGER_ADDRESS)
    service = Service(CHROMEDRIVER_PATH)
    return webdriver.Chrome(service=service, options=options)


def main() -> None:
    driver = build_driver()
    try:
        print("Connected to OnlyOffice")
        print("Title:", driver.title)
        print("URL:", driver.current_url)
        try:
            input("Screenshot: attached to OnlyOffice | Press Enter to close browser...")
        except EOFError:
            pass
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
