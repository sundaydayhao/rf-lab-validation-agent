# RF Lab Validation Report

- Generated: 2026-07-30T15:08:15+08:00
- Overall status: **FAIL**
- Test cases: 4
- Trend anomalies: 4

## Executive Summary

Pass: 3, Warn: 0, Fail: 1.
Trend anomalies indicate possible drift and should be confirmed before expanding coverage.

## Test Results

| Test ID | RAT | Band | Channel | Status | Score | Issue | Key Metrics |
| --- | --- | --- | --- | --- | ---: | --- | --- |
| RX-001 | NR | n78 | 633334 | PASS | 100 |  | sensitivity: -97.2dBm (pass, -1.20 dB versus expected; lower is better)<br>throughput: 710Mbps (pass, 98.6% of expected; higher is better)<br>evm: 3.1% (pass, 88.6% of expected limit; lower is better)<br>rsrp: -79.5dBm (pass, +0.50 dB versus expected; higher is better) |
| RX-002 | NR | n78 | 633334 | PASS | 100 |  | sensitivity: -95.4dBm (pass, +0.60 dB versus expected; lower is better)<br>throughput: 706Mbps (pass, 98.1% of expected; higher is better)<br>evm: 3.4% (pass, 97.1% of expected limit; lower is better)<br>rsrp: -80.1dBm (pass, -0.10 dB versus expected; higher is better) |
| RX-003 | NR | n78 | 633334 | FAIL | 15 | [RF-128](https://gitee.com/zhanghaogit/rf-lab-validation-agent/issues/RF-128) | sensitivity: -93.8dBm (fail, +2.20 dB versus expected; lower is better)<br>throughput: 640Mbps (fail, 88.9% of expected; higher is better)<br>evm: 4.2% (fail, 120.0% of expected limit; lower is better)<br>rsrp: -83dBm (warn, -3.00 dB versus expected; higher is better) |
| RX-004 | LTE | B3 | 1575 | PASS | 100 |  | sensitivity: -104.5dBm (pass, -0.50 dB versus expected; lower is better)<br>throughput: 142Mbps (pass, 97.9% of expected; higher is better)<br>evm: 7.5% (pass, 93.8% of expected limit; lower is better)<br>rsrp: -84.2dBm (pass, +0.80 dB versus expected; higher is better) |

## Trend Anomalies

| Group | Metric | Severity | Detail | Tests |
| --- | --- | --- | --- | --- |
| NR/n78/633334 | sensitivity | HIGH | sensitivity drifted from -97.20 to -93.80 dBm | RX-001, RX-002, RX-003 |
| NR/n78/633334 | throughput | MEDIUM | throughput moved from 710.00 to 640.00 Mbps | RX-001, RX-002, RX-003 |
| NR/n78/633334 | evm | HIGH | EVM moved from 3.10% to 4.20% | RX-001, RX-002, RX-003 |
| NR/n78/633334 | rsrp | HIGH | RSRP moved from -79.50 to -83.00 dBm | RX-001, RX-002, RX-003 |

## Recommended Next Tests

### RX-003
- Run a receiver sensitivity sweep around the failing point with 0.5 dB input power steps.
- Check cable loss, attenuator calibration, and CMW100 path compensation.
- Repeat throughput with fixed MCS, stable BLER target, and captured scheduler/OAI logs.
- Capture signal quality at low/mid/high channel and compare PA, LO, and clock reference settings.
- Re-run at 25 C as a control point before widening temperature coverage.
