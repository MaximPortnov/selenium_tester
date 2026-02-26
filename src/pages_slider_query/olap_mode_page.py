from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.common.exceptions import TimeoutException

from ..pages_common.base_page import BasePage


class OlapModePage(BasePage):
    """
    Экран OLAP и элементы конструктора сводных отчетов.
    """

    OPEN_PIVOT_REPORTS_BUTTON = (
        By.CSS_SELECTOR,
        "[data-testid='olap-home-open-pivot-reports']",
    )
    PIVOT_CONNECTION_SELECT = (
        By.CSS_SELECTOR,
        "[data-testid='olap-pivot-connection-select']",
    )
    PIVOT_CUBE_SELECT = (
        By.CSS_SELECTOR,
        "[data-testid='olap-pivot-cube-select']",
    )
    PIVOT_TOOLBAR_CREATE_BUTTON = (
        By.CSS_SELECTOR,
        "[data-testid='olap-pivot-toolbar-create']",
    )
    PIVOT_HEADER = (
        By.CSS_SELECTOR,
        "[data-testid='olap-pivot-header']",
    )

    def click_open_pivot_reports(self) -> None:
        self._log("click_open_pivot_reports")
        self._click_locator(self.OPEN_PIVOT_REPORTS_BUTTON)

    def select_connection(self, visible_text: str) -> None:
        self._log("select_connection %s", visible_text)
        select_el = self._find_locator(self.PIVOT_CONNECTION_SELECT)
        Select(select_el).select_by_visible_text(visible_text)

    def select_cube(self, visible_text: str) -> None:
        self._log("select_cube %s", visible_text)
        select_el = self._wait_locator(self.PIVOT_CUBE_SELECT, timeout=30)
        if not select_el:
            raise RuntimeError("Pivot cube select is disabled or not ready")
        Select(select_el).select_by_visible_text(visible_text)

    def click_toolbar_create(self, timeout: int = 30) -> None:
        self._log("click_toolbar_create timeout=%s", timeout)
        btn = self._find_locator(self.PIVOT_TOOLBAR_CREATE_BUTTON)
        self._click(btn)

        def _is_disabled(_):
            current = self.driver.find_element_in_frames(*self.PIVOT_TOOLBAR_CREATE_BUTTON)
            if not current:
                return False
            disabled_attr = current.get_attribute("disabled")
            aria_disabled = str(current.get_attribute("aria-disabled") or "").lower()
            return (not current.is_enabled()) or (disabled_attr is not None) or (aria_disabled == "true")

        # После клика кнопка обычно блокируется на время загрузки.
        try:
            WebDriverWait(self.driver.driver, min(3, timeout)).until(_is_disabled)
        except TimeoutException:
            pass

        ready = self._wait_locator(self.PIVOT_TOOLBAR_CREATE_BUTTON, timeout=timeout)
        if not ready:
            raise TimeoutException("olap-pivot-toolbar-create did not re-enable after click")

    def click_header(self) -> None:
        self._log("click_pivot_header")
        self._click_locator(self.PIVOT_HEADER)

