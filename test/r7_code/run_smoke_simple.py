import argparse
import sys
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.driver import DriverOnlyOffice  # noqa: E402
from src.pages_r7_code.r7_code_page import R7CodePage  # noqa: E402
from src.pages_slider_query.editor_page import EditorPage  # noqa: E402
from src.pages_slider_query.home_page import HomePage  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Simple R7 Code smoke: open document tab, open plugin, click buttons, type in editor."
    )
    parser.add_argument(
        "--debugger-address",
        default="127.0.0.1:9222",
        help="OnlyOffice remote debugger address.",
    )
    parser.add_argument(
        "--keep-open",
        action="store_true",
        help="Do not close webdriver session after script.",
    )
    args = parser.parse_args(argv)

    driver = DriverOnlyOffice(debugger_address=args.debugger_address)
    home_page = HomePage(driver)
    editor_page = EditorPage(driver)
    r7_page = R7CodePage(driver)

    try:
        # Same prepare flow as in slider_query profile:
        # 1) open a new editor tab 2) open Plugins tab 3) click plugin button.
        home_page.open_creation_cell()
        editor_page.open_plugins_tab()
        r7_page.open_plugin_by_caption("{r7}.code", timeout=20)
        r7_page.wait_ready(timeout=20)

        # If welcome popup appears, close it (optional step).
        try:
            r7_page.click_button("welcome_ok", timeout=2)
        except Exception:
            pass
        # A couple of direct clicks
        # r7_page.click_button("activity_left_view_examples", timeout=10)
        r7_page.click_toolbar_new_macro(timeout=10)
        time.sleep(2)
        # Click a couple more toolbar actions
        r7_page.click_toolbar_run(timeout=10)

        print("[r7-smoke] done")
        return 0
    finally:
        if not args.keep_open:
            try:
                driver.driver.quit()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
