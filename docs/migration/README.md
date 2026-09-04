# SLiCAP 5.2.1 迁移记录

## 目标

本目录记录从旧版 SLiCAP 4.0.8 原型迁移到 5.2.1 的事实、决策、测试结果和已知
限制。任何版本差异都应先在适配层消化，再暴露给界面和 SFG 算法。

## 当前里程碑

| 里程碑 | 状态 | 结果 |
|---|---|---|
| M0 冻结旧基线 | 完成 | 旧环境保留，算法 `52 passed`，建立本地 tag |
| M1 隔离环境/仓库 | 完成 | Python 3.12、SLiCAP 5.2.1、新功能分支 |
| M2 SLiCAP 适配层 | 完成首版 | 公共数值 API + 版本检查 + 独立任务目录 |
| M3 参数系统 | 完成首版 | 来源追踪、工程后缀、严格模式、版本化默认值 |
| M4 Web Schematic | 官方核心已接入 | 官方 SVG/引脚、junction、命名网络和原生 JSON |
| M5 FastAPI | 完成首版 | 转换、任务队列、结果和制品接口 |
| M6 两条分析主线 | 已接通 | `demo_2_numeric` 数值与 SFG wheel 端到端通过 |
| M7 前端集成 | 进行中 | 官方 headless CLI 已成为默认 `.cir` 导出路径 |

## 记录文件

- `architecture.md`：分层边界与数据流。
- `parameter-policy.md`：参数解析、默认值和数值完整性规则。
- `compatibility-matrix.md`：4.0.8 与 5.2.1 兼容性结论。
- `baseline-2026-09-04.json`：机器可读的当前验证快照。
- `official-web-schematic.md`：官方 Core 与浏览器画布的职责边界。

## 下一步

1. 用浏览器完成官方 SVG、旋转/翻转、junction 和网表错误的人工作流验收。
2. 将现有受控源、MOS、BJT CLI fixture 扩展为官方 GUI 保存后的往返 fixture。
3. 为项目子电路 symbol bundle 设计多文件上传和下载。
4. 将旧 Gradio 中的 HTML 结果抓取逐步替换为 FastAPI 结构化结果。
