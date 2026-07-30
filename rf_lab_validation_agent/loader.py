from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from .models import TestRecord


def load_records(path: str | Path) -> list[TestRecord]:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Input file not found: {source}")

    suffix = source.suffix.lower()
    if suffix == ".csv":
        rows = _load_csv(source)
    elif suffix == ".json":
        rows = _load_json(source)
    else:
        raise ValueError("Unsupported input format. Use CSV or JSON.")

    records = [_to_record(row) for row in rows]
    return sorted(records, key=lambda record: record.timestamp)


def _load_csv(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle)


def _load_json(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, dict):
        payload = payload.get("records", [])
    if not isinstance(payload, list):
        raise ValueError("JSON input must be a list or an object with a 'records' list.")
    yield from payload


def _to_record(row: dict[str, Any]) -> TestRecord:
    timestamp_raw = _required(row, "timestamp")
    return TestRecord(
        test_id=str(_required(row, "test_id")),
        timestamp=_parse_timestamp(timestamp_raw),
        band=str(_required(row, "band")),
        rat=str(_required(row, "rat")),
        channel=str(_required(row, "channel")),
        temperature_c=_float_or_none(row.get("temperature_c")),
        expected_sensitivity_dbm=_float_or_none(row.get("expected_sensitivity_dbm")),
        measured_sensitivity_dbm=_float_or_none(row.get("measured_sensitivity_dbm")),
        expected_throughput_mbps=_float_or_none(row.get("expected_throughput_mbps")),
        measured_throughput_mbps=_float_or_none(row.get("measured_throughput_mbps")),
        expected_evm_pct=_float_or_none(row.get("expected_evm_pct")),
        measured_evm_pct=_float_or_none(row.get("measured_evm_pct")),
        expected_rsrp_dbm=_float_or_none(row.get("expected_rsrp_dbm")),
        measured_rsrp_dbm=_float_or_none(row.get("measured_rsrp_dbm")),
        issue_id=_text_or_none(row.get("issue_id")),
        notes=str(row.get("notes") or ""),
        raw=dict(row),
    )


def _required(row: dict[str, Any], key: str) -> Any:
    value = row.get(key)
    if value is None or value == "":
        raise ValueError(f"Missing required field: {key}")
    return value


def _float_or_none(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _text_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Invalid timestamp: {value}") from exc
