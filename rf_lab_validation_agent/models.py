from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class TestRecord:
    test_id: str
    timestamp: datetime
    band: str
    rat: str
    channel: str
    temperature_c: float | None = None
    expected_sensitivity_dbm: float | None = None
    measured_sensitivity_dbm: float | None = None
    expected_throughput_mbps: float | None = None
    measured_throughput_mbps: float | None = None
    expected_evm_pct: float | None = None
    measured_evm_pct: float | None = None
    expected_rsrp_dbm: float | None = None
    measured_rsrp_dbm: float | None = None
    issue_id: str | None = None
    notes: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def group_key(self) -> tuple[str, str, str]:
        return (self.rat, self.band, self.channel)


@dataclass(frozen=True)
class Thresholds:
    sensitivity_margin_db: float = 1.5
    throughput_ratio: float = 0.95
    evm_ratio: float = 1.10
    rsrp_margin_db: float = 2.0
    trend_window: int = 3
    trend_sensitivity_db: float = 1.0
    trend_throughput_ratio: float = 0.10
    trend_evm_ratio: float = 0.15
    trend_rsrp_db: float = 2.0


@dataclass(frozen=True)
class MetricResult:
    name: str
    expected: float
    measured: float
    status: str
    delta: float
    unit: str
    detail: str


@dataclass(frozen=True)
class RecordAnalysis:
    record: TestRecord
    metrics: list[MetricResult]
    status: str
    score: int
    recommendations: list[str]


@dataclass(frozen=True)
class TrendAnomaly:
    group: tuple[str, str, str]
    metric: str
    severity: str
    detail: str
    affected_test_ids: list[str]


@dataclass(frozen=True)
class AnalysisReport:
    generated_at: datetime
    records: list[RecordAnalysis]
    anomalies: list[TrendAnomaly]
    issue_base_url: str | None = None

    @property
    def overall_status(self) -> str:
        if any(record.status == "fail" for record in self.records):
            return "fail"
        if self.anomalies or any(record.status == "warn" for record in self.records):
            return "warn"
        return "pass"
