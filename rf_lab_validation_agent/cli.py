from __future__ import annotations

import argparse
from pathlib import Path

from .analyzer import analyze_records
from .loader import load_records
from .models import Thresholds
from .report import write_json_report, write_markdown_report


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="rf-lab-agent",
        description="Analyze RF lab and field validation results, detect anomalies, and generate reports.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Analyze a CSV or JSON test result file.")
    analyze.add_argument("--input", "-i", required=True, help="CSV or JSON test result file.")
    analyze.add_argument("--output", "-o", default="reports/rf_validation_report.md", help="Markdown report path.")
    analyze.add_argument("--json-output", default=None, help="Optional JSON report path.")
    analyze.add_argument("--issue-base-url", default=None, help="Issue tracker URL prefix.")
    analyze.add_argument("--sensitivity-margin-db", type=float, default=1.5)
    analyze.add_argument("--throughput-ratio", type=float, default=0.95)
    analyze.add_argument("--evm-ratio", type=float, default=1.10)
    analyze.add_argument("--rsrp-margin-db", type=float, default=2.0)

    args = parser.parse_args()

    if args.command == "analyze":
        thresholds = Thresholds(
            sensitivity_margin_db=args.sensitivity_margin_db,
            throughput_ratio=args.throughput_ratio,
            evm_ratio=args.evm_ratio,
            rsrp_margin_db=args.rsrp_margin_db,
        )
        records = load_records(args.input)
        report = analyze_records(records, thresholds=thresholds, issue_base_url=args.issue_base_url)
        write_markdown_report(report, args.output)
        if args.json_output:
            write_json_report(report, args.json_output)
        print(
            f"Analyzed {len(records)} records: status={report.overall_status}, "
            f"anomalies={len(report.anomalies)}, report={Path(args.output)}"
        )
        return 0 if report.overall_status != "fail" else 2

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
