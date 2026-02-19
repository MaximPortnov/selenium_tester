import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from selenium.common.exceptions import NoSuchElementException

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.interaction_log_executor_simple import (  # noqa: E402
    InteractionStep,
    SimpleInteractionLogExecutor,
)
from src.pages.editor_page import EditorPage  # noqa: E402
from src.pages.home_page import HomePage  # noqa: E402
from src.pages.plugin_page import PluginPage  # noqa: E402
from src.pages.sql_manager_page import SqlManagerPage  # noqa: E402
from src.pages.sql_mode_page import SqlModePage  # noqa: E402


def _page(executor: SimpleInteractionLogExecutor, key: str):
    value = executor.context.get(key)
    if value is None:
        raise RuntimeError(f"Missing page in executor.context: {key}")
    return value

def _click_generic(executor: SimpleInteractionLogExecutor, step: InteractionStep) -> None:
    sql_manager_page = _page(executor, "sql_manager_page")
    locator = executor._locator_from_step(step)
    if not locator:
        raise NoSuchElementException(
            f"Cannot build click locator for line={step.index}"
        )
    executor.logger.info(
        "profile click_generic line=%s locator=%s",
        step.index,
        locator,
    )
    sql_manager_page._click_locator(locator)


def _set_query_text_from_step(
    executor: SimpleInteractionLogExecutor, step: InteractionStep
) -> None:
    value = executor._get_value_from_step(step)
    if value is None:
        raise RuntimeError(f"codemirror-change has no value at line={step.index}")
    text = str(value)
    executor.logger.info(
        "profile set_query_text line=%s chars=%s",
        step.index,
        len(text),
    )
    _page(executor, "sql_manager_page").set_query_text(text)


def _set_export_destination_from_step(
    executor: SimpleInteractionLogExecutor,
    step: InteractionStep,
) -> None:
    step_value = str(executor._get_value_from_step(step) or "").strip()
    visible_text = (str(getattr(step, "text", None) or "").strip() or step_value)
    if not visible_text:
        executor.logger.info(
            "profile set_export_destination skipped line=%s: empty text/value",
            step.index,
        )
        return
    normalized = visible_text.lower()
    if ("нов" in normalized and "текущ" in normalized) or (
        "new" in normalized and "current" in normalized
    ):
        executor.logger.info(
            "profile set_export_destination ambiguous line=%s value=%s -> skip direct select",
            step.index,
            visible_text,
        )
        return
    executor.logger.info(
        "profile set_export_destination line=%s value=%s",
        step.index,
        visible_text,
    )
    _page(executor, "sql_manager_page").select_export_destination(visible_text)


def _handle_export_destination_control(
    executor: SimpleInteractionLogExecutor,
    step: InteractionStep,
) -> None:
    event, action = step.action_key
    if event == "click" and action == "activate":
        _click_generic(executor, step)
        return
    _set_export_destination_from_step(executor, step)


def _delete_active_query(executor: SimpleInteractionLogExecutor) -> None:
    sql_manager_page = _page(executor, "sql_manager_page")
    executor.logger.info("profile delete_active_query")
    sql_manager_page.click_query_delete()
    sql_manager_page.card = None


def _perform_drag_drop(
    executor: SimpleInteractionLogExecutor,
    source_step: InteractionStep,
    target_step: InteractionStep,
) -> None:
    sql_manager_page = _page(executor, "sql_manager_page")
    source_locator = executor._locator_from_step(source_step)
    target_locator = executor._locator_from_step(target_step)
    source_point = executor._point_from_step(source_step)
    target_point = executor._point_from_step(target_step)
    step_delay_ms = int(executor.context.get("drag_step_delay_ms", 70))
    settle_delay_sec = float(executor.context.get("drag_settle_delay_sec", 0.10))
    executor.logger.info(
        "profile drag_drop source_line=%s target_line=%s source_locator=%s target_locator=%s source_point=%s target_point=%s step_delay_ms=%s settle_delay_sec=%s",
        source_step.index,
        target_step.index,
        source_locator,
        target_locator,
        source_point,
        target_point,
        step_delay_ms,
        settle_delay_sec,
    )
    sql_manager_page.drag_and_drop(
        source_locator=source_locator,
        target_locator=target_locator,
        source_point=source_point,
        target_point=target_point,
        step_delay_ms=step_delay_ms,
        settle_delay_sec=settle_delay_sec,
    )


def _on_drag_start(executor: SimpleInteractionLogExecutor, step: InteractionStep) -> None:
    executor.context["_pending_drag_source"] = step
    executor.logger.info(
        "profile drag_start line=%s testId=%s point=%s",
        step.index,
        getattr(step, "testId", None),
        executor._point_from_step(step),
    )


