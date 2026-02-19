import time

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.relative_locator import RelativeBy
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains

from ..utils.logging_utils import get_logger
from ..utils.visual import assert_screenshot


class BasePage:
    """
    Базовый Page Object, использует find_element_in_frames для неявного поиска в iframe.
    """

    def __init__(self, driver, timeout: int = 10):
        self.driver = driver
        self.wait = WebDriverWait(driver.driver, timeout)
        self.logger = get_logger(self.__class__.__name__.lower())

    def _log(self, message: str, *args, level: str = "info") -> None:
        if self.logger:
            log_fn = getattr(self.logger, level, self.logger.info)
            log_fn(message, *args)

    def _find(
        self, by: str | RelativeBy = None, selector: str | None = None
    ) -> WebElement:
        def _locate(_):
            return self.driver.find_element_in_frames(by, selector)

        el = self.wait.until(_locate)
        if el is None:
            raise NoSuchElementException(
                f"Элемент {by}='{selector}' не найден в iframe"
            )
        return el
    
    def _wait_find(
        self, by: str | RelativeBy = None, selector: str | None = None, timeout: int = 10
    ) -> WebElement:
        def _locate(_):
            return self.driver.find_element_in_frames(by, selector)

        el = WebDriverWait(self.driver.driver, timeout).until(_locate)
        if el is None:
            raise NoSuchElementException(
                f"Элемент {by}='{selector}' не найден в iframe"
            )
        return el

    def _js_click(self, element: WebElement) -> None:
        # self.driver.driver.execute_script(
        #     "arguments[0].scrollIntoView({block:'center'});", element
        # )
        self.driver.driver.execute_script("arguments[0].click();", element)
        # element.click()
    def _click(self, element: WebElement) -> None:
        # self.driver.driver.execute_script(
        #     "arguments[0].scrollIntoView({block:'center'});", element
        # )
        self.driver.driver.execute_script("arguments[0].click();", element)
        # element.click()
    def _find_locator(self, locator: tuple[str, str]) -> WebElement:
        by, selector = locator
        return self._find(by, selector)
    def _wait_find_locator(self, locator: tuple[str, str], timeout:int = 10) -> WebElement:
        by, selector = locator
        return self._wait_find(by, selector, timeout)

    
    def _js_click_locator(self, locator: tuple[str, str]) -> WebElement:
        el = self._find_locator(locator)
        self._js_click(el)
        return el
    
    def _click_locator(self, locator: tuple[str, str]) -> WebElement:
        el = self._find_locator(locator)
        self._click(el)
        return el

    def _resolve_drag_element(
        self,
        locator: tuple[str, str] | None = None,
        point: tuple[int, int] | None = None,
        *,
        prefer_point: bool = True,
    ) -> WebElement | None:
        """
        Resolves drag source/target element using locator and optional viewport point.
        If point is provided and elementFromPoint succeeds, pointed element has priority.
        """
        anchor: WebElement | None = None
        if locator:
            try:
                anchor = self._find_locator(locator)
            except NoSuchElementException:
                anchor = None

        pointed: WebElement | None = None
        if point is not None:
            x, y = int(point[0]), int(point[1])
            pointed = self.driver.driver.execute_script(
                "return document.elementFromPoint(arguments[0], arguments[1]);",
                x,
                y,
            )

        if prefer_point:
            return pointed or anchor
        return anchor or pointed

    def _js_dispatch_drag_and_drop(
        self,
        source: WebElement,
        target: WebElement,
        source_point: tuple[int, int] | None = None,
        target_point: tuple[int, int] | None = None,
        step_delay_ms: int = 35,
    ) -> bool:
        sx = None if source_point is None else int(source_point[0])
        sy = None if source_point is None else int(source_point[1])
        tx = None if target_point is None else int(target_point[0])
        ty = None if target_point is None else int(target_point[1])
        delay_ms = int(step_delay_ms)
        return bool(
            self.driver.driver.execute_async_script(
                """
                const done = arguments[arguments.length - 1];
                const sourceBase = arguments[0];
                const targetBase = arguments[1];
                const sx = arguments[2];
                const sy = arguments[3];
                const tx = arguments[4];
                const ty = arguments[5];
                const delayMs = arguments[6];

                const pick = (fallback, x, y) => {
                  if (typeof x === 'number' && typeof y === 'number') {
                    const byPoint = document.elementFromPoint(x, y);
                    if (byPoint) return byPoint;
                  }
                  return fallback;
                };

                const source = pick(sourceBase, sx, sy);
                const target = pick(targetBase, tx, ty);
                if (!source || !target) {
                  done(false);
                  return;
                }

                try {
                  const dataTransfer = new DataTransfer();
                  const sequence = [
                    [source, 'dragstart', sx, sy],
                    [target, 'dragenter', tx, ty],
                    [target, 'dragover', tx, ty],
                    [target, 'drop', tx, ty],
                    [source, 'dragend', sx, sy],
                  ];

                  let index = 0;
                  const fireNext = () => {
                    const [node, type, x, y] = sequence[index];
                    const evt = new DragEvent(type, {
                      bubbles: true,
                      cancelable: true,
                      dataTransfer: dataTransfer,
                      clientX: typeof x === 'number' ? x : 0,
                      clientY: typeof y === 'number' ? y : 0,
                    });
                    node.dispatchEvent(evt);
                    index += 1;
                    if (index >= sequence.length) {
                      done(true);
                      return;
                    }
                    setTimeout(fireNext, delayMs);
                  };

                  fireNext();
                } catch (_err) {
                  done(false);
                }
                """,
                source,
                target,
                sx,
                sy,
                tx,
                ty,
                delay_ms,
            )
        )

    def drag_and_drop(
        self,
        source_locator: tuple[str, str] | None,
        target_locator: tuple[str, str] | None,
        *,
        source_point: tuple[int, int] | None = None,
        target_point: tuple[int, int] | None = None,
        step_delay_ms: int = 35,
        settle_delay_sec: float = 0.05,
    ) -> None:
        source_el = self._resolve_drag_element(
            source_locator,
            source_point,
            prefer_point=True,
        )
        target_el = self._resolve_drag_element(
            target_locator,
            target_point,
            prefer_point=True,
        )
        if source_el is None:
            raise NoSuchElementException(f"Drag source not found: {source_locator}")
        if target_el is None:
            raise NoSuchElementException(f"Drop target not found: {target_locator}")

        try:
            if self._js_dispatch_drag_and_drop(
                source_el,
                target_el,
                source_point,
                target_point,
                step_delay_ms=step_delay_ms,
            ):
                if settle_delay_sec > 0:
                    time.sleep(settle_delay_sec)
                return
        except Exception:
            pass

        # Selenium fallback for browsers/frameworks that ignore synthetic DragEvent.
        ActionChains(self.driver.driver).click_and_hold(source_el).move_to_element(
            target_el
        ).release(target_el).perform()
        if settle_delay_sec > 0:
            time.sleep(settle_delay_sec)

    # --- Visual regression helpers ---
    def screenshot(self, name: str, element: WebElement | None = None, **kwargs):
        """Снимает скрин и сравнивает с baseline (см. utils.visual.assert_screenshot)."""
        return assert_screenshot(
            self.driver.driver, name=name, element=element, logger=self.logger, **kwargs
        )

    def screenshot_locator(self, locator: tuple[str, str], name: str, **kwargs):
        el = self._find_locator(locator)
        return self.screenshot(name, element=el, **kwargs)
    

    # def _try_click_locator(self, locator: tuple[str, str], timeout: int = 3) -> bool:
    #     """
    #     Пытается кликнуть локатор за отведённое время.
    #     Возвращает True при успехе, False если элемент не появился/недоступен.
    #     Ошибки других типов пробрасываются.
    #     """
    #     by, selector = locator
    #     try:
    #         el = WebDriverWait(self.driver.driver, timeout).until(
    #             lambda d: self.driver.find_element_in_frames(by, selector)
    #         )
    #         if el is None:
    #             return False
    #         self._click(el)
    #         return True
    #     except TimeoutException:
    #         return False

    def _wait_locator(
        self,
        locator: tuple[str, str],
        timeout: int = 3,
        require_displayed: bool = True,
        require_enabled: bool = True,
    ) -> WebElement | None:
        """
        Ждёт появления локатора (учитывая iframe), опционально проверяет visible/enabled,
        затем кликает. Возвращает True при успехе, False при таймауте.
        """
        by, selector = locator

        def _ready(_):
            el = self.driver.find_element_in_frames(by, selector)
            if not el:
                return False
            if require_displayed and not el.is_displayed():
                return False
            if require_enabled and not el.is_enabled():
                return False
            return el

        try:
            el = WebDriverWait(self.driver.driver, timeout).until(_ready)
            return el
        except TimeoutException:
            return None
