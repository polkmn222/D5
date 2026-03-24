from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from textwrap import dedent


EVIDENCE_DIR = Path(__file__).resolve().parent / "evidence"


@dataclass(frozen=True)
class ChecklistItem:
    label: str
    steps: str
    expected: str
    area: str = "General"
    severity: str = "medium"


def parse_args(default_name: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--print-only", action="store_true", help="Print the checklist without interactive prompts")
    parser.add_argument("--no-save", action="store_true", help="Do not write a markdown report to manual/evidence")
    parser.add_argument("--report-name", default=default_name, help="Base name for the generated markdown report")
    return parser.parse_args()


def print_checklist(title: str, intro: str, items: list[ChecklistItem]) -> None:
    print(title)
    print()
    print(intro)
    print()
    for index, item in enumerate(items, start=1):
        print(f"{index}. [{item.area}] {item.label} ({item.severity})")
        print(f"   Steps: {item.steps}")
        print(f"   Expected: {item.expected}")


def collect_results(title: str, items: list[ChecklistItem]) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    print(title)
    print("Enter: [p]ass, [f]ail, [s]kip, [n]ote-only")
    print()
    for index, item in enumerate(items, start=1):
        print(f"{index}. [{item.area}] {item.label} ({item.severity})")
        print(f"   Steps: {item.steps}")
        print(f"   Expected: {item.expected}")
        status = input("   Result [p/f/s/n]: ").strip().lower() or "s"
        while status not in {"p", "f", "s", "n"}:
            status = input("   Use p, f, s, or n: ").strip().lower() or "s"
        notes = input("   Notes: ").strip()
        results.append(
            {
                "label": item.label,
                "status": {"p": "pass", "f": "fail", "s": "skip", "n": "note"}[status],
                "steps": item.steps,
                "expected": item.expected,
                "notes": notes,
                "area": item.area,
                "severity": item.severity,
            }
        )
        print()
    return results


def write_report(report_name: str, title: str, intro: str, results: list[dict[str, str]]) -> Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EVIDENCE_DIR / f"{report_name}_{timestamp}.md"
    generated_at = datetime.now().isoformat(timespec="seconds")
    lines = [f"# {title}", "", intro, "", f"Generated: {generated_at}", ""]
    summary = {
        "pass": sum(1 for result in results if result["status"] == "pass"),
        "fail": sum(1 for result in results if result["status"] == "fail"),
        "skip": sum(1 for result in results if result["status"] == "skip"),
        "note": sum(1 for result in results if result["status"] == "note"),
    }
    failed = [result for result in results if result["status"] == "fail"]
    total = len(results)
    lines.extend(
        [
            "## Summary",
            "",
            f"- total: {total}",
            f"- pass: {summary['pass']}",
            f"- fail: {summary['fail']}",
            f"- skip: {summary['skip']}",
            f"- note: {summary['note']}",
            "",
            "## Failures",
            "",
        ]
    )
    if failed:
        for result in failed:
            lines.append(f"- [{result['area']}] {result['label']}: {result['notes'] or '(no notes)'}")
    else:
        lines.append("- none")

    lines.extend(["", "## Area Summary", ""])
    for area in sorted({result["area"] for result in results}):
        area_results = [result for result in results if result["area"] == area]
        area_pass = sum(1 for result in area_results if result["status"] == "pass")
        area_fail = sum(1 for result in area_results if result["status"] == "fail")
        area_skip = sum(1 for result in area_results if result["status"] == "skip")
        area_note = sum(1 for result in area_results if result["status"] == "note")
        lines.append(f"- {area}: pass={area_pass}, fail={area_fail}, skip={area_skip}, note={area_note}")

    lines.extend(["", "## Results", ""])
    for result in results:
        lines.extend(
            [
                f"### [{result['area']}] {result['label']}",
                "",
                f"- status: {result['status']}",
                f"- severity: {result['severity']}",
                f"- steps: {result['steps']}",
                f"- expected: {result['expected']}",
                f"- notes: {result['notes'] or '(none)'}",
                "",
            ]
        )
    path.write_text("\n".join(lines))
    return path


def run_checklist(title: str, intro: str, items: list[ChecklistItem], default_report_name: str) -> None:
    args = parse_args(default_report_name)
    intro = dedent(intro).strip()
    if args.print_only:
        print_checklist(title, intro, items)
        return

    results = collect_results(title, items)
    if args.no_save:
        print("Manual checklist completed without saving a report.")
        return

    report_path = write_report(args.report_name, title, intro, results)
    print(f"Saved report to {report_path}")