def _on_drop(executor: SimpleInteractionLogExecutor, step: InteractionStep) -> None:
    source_step = executor.context.get("_pending_drag_source")
    if source_step is None:
        executor.logger.info("profile drop skipped line=%s: no drag source", step.index)
        return
    _perform_drag_drop(executor, source_step, step)
    executor.context["_pending_drag_source"] = None


def _on_drag_end(executor: SimpleInteractionLogExecutor) -> None:
    executor.context["_pending_drag_source"] = None


def _set_query_name_from_step(
    executor: SimpleInteractionLogExecutor, step: InteractionStep
) -> None:
    value = str(executor._get_value_from_step(step) or "").strip()
    if not value:
        executor.logger.info(
            "profile set_query_name skipped line=%s: empty value",
            step.index,
        )
        return
    executor.logger.info("profile set_query_name line=%s value=%s", step.index, value)
    _page(executor, "sql_manager_page").enter_query_name(value)


def _handle_query_editor(
    executor: SimpleInteractionLogExecutor,
    step: InteractionStep,
) -> None:
    event, action = step.action_key
    if action == "set-value" or event == "codemirror-change":
        _set_query_text_from_step(executor, step)
        return
    _click_generic(executor, step)


def _build_pages(executor: SimpleInteractionLogExecutor) -> dict[str, Any]:
    return {
        "home_page": HomePage(executor.driver),
        "editor_page": EditorPage(executor.driver),
        "plugin_page": PluginPage(executor.driver),
        "sql_mode_page": SqlModePage(executor.driver),
        "sql_manager_page": SqlManagerPage(executor.driver),
        "preview_timeout": 60,
        "export_timeout": 60,
        "success_timeout": 30,
        "drag_step_delay_ms": 70,
        "drag_settle_delay_sec": 0.10,
        "_pending_drag_source": None,
    }


def build_context(executor: SimpleInteractionLogExecutor) -> dict[str, Any]:
    return _build_pages(executor)


def build_prepare_hook(executor: SimpleInteractionLogExecutor) -> Callable[[], None]:
    def _prepare() -> None:
        _page(executor, "home_page").open_creation_cell()
        _page(executor, "editor_page").click_plugin_button()
        _page(executor, "editor_page").try_click_close()

    return _prepare


def build_default_click_handler(
    executor: SimpleInteractionLogExecutor,
) -> Callable[[InteractionStep], None]:
    return lambda step: _click_generic(executor, step)


def build_step_routes(
    executor: SimpleInteractionLogExecutor,
) -> dict[tuple[str, str], Callable[[InteractionStep], None]]:
    return {
        ("dragstart", "*"): lambda step: _on_drag_start(executor, step),
        ("drop", "*"): lambda step: _on_drop(executor, step),
        ("dragend", "*"): lambda _step: _on_drag_end(executor),
        ("drag", "*"): lambda _step: None,
        ("click", "preview"): lambda _step: _page(
            executor, "sql_manager_page"
        ).click_query_preview(timeout=int(executor.context.get("preview_timeout", 60))),
        ("click", "export"): lambda _step: _page(executor, "sql_manager_page").click_export(),
        ("click", "delete"): lambda _step: _delete_active_query(executor),
        ("codemirror-change", "set-value"): lambda step: _set_query_text_from_step(
            executor, step
        ),
    }


