"""
Simple interaction log replay for OnlyOffice SQL plugin.

Design goals:
- flat replay loop in file order;
- explicit dict-based routing configured from caller side;
- executor stays a dumb dispatcher.
"""

from __future__ import annotations

import argparse
import importlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Callable

from selenium.webdriver.common.by import By

from .driver import DriverOnlyOffice
from .utils.logging_utils import get_logger


_GENERATED_TEST_ID_SUFFIX_RE = re.compile(r"[A-Za-z0-9]+(?:_[A-Za-z0-9]+)+$")
_SELECTOR_TEST_ID_RE = re.compile(r"""^\[data-testid=(["'])(.+?)\1\]$""")

StepHandler = Callable[["InteractionStep"], None]


class InteractionStep:
    """
    Plain wrapper around one JSON object line.
    Keeps original nesting as-is.
    """

    def __init__(self, raw: dict[str, Any], index: int):
        if not isinstance(raw, dict):
            raise TypeError("InteractionStep raw payload must be dict")
        self.data = raw
        self.raw = raw
        self.index = index
        self.__dict__.update(raw)

    @classmethod
    def from_raw(cls, raw: dict[str, Any], index: int) -> "InteractionStep":
        return cls(raw=raw, index=index)

    @property
    def action_key(self) -> tuple[str, str]:
        event = str(self.raw.get("event") or "").strip().lower()
        action = str(self.raw.get("action") or "").strip().lower()
        return event, action

    def get(self, key: str, default: Any = None) -> Any:
        return self.raw.get(key, default)


def read_interaction_log(log_path: str | Path) -> list[InteractionStep]:
    path = Path(log_path)
    if not path.exists():
        raise FileNotFoundError(f"Interaction log not found: {path}")

    steps: list[InteractionStep] = []
    with path.open("r", encoding="utf-8-sig") as stream:
        for line_number, line in enumerate(stream, start=1):
            payload = line.strip()
            if not payload:
                continue
            try:
                raw = json.loads(payload)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at {path}:{line_number}") from exc
            if not isinstance(raw, dict):
                raise ValueError(f"JSON line must be an object at {path}:{line_number}")
            steps.append(InteractionStep.from_raw(raw, index=line_number))
    return steps


