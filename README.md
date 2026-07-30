# RF Lab Validation Agent

面向 RF 实验室、CMW100、USRP/OAI 和外场测试数据的工程自动化 agent。

它可以读取 CSV/JSON 测试结果，自动比较 expected sensitivity、throughput、signal quality，识别异常趋势，生成测试报告，推荐下一轮测试条件，并把测试项关联到 issue tracker。

## 快速开始

```powershell
python -m rf_lab_validation_agent analyze `
  --input sample_data/rf_results.csv `
  --output reports/latest.md `
  --json-output reports/latest.json `
  --issue-base-url https://gitee.com/zhanghaogit/rf-lab-validation-agent/issues
```

命令会返回整体状态。若存在 fail，进程退出码为 2，便于接入 CI。

## 输入字段

必填字段：

- `test_id`
- `timestamp`
- `band`
- `rat`
- `channel`

可选指标字段：

- `expected_sensitivity_dbm`, `measured_sensitivity_dbm`
- `expected_throughput_mbps`, `measured_throughput_mbps`
- `expected_evm_pct`, `measured_evm_pct`
- `expected_rsrp_dbm`, `measured_rsrp_dbm`
- `temperature_c`
- `issue_id`
- `notes`

## 判定逻辑

- Sensitivity：measured 不应比 expected 差超过 `1.5 dB`。
- Throughput：measured 不应低于 expected 的 `95%`。
- EVM：measured 不应超过 expected limit 的 `110%`。
- RSRP：measured 不应比 expected 低超过 `2 dB`。
- Trend：同 RAT/Band/Channel 最近 3 个点出现单调劣化或超过漂移阈值时标记异常。

阈值可通过 CLI 参数覆盖。

## 下一步扩展

- 接 CMW100/仪表导出的 CSV 模板。
- 接 OAI log parser，把 BLER、MCS、SNR、RSRP、EVM 自动抽取为结构化记录。
- 接 Gitee/Jira/GitHub issue API，自动回写报告摘要和附件链接。
- 增加 HTML 报告和趋势图。
