from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from ..pages_common.base_page import BasePage


class R7CodePage(BasePage):
    """Page object for R7 Code plugin buttons and main editor."""

    APP_WORKBENCH = (By.CSS_SELECTOR, "[data-testid='app-workbench']")

    PLUGIN_OPEN_BUTTON_BY_TEXT = (
        By.XPATH,
        "//button[.//span[contains(@class,'caption') and normalize-space()='{r7}.code']]",
    )

    MAIN_EDITOR_ROOT = (By.CSS_SELECTOR, "#editor")
    MAIN_EDITOR_MONACO = (By.CSS_SELECTOR, "#editor .monaco-editor")
    MAIN_EDITOR_TEXTAREA = (By.CSS_SELECTOR, "#editor textarea.inputarea")

    # Verified clickable buttons from temp/r7_code.html (<button> + no disabled attr).
    ACTIVITY_LEFT_TOGGLE_SIDEBAR_BUTTON = (
        By.CSS_SELECTOR,
        "[data-testid='activity-left-toggle-sidebar-btn']",
    )
    ACTIVITY_LEFT_VIEW_MACROS_BUTTON = (
        By.CSS_SELECTOR,
        "[data-testid='activity-left-view-macros-btn']",
    )
    ACTIVITY_LEFT_VIEW_WORK_MACROS_BUTTON = (
        By.CSS_SELECTOR,
        "[data-testid='activity-left-view-work-macros-btn']",
    )
    ACTIVITY_LEFT_VIEW_SEARCH_BUTTON = (
        By.CSS_SELECTOR,
        "[data-testid='activity-left-view-search-btn']",
    )
    ACTIVITY_LEFT_VIEW_EXAMPLES_BUTTON = (
        By.CSS_SELECTOR,
        "[data-testid='activity-left-view-examples-btn']",
    )
    ACTIVITY_LEFT_VIEW_EXTERNAL_SCRIPTS_BUTTON = (
        By.CSS_SELECTOR,
        "[data-testid='activity-left-view-external-scripts-btn']",
    )
    ACTIVITY_LEFT_SETTINGS_BUTTON = (
        By.CSS_SELECTOR,
        "[data-testid='activity-left-settings-btn']",
    )

    ACTIVITY_RIGHT_TOGGLE_PANE_BUTTON = (
        By.CSS_SELECTOR,
        "[data-testid='activity-right-toggle-pane-btn']",
    )
    ACTIVITY_RIGHT_AI_CONNECTION_BUTTON = (
        By.CSS_SELECTOR,
        "[data-testid='activity-right-pane-ai-connection-btn']",
    )
    ACTIVITY_RIGHT_CHAT_BUTTON = (
        By.CSS_SELECTOR,
        "[data-testid='activity-right-pane-chat-btn']",
    )
    ACTIVITY_RIGHT_DEBUG_INSIGHTS_BUTTON = (
        By.CSS_SELECTOR,
        "[data-testid='activity-right-pane-debug-insights-btn']",
    )

    TOOLBAR_NEW_MACRO_BUTTON = (
        By.CSS_SELECTOR,
        "[data-testid='toolbar-editor-new-macro-btn']",
    )
    TOOLBAR_PASTE_BUTTON = (By.CSS_SELECTOR, "[data-testid='toolbar-editor-paste-btn']")
    TOOLBAR_RUN_BUTTON = (By.CSS_SELECTOR, "[data-testid='toolbar-run-btn']")
    TOOLBAR_SAVE_BUTTON = (By.CSS_SELECTOR, "[data-testid='toolbar-save-btn']")
    TOOLBAR_DEBUG_BUTTON = (By.CSS_SELECTOR, "[data-testid='toolbar-debug-btn']")
    TOOLBAR_COPY_BUTTON = (By.CSS_SELECTOR, "[data-testid='toolbar-copy-btn']")
    TOOLBAR_RENAME_BUTTON = (By.CSS_SELECTOR, "[data-testid='toolbar-rename-btn']")
    TOOLBAR_DELETE_BUTTON = (By.CSS_SELECTOR, "[data-testid='toolbar-delete-btn']")
    TOOLBAR_MAXIMIZE_BUTTON = (By.CSS_SELECTOR, "[data-testid='toolbar-maximize-btn']")
    TOOLBAR_MINIMIZE_BUTTON = (By.CSS_SELECTOR, "[data-testid='toolbar-minimize-btn']")

    CONSOLE_SAVE_BUTTON = (By.CSS_SELECTOR, "[data-testid='console-save-btn']")
    CONSOLE_CLEAR_BUTTON = (By.CSS_SELECTOR, "[data-testid='console-clear-btn']")

    SETTINGS_TAB_EDITOR_BUTTON = (
        By.CSS_SELECTOR,
        "[data-testid='settings-tab-editor-btn']",
    )
    SETTINGS_TAB_MODULES_BUTTON = (
        By.CSS_SELECTOR,
        "[data-testid='settings-tab-modules-btn']",
    )
    SETTINGS_TAB_DEBUG_BUTTON = (By.CSS_SELECTOR, "[data-testid='settings-tab-debug-btn']")
    SETTINGS_TAB_DEV_TOOLS_BUTTON = (
        By.CSS_SELECTOR,
        "[data-testid='settings-tab-dev-tools-btn']",
    )
    SETTINGS_RESET_BUTTON = (By.CSS_SELECTOR, "[data-testid='settings-reset-btn']")
    SETTINGS_CANCEL_BUTTON = (By.CSS_SELECTOR, "[data-testid='settings-cancel-btn']")
    SETTINGS_SAVE_BUTTON = (By.CSS_SELECTOR, "[data-testid='settings-save-btn']")

    VBA_CONVERSION_ACCEPT_BUTTON = (
        By.CSS_SELECTOR,
        "[data-testid='vba-conversion-dialog-accept-btn']",
    )
    VBA_CONVERSION_EDIT_BUTTON = (
        By.CSS_SELECTOR,
        "[data-testid='vba-conversion-dialog-edit-btn']",
    )
    VBA_CONVERSION_CANCEL_BUTTON = (
        By.CSS_SELECTOR,
        "[data-testid='vba-conversion-dialog-cancel-btn']",
    )

    WELCOME_OK_BUTTON = (By.CSS_SELECTOR, "[data-testid='welcome-popup-ok-btn']")

    BUTTON_LOCATORS = {
        "activity_left_toggle_sidebar": ACTIVITY_LEFT_TOGGLE_SIDEBAR_BUTTON,
        "activity_left_view_macros": ACTIVITY_LEFT_VIEW_MACROS_BUTTON,
        "activity_left_view_work_macros": ACTIVITY_LEFT_VIEW_WORK_MACROS_BUTTON,
        "activity_left_view_search": ACTIVITY_LEFT_VIEW_SEARCH_BUTTON,
        "activity_left_view_examples": ACTIVITY_LEFT_VIEW_EXAMPLES_BUTTON,
        "activity_left_view_external_scripts": ACTIVITY_LEFT_VIEW_EXTERNAL_SCRIPTS_BUTTON,
        "activity_left_settings": ACTIVITY_LEFT_SETTINGS_BUTTON,
        "activity_right_toggle_pane": ACTIVITY_RIGHT_TOGGLE_PANE_BUTTON,
        "activity_right_ai_connection": ACTIVITY_RIGHT_AI_CONNECTION_BUTTON,
        "activity_right_chat": ACTIVITY_RIGHT_CHAT_BUTTON,
        "activity_right_debug_insights": ACTIVITY_RIGHT_DEBUG_INSIGHTS_BUTTON,
        "toolbar_new_macro": TOOLBAR_NEW_MACRO_BUTTON,
        "toolbar_paste": TOOLBAR_PASTE_BUTTON,
        "toolbar_run": TOOLBAR_RUN_BUTTON,
        "toolbar_save": TOOLBAR_SAVE_BUTTON,
        "toolbar_debug": TOOLBAR_DEBUG_BUTTON,
        "toolbar_copy": TOOLBAR_COPY_BUTTON,
        "toolbar_rename": TOOLBAR_RENAME_BUTTON,
        "toolbar_delete": TOOLBAR_DELETE_BUTTON,
        "toolbar_maximize": TOOLBAR_MAXIMIZE_BUTTON,
        "toolbar_minimize": TOOLBAR_MINIMIZE_BUTTON,
        "console_save": CONSOLE_SAVE_BUTTON,
        "console_clear": CONSOLE_CLEAR_BUTTON,
        "settings_tab_editor": SETTINGS_TAB_EDITOR_BUTTON,
        "settings_tab_modules": SETTINGS_TAB_MODULES_BUTTON,
        "settings_tab_debug": SETTINGS_TAB_DEBUG_BUTTON,
        "settings_tab_dev_tools": SETTINGS_TAB_DEV_TOOLS_BUTTON,
        "settings_reset": SETTINGS_RESET_BUTTON,
        "settings_cancel": SETTINGS_CANCEL_BUTTON,
        "settings_save": SETTINGS_SAVE_BUTTON,
        "vba_conversion_accept": VBA_CONVERSION_ACCEPT_BUTTON,
        "vba_conversion_edit": VBA_CONVERSION_EDIT_BUTTON,
        "vba_conversion_cancel": VBA_CONVERSION_CANCEL_BUTTON,
        "welcome_ok": WELCOME_OK_BUTTON,
    }

    def wait_ready(self, timeout: int = 10):
        self._log("wait_ready timeout=%s", timeout)
        return self._wait_find_locator(self.APP_WORKBENCH, timeout=timeout)

    def _click_ready_locator(self, locator: tuple[str, str], timeout: int = 10):
        by, selector = locator
        button = self._wait_locator(
            locator,
            timeout=timeout,
            require_displayed=True,
            require_enabled=True,
        )
        if not button:
            raise TimeoutException(
                f"R7 Code button not ready: by={by} selector={selector}"
            )
        self._click(button)
        return button

    def open_plugin_by_caption(self, caption: str = "{r7}.code", timeout: int = 10):
        self._log("open_plugin_by_caption caption=%s", caption)
        locator = (
            By.XPATH,
            "//button[.//span[contains(@class,'caption') and normalize-space()="
            f"'{caption}'"
            "]]",
        )
        return self._js_click_locator(locator)

    def click_button(self, key: str, timeout: int = 10):
        locator = self.BUTTON_LOCATORS.get(key)
        if locator is None:
            available = ", ".join(sorted(self.BUTTON_LOCATORS.keys()))
            raise KeyError(f"Unknown R7 Code button key: {key}. Available: {available}")
        self._log("click_button key=%s", key)
        return self._click_ready_locator(locator, timeout=timeout)

    def click_main_editor(self, timeout: int = 10):
        self._log("click_main_editor")
        editor = self._wait_locator(
            self.MAIN_EDITOR_MONACO,
            timeout=timeout,
            require_displayed=True,
            require_enabled=False,
        )
        if not editor:
            raise TimeoutException("Main Monaco editor is not ready")
        self._click(editor)
        return editor

    def set_main_editor_text(self, text: str, timeout: int = 10) -> None:
        self._log("set_main_editor_text chars=%s", len(text))
        root = self._wait_locator(
            self.MAIN_EDITOR_ROOT,
            timeout=timeout,
            require_displayed=True,
            require_enabled=False,
        )
        if not root:
            raise TimeoutException("Main editor root not found")

        applied = bool(
            self.driver.driver.execute_script(
                """
                const root = arguments[0];
                const value = arguments[1];

                const host = root.matches('.monaco-editor')
                  ? root
                  : root.querySelector('.monaco-editor');

                const globalMonaco = window.monaco && window.monaco.editor;
                if (globalMonaco && typeof globalMonaco.getEditors === 'function') {
                  const editors = globalMonaco.getEditors() || [];
                  for (const ed of editors) {
                    const dom = ed && ed.getDomNode ? ed.getDomNode() : null;
                    if (dom && host && (dom === host || host.contains(dom) || dom.contains(host))) {
                      ed.setValue(value);
                      ed.focus();
                      return true;
                    }
                  }
                  if (editors.length > 0) {
                    editors[0].setValue(value);
                    editors[0].focus();
                    return true;
                  }
                }

                const ta = root.querySelector('textarea.inputarea') || root.querySelector('textarea');
                if (ta) {
                  ta.focus();
                  ta.value = value;
                  ta.dispatchEvent(new Event('input', { bubbles: true }));
                  ta.dispatchEvent(new Event('change', { bubbles: true }));
                  return true;
                }
                return false;
                """,
                root,
                text,
            )
        )

        if not applied:
            raise TimeoutException("Unable to set text in main R7 Code editor")

    # Common direct actions
    def click_toolbar_run(self, timeout: int = 10):
        return self.click_button("toolbar_run", timeout=timeout)

    def click_toolbar_save(self, timeout: int = 10):
        return self.click_button("toolbar_save", timeout=timeout)

    def click_toolbar_new_macro(self, timeout: int = 10):
        return self.click_button("toolbar_new_macro", timeout=timeout)

    def click_activity_left_settings(self, timeout: int = 10):
        return self.click_button("activity_left_settings", timeout=timeout)

    def click_settings_save(self, timeout: int = 10):
        return self.click_button("settings_save", timeout=timeout)
