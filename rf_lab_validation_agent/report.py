from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .models import AnalysisReport, RecordAnalysis


def write_markdown_report(report: AnalysisReport, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_markdown(report), encoding="utf-8")


def write_json_report(report: AnalysisReport, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(_report_to_dict(report), indent=2, ensure_ascii=False), encoding="utf-8")


def render_markdown(report: AnalysisReport) -> str:
    lines: list[str] = [
        "# RF Lab Validation Report",
        "",
        f"- Generated: {report.generated_at.isoformat(timespec='seconds')}",
        f"- Overall status: **{report.overall_status.upper()}**",
        f"- Test cases: {len(report.records)}",
        f"- Trend anomalies: {len(report.anomalies)}",
        "",
        "## Executive Summary",
        "",
    ]

    status_counts = _status_counts(report.records)
    lines.append(
        f"Pass: {status_counts['pass']}, Warn: {status_counts['warn']}, Fail: {status_counts['fail']}."
    )
    if report.anomalies:
        lines.append("Trend anomalies indicate possible drift and should be confirmed before expanding coverage.")
    else:
        lines.append("No trend anomaly was detected in the current data window.")

    lines.extend(["", "## Test Results", ""])
    lines.append("| Test ID | RAT | Band | Channel | Status | Score | Issue | Key Metrics |")
    lines.append("| --- | --- | --- | --- | --- | ---: | --- | --- |")
    for item in report.records:
        record = item.record
        issue = _issue_markdown(record.issue_id, report.issue_base_url)
        metrics = "<br>".join(
            f"{metric.name}: {metric.measured:g}{metric.unit} ({metric.status}, {metric.detail})"
            for metric in item.metrics
        )
        lines.append(
            f"| {record.test_id} | {record.rat} | {record.band} | {record.channel} | "
            f"{item.status.upper()} | {item.score} | {issue} | {metrics} |"
        )

    lines.extend(["", "## Trend Anomalies", ""])
    if not report.anomalies:
        lines.append("None.")
    else:
        lines.append("| Group | Metric | Severity | Detail | Tests |")
        lines.append("| --- | --- | --- | --- | --- |")
        for anomaly in report.anomalies:
            group = "/".join(anomaly.group)
            tests = ", ".join(anomaly.affected_test_ids)
            lines.append(
                f"| {group} | {anomaly.metric} | {anomaly.severity.upper()} | {anomaly.detail} | {tests} |"
            )

    lines.extend(["", "## Recommended Next Tests", ""])
    for item in report.records:
        if item.status == "pass" and item.score == 100:
            continue
        lines.append(f"### {item.record.test_id}")
        for recommendation in item.recommendations:
            lines.append(f"- {recommendation}")
        lines.append("")

    if all(item.status == "pass" and item.score == 100 for item in report.records):
        lines.append("- Current results are clean. Continue with the next band/channel/temperature corner.")

    return "\n".join(lines).rstrip() + "\n"


def _issue_markdown(issue_id: str | None, issue_base_url: str | None) -> str:
    if not issue_id:
        return ""
    if not issue_base_url:
        return issue_id
    return f"[{issue_id}]({issue_base_url.rstrip('/')}/{issue_id})"


def _status_counts(records: list[RecordAnalysis]) -> dict[str, int]:
    counts = {"pass": 0, "warn": 0, "fail": 0}
    for record in records:
        counts[record.status] += 1
    return counts


def _report_to_dict(report: AnalysisReport) -> dict[str, Any]:
    payload = asdict(report)
    payload["generated_at"] = report.generated_at.isoformat()
    for record in payload["records"]:
        record["record"]["timestamp"] = record["record"]["timestamp"].isoformat()
    payload["overall_status"] = report.overall_status
    return payload