def build_click_routes(
    executor: SimpleInteractionLogExecutor,
) -> tuple[
    dict[str, Callable[[InteractionStep], None]],
    dict[str, Callable[[InteractionStep], None]],
]:
    plugin_page = _page(executor, "plugin_page")
    sql_mode_page = _page(executor, "sql_mode_page")
    sql_manager_page = _page(executor, "sql_manager_page")

    exact: dict[str, Callable[[InteractionStep], None]] = {
        "main-sql-mode": lambda _step: plugin_page.click_main_sql_mode(),
        "main-olap-mode": lambda _step: plugin_page.click_main_olap_mode(),
        "main-file-mode": lambda _step: plugin_page.click_main_file_mode(),
        "main-smartdocs": lambda _step: plugin_page.click_main_smartdocs(),
        "main-connection-manager": lambda _step: plugin_page.click_main_connection_manager(),
        "main-settings": lambda _step: plugin_page.click_main_settings(),
        "main-about": lambda _step: plugin_page.click_main_about(),
        "sql-home-open-sql-manager": lambda _step: sql_mode_page.click_sql_manager(),
        "sql-home-open-report-manager": lambda _step: sql_mode_page.click_report_manager(),
        "sql-home-open-query-history": lambda _step: sql_mode_page.click_query_history(),
        "sql-home-open-log": lambda _step: sql_mode_page.click_log(),
        "sql-manager-add-query-open": lambda _step: sql_manager_page.click_add_query_button(),
        "sql-manager-add-query-confirm": lambda _step: sql_manager_page.confirm_add_query(),
        "sql-manager-add-query-name": lambda step: _set_query_name_from_step(
            executor, step
        ),
        "sql-manager-export-confirm": lambda _step: sql_manager_page.confirm_export(
            timeout=int(executor.context.get("export_timeout", 60))
        ),
        "sql-manager-export-destination": lambda step: _handle_export_destination_control(
            executor, step
        ),
        "messagebox-button-OK-0": lambda _step: sql_manager_page.click_success_ok(
            timeout=int(executor.context.get("success_timeout", 30))
        ),
        "sql-manager-minimize": lambda _step: sql_manager_page.minimize(),
        "sql-manager-toggle-left-panel": lambda _step: sql_manager_page.toggle_left_panel_panel(),
    }

    prefix: dict[str, Callable[[InteractionStep], None]] = {
        "cm-tree-connection-": lambda step: (
            sql_manager_page.select_connection(
                str(getattr(step, "connectionName", None) or "").strip()
            )
            if str(getattr(step, "connectionName", None) or "").strip()
            else _click_generic(executor, step)
        ),
        "sql-manager-query-preview-": lambda _step: sql_manager_page.click_query_preview(
            timeout=int(executor.context.get("preview_timeout", 60))
        ),
        "sql-manager-query-export-": lambda _step: sql_manager_page.click_export(),
        "sql-manager-query-delete-": lambda _step: _delete_active_query(executor),
        "sql-manager-query-editor-": lambda step: _handle_query_editor(executor, step),
        "custom-select-item-sql_manager_export_destination-": lambda step: (
            sql_manager_page.select_export_destination(
                (
                    str(getattr(step, "text", None) or "").strip()
                    or str(executor._get_value_from_step(step) or "").strip()
                )
            )
            if (
                str(getattr(step, "text", None) or "").strip()
                or str(executor._get_value_from_step(step) or "").strip()
            )
            else _click_generic(executor, step)
        ),
    }
    return exact, prefix


def build_skip_rules() -> list[dict[str, Any]]:
    return [
        {
            "event": "input",
            "action": "set-value",
            "testId": "sql-manager-add-query-name",
        },
        {
            "event": "codemirror-change",
            "action": "set-value",
            "testId": "sql-codemirror-container-sql_wizard_output",
        },
        {
            "event": "click",
            "action": "activate",
            "testId__startswith": "sql-codemirror-",
        },
    ]


def configure_executor(executor: SimpleInteractionLogExecutor) -> None:
    executor.context.update(build_context(executor))
    exact, prefix = build_click_routes(executor)
    executor.set_click_routes(exact, prefix)
    executor.set_step_routes(build_step_routes(executor))
    executor.set_skip_rules(build_skip_rules())
    executor.set_default_click_handler(build_default_click_handler(executor))
    executor.set_prepare_hook(build_prepare_hook(executor))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run `python -m src.interaction_log_executor_simple --log ...` "
            "with routes from this file."
        )
    )
    parser.add_argument(
        "--log",
        type=Path,
        default=Path("interaction-log-1771241377641.jsonl"),
        help="Path to interaction log JSONL.",
    )
    parser.add_argument(
        "--debugger-address",
        default="127.0.0.1:9222",
        help="OnlyOffice remote debugger address.",
    )
    parser.add_argument(
        "--no-prepare",
        action="store_true",
        help="Do not auto-open cell and plugin home before replay.",
    )
    args = parser.parse_args(argv)

    if not args.log.exists():
        print(f"[replay-profile] log not found: {args.log}")
        return 2

    cmd = [
        sys.executable,
        "-m",
        "src.interaction_log_executor_simple",
        "--log",
        str(args.log),
        "--debugger-address",
        args.debugger_address,
    ]
    if args.no_prepare:
        cmd.append("--no-prepare")

    env = os.environ.copy()
    env["OO_SIMPLE_ROUTES_MODULE"] = "test.run_replay_simple"

    print("[replay-profile] run:", " ".join(cmd))
    return subprocess.call(cmd, cwd=str(ROOT), env=env)


if __name__ == "__main__":
    raise SystemExit(main())
