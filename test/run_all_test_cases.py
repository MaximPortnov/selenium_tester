import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _safe_name(name: str) -> str:
    allowed = []
    for ch in name:
        if ch.isalnum() or ch in {"-", "_", "."}:
            allowed.append(ch)
        else:
            allowed.append("_")
    return "".join(allowed)


def _find_logs(log_dir: Path) -> list[Path]:
    return sorted(log_dir.glob("run-*.log"), key=lambda p: p.stat().st_mtime)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run all interaction-log *.jsonl files from test_cases one-by-one "
            "using test/run_replay_simple.py and collect logs under artifacts."
        )
    )
    parser.add_argument(
        "--cases-dir",
        type=Path,
        default=Path("test_cases"),
        help="Directory with *.jsonl replay cases.",
    )
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        default=Path("artifacts/replay_cases"),
        help="Root directory where per-run logs/reports are stored.",
    )
    parser.add_argument(
        "--debugger-address",
        default="127.0.0.1:9222",
        help="OnlyOffice remote debugger address.",
    )
    parser.add_argument(
        "--no-prepare",
        action="store_true",
        help="Pass --no-prepare to replay launcher.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue executing remaining cases if one case fails.",
    )
    args = parser.parse_args(argv)

    cases_dir = (ROOT / args.cases_dir).resolve()
    if not cases_dir.exists():
        print(f"[batch-replay] cases dir not found: {cases_dir}")
        return 2

    case_files = sorted(cases_dir.glob("*.jsonl"))
    if not case_files:
        print(f"[batch-replay] no *.jsonl files in: {cases_dir}")
        return 2

    run_stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_root = (ROOT / args.artifacts_dir / f"batch-{run_stamp}").resolve()
    run_root.mkdir(parents=True, exist_ok=True)

    print(f"[batch-replay] run root: {run_root}")
    print(f"[batch-replay] cases: {len(case_files)}")

    results: list[dict[str, object]] = []
    failures = 0

    for idx, case_path in enumerate(case_files, start=1):
        case_name = _safe_name(case_path.stem)
        case_dir = run_root / f"{idx:03d}_{case_name}"
        case_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            sys.executable,
            "test/run_replay_simple.py",
            "--log",
            str(case_path),
            "--debugger-address",
            args.debugger_address,
        ]
        if args.no_prepare:
            cmd.append("--no-prepare")

        env = os.environ.copy()
        env["LOG_DIR"] = str(case_dir)
        env.setdefault("PYTHONIOENCODING", "utf-8")

        print(f"[batch-replay] ({idx}/{len(case_files)}) start: {case_path.name}")
        started = perf_counter()
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        duration_sec = round(perf_counter() - started, 3)

        stdout_path = case_dir / "stdout.log"
        stderr_path = case_dir / "stderr.log"
        stdout_path.write_text(proc.stdout or "", encoding="utf-8")
        stderr_path.write_text(proc.stderr or "", encoding="utf-8")
        log_files = [str(p.name) for p in _find_logs(case_dir)]

        status = "ok" if proc.returncode == 0 else "failed"
        if status == "failed":
            failures += 1
        print(
            f"[batch-replay] ({idx}/{len(case_files)}) {status}: "
            f"exit={proc.returncode}, duration={duration_sec}s, case_dir={case_dir.name}"
        )

        results.append(
            {
                "index": idx,
                "case_file": str(case_path),
                "case_dir": str(case_dir),
                "status": status,
                "returncode": proc.returncode,
                "duration_sec": duration_sec,
                "stdout_log": str(stdout_path),
                "stderr_log": str(stderr_path),
                "run_logs": log_files,
            }
        )

        if proc.returncode != 0 and not args.continue_on_error:
            break

    summary = {
        "cases_total": len(case_files),
        "cases_executed": len(results),
        "failures": failures,
        "run_root": str(run_root),
        "results": results,
    }
    summary_path = run_root / "summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"[batch-replay] summary: {summary_path}")
    if failures:
        print(f"[batch-replay] finished with failures={failures}")
        return 2

    print("[batch-replay] finished successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
