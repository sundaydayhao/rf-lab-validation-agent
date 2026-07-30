from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from statistics import mean

from .models import (
    AnalysisReport,
    MetricResult,
    RecordAnalysis,
    TestRecord,
    Thresholds,
    TrendAnomaly,
)


def analyze_records(
    records: list[TestRecord],
    thresholds: Thresholds | None = None,
    issue_base_url: str | None = None,
) -> AnalysisReport:
    active_thresholds = thresholds or Thresholds()
    analyses = [_analyze_record(record, active_thresholds) for record in records]
    anomalies = _detect_trends(records, active_thresholds)
    return AnalysisReport(
        generated_at=datetime.now().astimezone(),
        records=analyses,
        anomalies=anomalies,
        issue_base_url=issue_base_url,
    )


def _analyze_record(record: TestRecord, thresholds: Thresholds) -> RecordAnalysis:
    metrics: list[MetricResult] = []
    metrics.extend(_metric_sensitivity(record, thresholds))
    metrics.extend(_metric_throughput(record, thresholds))
    metrics.extend(_metric_evm(record, thresholds))
    metrics.extend(_metric_rsrp(record, thresholds))

    failures = sum(1 for metric in metrics if metric.status == "fail")
    warnings = sum(1 for metric in metrics if metric.status == "warn")
    status = "fail" if failures else "warn" if warnings else "pass"
    score = max(0, 100 - failures * 25 - warnings * 10)

    return RecordAnalysis(
        record=record,
        metrics=metrics,
        status=status,
        score=score,
        recommendations=_recommend_next_steps(record, metrics),
    )


def _metric_sensitivity(record: TestRecord, thresholds: Thresholds) -> list[MetricResult]:
    expected = record.expected_sensitivity_dbm
    measured = record.measured_sensitivity_dbm
    if expected is None or measured is None:
        return []
    delta = measured - expected
    status = "pass" if delta <= thresholds.sensitivity_margin_db else "fail"
    return [
        MetricResult(
            name="sensitivity",
            expected=expected,
            measured=measured,
            status=status,
            delta=delta,
            unit="dBm",
            detail=f"{delta:+.2f} dB versus expected; lower is better",
        )
    ]


def _metric_throughput(record: TestRecord, thresholds: Thresholds) -> list[MetricResult]:
    expected = record.expected_throughput_mbps
    measured = record.measured_throughput_mbps
    if expected is None or measured is None:
        return []
    ratio = measured / expected if expected else 0.0
    status = "pass" if ratio >= thresholds.throughput_ratio else "fail"
    return [
        MetricResult(
            name="throughput",
            expected=expected,
            measured=measured,
            status=status,
            delta=measured - expected,
            unit="Mbps",
            detail=f"{ratio:.1%} of expected; higher is better",
        )
    ]


def _metric_evm(record: TestRecord, thresholds: Thresholds) -> list[MetricResult]:
    expected = record.expected_evm_pct
    measured = record.measured_evm_pct
    if expected is None or measured is None:
        return []
    ratio = measured / expected if expected else float("inf")
    status = "pass" if ratio <= thresholds.evm_ratio else "fail"
    return [
        MetricResult(
            name="evm",
            expected=expected,
            measured=measured,
            status=status,
            delta=measured - expected,
            unit="%",
            detail=f"{ratio:.1%} of expected limit; lower is better",
        )
    ]


def _metric_rsrp(record: TestRecord, thresholds: Thresholds) -> list[MetricResult]:
    expected = record.expected_rsrp_dbm
    measured = record.measured_rsrp_dbm
    if expected is None or measured is None:
        return []
    delta = measured - expected
    status = "pass" if delta >= -thresholds.rsrp_margin_db else "warn"
    return [
        MetricResult(
            name="rsrp",
            expected=expected,
            measured=measured,
            status=status,
            delta=delta,
            unit="dBm",
            detail=f"{delta:+.2f} dB versus expected; higher is better",
        )
    ]


