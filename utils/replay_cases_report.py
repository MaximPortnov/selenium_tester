from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_replay_root() -> Path:
    return _repo_root() / "artifacts" / "replay_cases"


def _find_latest_batch_dir(replay_root: Path) -> Path:
    candidates = [
        p
        for p in replay_root.glob("batch-*")
        if p.is_dir() and (p / "summary.json").exists()
    ]
    if not candidates:
        raise FileNotFoundError(
            f"No batch-* folders with summary.json in: {replay_root}"
        )
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _resolve_summary_path(target: str | None) -> Path:
    if not target:
        return _find_latest_batch_dir(_default_replay_root()) / "summary.json"

    raw = Path(target).expanduser()
    if not raw.is_absolute():
        raw = (_repo_root() / raw).resolve()

    if raw.is_file():
        return raw
    if not raw.exists():
        raise FileNotFoundError(f"Path not found: {raw}")

    summary = raw / "summary.json"
    if summary.exists():
        return summary

    return _find_latest_batch_dir(raw) / "summary.json"


def _load_summary(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}") from exc


def _fmt_duration(value: Any) -> str:
    if isinstance(value, (float, int)):
        return f"{float(value):.3f}"
    return "-"


def _short_name(path_like: Any) -> str:
    if not isinstance(path_like, str) or not path_like:
        return "-"
    return Path(path_like).name


def _make_rows(results: list[dict[str, Any]]) -> list[list[str]]:
    rows: list[list[str]] = []
    for item in results:
        rows.append(
            [
                str(item.get("index", "-")),
                str(item.get("status", "-")),
                str(item.get("returncode", "-")),
                _fmt_duration(item.get("duration_sec")),
                _short_name(item.get("case_file")),
                ",".join(item.get("run_logs", []) or []) or "-",
            ]
        )
    return rows


def _print_table(headers: list[str], rows: list[list[str]]) -> None:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def _line(parts: list[str]) -> str:
        return " | ".join(parts[i].ljust(widths[i]) for i in range(len(parts)))

    sep = "-+-".join("-" * w for w in widths)
    print(_line(headers))
    print(sep)
    for row in rows:
        print(_line(row))


def _print_report(summary: dict[str, Any], summary_path: Path) -> None:
    results = summary.get("results", [])
    if not isinstance(results, list):
        results = []

    print(f"Summary: {summary_path}")
    print(f"Run root: {summary.get('run_root', '-')}")
    print(
        "Totals: "
        f"total={summary.get('cases_total', '-')}, "
        f"executed={summary.get('cases_executed', '-')}, "
        f"failures={summary.get('failures', '-')}"
    )
    print()

    if not results:
        print("No case results.")
        return

    rows = _make_rows([r for r in results if isinstance(r, dict)])
    _print_table(
        headers=["#", "status", "rc", "sec", "case", "run_log"],
        rows=rows,
    )

    failed = [r for r in results if isinstance(r, dict) and r.get("status") != "ok"]
    if failed:
        print()
        print("Failed cases:")
        for item in failed:
            print(
                f"- #{item.get('index', '-')}: {item.get('case_file', '-')}"
                f" | stderr={item.get('stderr_log', '-')}"
                f" | case_dir={item.get('case_dir', '-')}"
            )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Pretty-print replay_cases summary. "
            "By default uses latest artifacts/replay_cases/batch-*/summary.json."
        )
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=None,
        help=(
            "Path to summary.json, batch directory, or replay_cases root. "
            "Default: latest artifacts/replay_cases batch."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        summary_path = _resolve_summary_path(args.target)
        summary = _load_summary(summary_path)
        _print_report(summary, summary_path)
        return 0
    except Exception as exc:
        print(f"[replay-cases-report] failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