def find_latest_interaction_log(root: str | Path = ".") -> Path | None:
    base = Path(root)
    candidates = sorted(
        base.glob("interaction-log-*.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


class SimpleInteractionLogExecutor:
    """
    Universal replay executor:
    - applies skip rules;
    - dispatches by event/action and/or testId;
    - uses caller-provided handlers for domain logic.
    """

    DEFAULT_SKIP_RULES: list[dict[str, Any]] = []

    def __init__(
        self,
        *,
        driver: DriverOnlyOffice | None = None,
        debugger_address: str = "127.0.0.1:9222",
        click_routes_exact: dict[str, StepHandler] | None = None,
        click_routes_prefix: dict[str, StepHandler] | None = None,
        step_routes: dict[tuple[str, str], StepHandler] | None = None,
        skip_rules: list[dict[str, Any]] | None = None,
        default_click_handler: StepHandler | None = None,
        prepare_hook: Callable[[], None] | None = None,
        context: dict[str, Any] | None = None,
    ):
        self.driver = driver or DriverOnlyOffice(debugger_address=debugger_address)
        self.logger = get_logger("interaction_log_executor_simple")
        self._ensure_info_logging()

        self.context: dict[str, Any] = dict(context or {})
        self.default_click_handler: StepHandler | None = default_click_handler
        self.prepare_hook: Callable[[], None] | None = prepare_hook

        default_exact, default_prefix = self._build_click_routes()
        self.click_routes_exact: dict[str, StepHandler] = {}
        self.click_routes_prefix: dict[str, StepHandler] = {}
        self.step_routes: dict[tuple[str, str], StepHandler] = {}
        self.set_click_routes(
            click_routes_exact if click_routes_exact is not None else default_exact,
            click_routes_prefix if click_routes_prefix is not None else default_prefix,
        )
        self.set_step_routes(
            step_routes if step_routes is not None else self._build_step_routes()
        )
        initial_skip_rules = (
            skip_rules if skip_rules is not None else self.DEFAULT_SKIP_RULES
        )
        self.skip_rules: list[dict[str, Any]] = [dict(r) for r in initial_skip_rules]

    def _ensure_info_logging(self) -> None:
        root_name = self.logger.name.split(".", 1)[0]
        root_logger = logging.getLogger(root_name)
        if root_logger.level > logging.INFO:
            root_logger.setLevel(logging.INFO)
        for handler in root_logger.handlers:
            if handler.level > logging.INFO:
                handler.setLevel(logging.INFO)

        log_file = getattr(root_logger, "log_file", None)
        if log_file:
            self.logger.info("executor logger ready: file=%s", log_file)
        else:
            self.logger.info("executor logger ready")

    # ---------- public API ----------
    def replay_file(
        self,
        log_path: str | Path,
        *,
        prepare_plugin_home: bool = True,
        stop_on_error: bool = True,
    ) -> None:
        steps = read_interaction_log(log_path)
        self.logger.info(
            "Replay file=%s steps=%s prepare_plugin_home=%s stop_on_error=%s",
            log_path,
            len(steps),
            prepare_plugin_home,
            stop_on_error,
        )
        if prepare_plugin_home:
            if self.prepare_hook is None:
                self.logger.info("Prepare hook is not configured: skip prepare")
            else:
                self.prepare_hook()
        self.replay_steps(steps, stop_on_error=stop_on_error)

    def replay_steps(
        self,
        steps: list[InteractionStep],
        *,
        stop_on_error: bool = True,
    ) -> None:
        self.logger.info("Replay started: total_steps=%s", len(steps))
        for step in steps:
            try:
                self.execute_step(step)
            except Exception as exc:
                seq = getattr(step, "seq", None)
                event = getattr(step, "event", None)
                action = getattr(step, "action", None)
                test_id = getattr(step, "testId", None)
                message = (
                    f"Replay failed on line={step.index}, seq={seq}, "
                    f"event={event}/{action}, testId={test_id}"
                )
                self.logger.exception(message)
                if stop_on_error:
                    raise RuntimeError(message) from exc
        self.logger.info("Replay finished")

    def execute_step(self, step: InteractionStep) -> None:
        event, action = step.action_key
        self.logger.info(
            "Step line=%s seq=%s event/action=%s/%s testId=%s",
            step.index,
            getattr(step, "seq", None),
            event,
            action,
            getattr(step, "testId", None),
        )

        if self._should_skip_step(step):
            return
        if self._dispatch_by_step_route(step, event, action):
            return
        if self._dispatch_by_test_id(step):
            return
        if event == "click" and self.default_click_handler is not None:
            self.logger.info(
                "Route default-click line=%s testId=%s",
                step.index,
                getattr(step, "testId", None),
            )
            self.default_click_handler(step)
            return

        self.logger.info(
            "Skip line=%s event/action=%s/%s", step.index, event, action
        )

    def close(self) -> None:
        try:
            self.driver.driver.quit()
        except Exception:
            pass

    def __enter__(self) -> "SimpleInteractionLogExecutor":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def set_skip_rules(self, rules: list[dict[str, Any]]) -> None:
        self.skip_rules = [dict(rule) for rule in rules]

    def add_skip_rule(self, **rule: Any) -> None:
        if rule:
            self.skip_rules.append(rule)

    def set_click_routes(
        self,
        exact: dict[str, StepHandler] | None = None,
        prefix: dict[str, StepHandler] | None = None,
    ) -> None:
        self.click_routes_exact = dict(exact or {})
        self.click_routes_prefix = dict(prefix or {})

    def set_step_routes(
        self,
        routes: dict[tuple[str, str], StepHandler] | None = None,
    ) -> None:
        self.step_routes = dict(routes or {})

    def set_default_click_handler(self, handler: StepHandler | None) -> None:
        self.default_click_handler = handler

    def set_prepare_hook(self, hook: Callable[[], None] | None) -> None:
        self.prepare_hook = hook

    # ---------- routes ----------
    def _build_click_routes(
        self,
    ) -> tuple[dict[str, StepHandler], dict[str, StepHandler]]:
        return {}, {}

    def _build_step_routes(self) -> dict[tuple[str, str], StepHandler]:
        return {}

    def _dispatch_by_step_route(
        self,
        step: InteractionStep,
        event: str,
        action: str,
    ) -> bool:
        keys = [
            (event, action),
            (event, "*"),
            ("*", action),
        ]
        for key in keys:
            handler = self.step_routes.get(key)
            if handler is None:
                continue
            self.logger.info(
                "Route step line=%s key=%s",
                step.index,
                key,
            )
            handler(step)
            return True
        return False

    def _dispatch_by_test_id(self, step: InteractionStep) -> bool:
        test_id = getattr(step, "testId", None) or ""
        if not test_id:
            return False

        exact = self.click_routes_exact.get(test_id)
        if exact:
            self.logger.info(
                "Route exact line=%s testId=%s",
                step.index,
                test_id,
            )
            exact(step)
            return True

        for prefix, handler in self.click_routes_prefix.items():
            if test_id.startswith(prefix):
                self.logger.info(
                    "Route prefix line=%s testId=%s prefix=%s",
                    step.index,
                    test_id,
                    prefix,
                )
                handler(step)
                return True

        self.logger.info(
            "No route line=%s testId=%s",
            step.index,
            test_id,
        )
        return False

    def _should_skip_step(self, step: InteractionStep) -> bool:
        for rule in self.skip_rules:
            if self._rule_matches(step, rule):
                self.logger.info(
                    "Skip line=%s by rule=%s", step.index, rule
                )
                return True
        return False

    def _rule_matches(self, step: InteractionStep, rule: dict[str, Any]) -> bool:
        for key, expected in rule.items():
            field_key, op = self._parse_rule_key(key)
            actual = self._get_step_field(step, field_key)
            if op == "startswith":
                if actual is None:
                    matched = False
                elif isinstance(expected, (set, tuple, list)):
                    matched = any(
                        str(actual).startswith(str(prefix)) for prefix in expected
                    )
                else:
                    matched = str(actual).startswith(str(expected))
            elif callable(expected):
                try:
                    matched = bool(expected(actual, step))
                except TypeError:
                    matched = bool(expected(actual))
            elif isinstance(expected, (set, tuple, list)):
                matched = actual in expected
            else:
                matched = actual == expected
            if not matched:
                return False
        return True

    @staticmethod
    def _parse_rule_key(key: str) -> tuple[str, str]:
        suffix = "__startswith"
        if key.endswith(suffix):
            return key[: -len(suffix)], "startswith"
        return key, "eq"

    @staticmethod
    def _get_step_field(step: InteractionStep, key: str) -> Any:
        if key.startswith("raw."):
            return step.raw.get(key.split(".", 1)[1])
        if hasattr(step, key):
            return getattr(step, key)
        return step.raw.get(key)

    # ---------- generic helpers ----------
    @staticmethod
    def _locator_from_step(step: InteractionStep) -> tuple[str, str] | None:
        test_id = getattr(step, "testId", None)
        selector = getattr(step, "selector", None)

        if test_id:
            trimmed = _GENERATED_TEST_ID_SUFFIX_RE.sub("", test_id)
            safe = trimmed.replace("'", "\\'")
            if trimmed != test_id:
                return By.CSS_SELECTOR, f"[data-testid^='{safe}']"
            return By.CSS_SELECTOR, f"[data-testid='{safe}']"

        if selector:
            match = _SELECTOR_TEST_ID_RE.match(selector.strip())
            if match:
                selector_test_id = match.group(2)
                trimmed = _GENERATED_TEST_ID_SUFFIX_RE.sub("", selector_test_id)
                safe = trimmed.replace("'", "\\'")
                if trimmed != selector_test_id:
                    return By.CSS_SELECTOR, f"[data-testid^='{safe}']"
                return By.CSS_SELECTOR, f"[data-testid='{safe}']"
            return By.CSS_SELECTOR, selector

        return None

    @staticmethod
    def _point_from_step(step: InteractionStep) -> tuple[int, int] | None:
        x = getattr(step, "clientX", None)
        y = getattr(step, "clientY", None)
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            return int(x), int(y)
        return None

    @staticmethod
    def _get_value_from_step(step: InteractionStep) -> Any:
        direct = getattr(step, "value", None)
        if direct is not None:
            return direct

        event_data = getattr(step, "eventData", None)
        if isinstance(event_data, dict):
            detail = event_data.get("detail")
            if isinstance(detail, dict) and detail.get("value") is not None:
                return detail.get("value")
        return None


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Replay interaction-log-*.jsonl using external routes profile."
    )
    parser.add_argument(
        "--log",
        type=Path,
        default=None,
        help=(
            "Path to interaction log JSONL. Defaults to latest "
            "interaction-log-*.jsonl in cwd."
        ),
    )
    parser.add_argument(
        "--debugger-address",
        default="127.0.0.1:9222",
        help="OnlyOffice remote debugger address.",
    )
    parser.add_argument(
        "--no-prepare",
        action="store_true",
        help="Do not call prepare hook before replay.",
    )
    return parser


def _apply_external_profile(executor: SimpleInteractionLogExecutor) -> None:
    module_name = os.getenv("OO_SIMPLE_ROUTES_MODULE", "").strip()
    if not module_name:
        return

    module = importlib.import_module(module_name)
    configure_fn = getattr(module, "configure_executor", None)
    if callable(configure_fn):
        configure_fn(executor)
        executor.logger.info("External routes profile loaded: %s", module_name)
        return

    configured = False

    build_context_fn = getattr(module, "build_context", None)
    if callable(build_context_fn):
        extra_context = build_context_fn(executor)
        if isinstance(extra_context, dict):
            executor.context.update(extra_context)
            configured = True

    build_routes_fn = getattr(module, "build_click_routes", None)
    if callable(build_routes_fn):
        exact, prefix = build_routes_fn(executor)
        executor.set_click_routes(exact, prefix)
        configured = True

    build_step_routes_fn = getattr(module, "build_step_routes", None)
    if callable(build_step_routes_fn):
        executor.set_step_routes(build_step_routes_fn(executor))
        configured = True

    build_skips_fn = getattr(module, "build_skip_rules", None)
    if callable(build_skips_fn):
        rules = build_skips_fn()
        executor.set_skip_rules(rules)
        configured = True

    build_default_click_fn = getattr(module, "build_default_click_handler", None)
    if callable(build_default_click_fn):
        executor.set_default_click_handler(build_default_click_fn(executor))
        configured = True

    build_prepare_fn = getattr(module, "build_prepare_hook", None)
    if callable(build_prepare_fn):
        executor.set_prepare_hook(build_prepare_fn(executor))
        configured = True

    if configured:
        executor.logger.info("External routes profile loaded: %s", module_name)
    else:
        executor.logger.info(
            "External routes profile has no supported hooks: %s", module_name
        )


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    log_path = args.log or find_latest_interaction_log()
    if not log_path:
        parser.error(
            "Log path is not provided and no interaction-log-*.jsonl was found in current directory."
        )
    if not log_path.exists():
        parser.error(f"Log file not found: {log_path}")

    driver = DriverOnlyOffice(debugger_address=args.debugger_address)
    executor = SimpleInteractionLogExecutor(driver=driver)
    try:
        _apply_external_profile(executor)
        executor.replay_file(
            log_path=log_path,
            prepare_plugin_home=not args.no_prepare,
            stop_on_error=True,
        )
    except Exception as exc:
        print(f"[replay-simple] failed: {exc}")
        return 2
    finally:
        executor.close()

    print("[replay-simple] completed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