def _detect_trends(records: list[TestRecord], thresholds: Thresholds) -> list[TrendAnomaly]:
    grouped: dict[tuple[str, str, str], list[TestRecord]] = defaultdict(list)
    for record in records:
        grouped[record.group_key].append(record)

    anomalies: list[TrendAnomaly] = []
    for group, group_records in grouped.items():
        if len(group_records) < thresholds.trend_window:
            continue
        window = group_records[-thresholds.trend_window :]
        anomalies.extend(_trend_for_metric(group, window, "sensitivity", thresholds))
        anomalies.extend(_trend_for_metric(group, window, "throughput", thresholds))
        anomalies.extend(_trend_for_metric(group, window, "evm", thresholds))
        anomalies.extend(_trend_for_metric(group, window, "rsrp", thresholds))
    return anomalies


def _trend_for_metric(
    group: tuple[str, str, str],
    records: list[TestRecord],
    metric: str,
    thresholds: Thresholds,
) -> list[TrendAnomaly]:
    values = [_metric_value(record, metric) for record in records]
    if any(value is None for value in values):
        return []
    series = [float(value) for value in values if value is not None]
    first = series[0]
    last = series[-1]
    previous_mean = mean(series[:-1])
    ids = [record.test_id for record in records]

    if metric == "sensitivity":
        degraded = last - previous_mean > thresholds.trend_sensitivity_db
        monotonic = _monotonic_increasing(series)
        detail = f"sensitivity drifted from {first:.2f} to {last:.2f} dBm"
    elif metric == "throughput":
        degraded = previous_mean > 0 and (previous_mean - last) / previous_mean > thresholds.trend_throughput_ratio
        monotonic = _monotonic_decreasing(series)
        detail = f"throughput moved from {first:.2f} to {last:.2f} Mbps"
    elif metric == "evm":
        degraded = previous_mean > 0 and (last - previous_mean) / previous_mean > thresholds.trend_evm_ratio
        monotonic = _monotonic_increasing(series)
        detail = f"EVM moved from {first:.2f}% to {last:.2f}%"
    else:
        degraded = previous_mean - last > thresholds.trend_rsrp_db
        monotonic = _monotonic_decreasing(series)
        detail = f"RSRP moved from {first:.2f} to {last:.2f} dBm"

    if not degraded and not monotonic:
        return []

    severity = "high" if degraded else "medium"
    return [
        TrendAnomaly(
            group=group,
            metric=metric,
            severity=severity,
            detail=detail,
            affected_test_ids=ids,
        )
    ]


def _metric_value(record: TestRecord, metric: str) -> float | None:
    return {
        "sensitivity": record.measured_sensitivity_dbm,
        "throughput": record.measured_throughput_mbps,
        "evm": record.measured_evm_pct,
        "rsrp": record.measured_rsrp_dbm,
    }[metric]


def _monotonic_increasing(values: list[float]) -> bool:
    return all(left < right for left, right in zip(values, values[1:]))


def _monotonic_decreasing(values: list[float]) -> bool:
    return all(left > right for left, right in zip(values, values[1:]))


def _recommend_next_steps(record: TestRecord, metrics: list[MetricResult]) -> list[str]:
    recommendations: list[str] = []
    failed_metrics = {metric.name for metric in metrics if metric.status != "pass"}

    if "sensitivity" in failed_metrics:
        recommendations.append(
            "Run a receiver sensitivity sweep around the failing point with 0.5 dB input power steps."
        )
        recommendations.append("Check cable loss, attenuator calibration, and CMW100 path compensation.")
    if "throughput" in failed_metrics:
        recommendations.append(
            "Repeat throughput with fixed MCS, stable BLER target, and captured scheduler/OAI logs."
        )
    if "evm" in failed_metrics or "rsrp" in failed_metrics:
        recommendations.append(
            "Capture signal quality at low/mid/high channel and compare PA, LO, and clock reference settings."
        )
    if record.temperature_c is not None and abs(record.temperature_c - 25.0) >= 15.0:
        recommendations.append("Re-run at 25 C as a control point before widening temperature coverage.")
    if not recommendations:
        recommendations.append("Advance to the next band/channel corner or reduce step size near the pass margin.")
    return recommendations
