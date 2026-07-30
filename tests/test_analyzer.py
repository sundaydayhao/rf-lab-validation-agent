from datetime import datetime
import unittest

from rf_lab_validation_agent.analyzer import analyze_records
from rf_lab_validation_agent.models import TestRecord


class AnalyzerTest(unittest.TestCase):
    def test_flags_failures_and_trends(self) -> None:
        records = [
            TestRecord("t1", datetime.fromisoformat("2026-07-20T10:00:00+08:00"), "n78", "NR", "1", measured_sensitivity_dbm=-97, expected_sensitivity_dbm=-96, measured_throughput_mbps=720, expected_throughput_mbps=720),
            TestRecord("t2", datetime.fromisoformat("2026-07-21T10:00:00+08:00"), "n78", "NR", "1", measured_sensitivity_dbm=-95, expected_sensitivity_dbm=-96, measured_throughput_mbps=690, expected_throughput_mbps=720),
            TestRecord("t3", datetime.fromisoformat("2026-07-22T10:00:00+08:00"), "n78", "NR", "1", measured_sensitivity_dbm=-93, expected_sensitivity_dbm=-96, measured_throughput_mbps=620, expected_throughput_mbps=720),
        ]

        report = analyze_records(records)

        self.assertEqual(report.overall_status, "fail")
        self.assertGreaterEqual(len(report.anomalies), 1)
        self.assertEqual(report.records[-1].status, "fail")
        self.assertTrue(any("sensitivity sweep" in item for item in report.records[-1].recommendations))


if __name__ == "__main__":
    unittest.main()
