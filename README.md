# 智能符号化模拟电路分析系统

本分支用于在本地集成 **SLiCAP 5.2.1**、Web 原理图编辑器和独立的 SFG
符号化简算法。系统把不同输入统一为规范化 `.cir` 网表，再分别执行数值分析与
分频段符号化简。

```text
图片识别 IR（接口预留） ─┐
手写/上传 .cir ──────────┼─> CircuitDocument -> SLiCAP 5.2.1 数值分析
Web Schematic ───────────┤                    -> SFG 分频段符号化简
官方 .slicap_sch ────────┘
```

## 当前能力

| 模块 | 当前状态 |
|---|---|
| `.cir` 规范化与严格参数解析 | 已实现；支持 `k/m/u/n/p` 和科学计数法 |
| SLiCAP 5.2.1 数值分析 | 已实现；使用 `makeCircuit/doLaplace/doPZ/doMatrix/doNoise` |
| SFG 算法接入 | 已实现；安装独立 `sfg-prototype` wheel 后可调用 |
| Web Schematic | 已实现首版；支持 R/C/L、独立源、四种受控源、MOS、QV BJT、端口和地 |
| `.slicap_sch` 双向转换 | 核心器件已实现，并由官方 SLiCAP CLI 往返测试验证 |
| `X` 子电路块 | 可编辑端口并导出 `.cir`；原生 `.slicap_sch` 符号导出暂不支持 |
| 旧 Gradio 页面 | 保留，并嵌入 Web Schematic；固定使用 Gradio 5.x |
| 图片识别 | 本阶段只保留 `netLens IR -> CircuitDocument` 边界，不加载视觉权重 |

## 设计原则

- 旧 `slicap_env` 与 SLiCAP 4.0.8 不原地升级，新系统使用隔离的
  `slicap5_env`。
- SLiCAP 调用集中在 `backend/isaca_api/slicap_adapter.py`，界面代码不直接依赖
  SLiCAP 私有全局状态。
- SFG 算法保留在独立仓库，通过版本化 wheel 安装；本仓库不复制算法源码。
- 数值参数默认采用严格模式，未赋值参数不会被静默替换为 `1`。
- 每个分析任务有独立目录，保存输入、版本、诊断和结果制品。

## 目录结构

```text
backend/isaca_api/                 FastAPI、统一数据模型、SLiCAP 适配层
backend/tests/                     后端、参数、schematic 与官方 CLI 测试
web-schematic/                     React + TypeScript + @xyflow/react 画布
SLiCAP/                            兼容保留的旧 Gradio 页面
scripts/start-dev.ps1              本地三服务启动器
scripts/check-environment.ps1      环境、测试和前端构建检查
scripts/run-circuit-regression.py  60 个测试网表的迁移回归
docs/migration/                    升级记录与架构决策
```

## 环境安装

推荐在 PowerShell 中执行：

```powershell
conda create -n slicap5_env python=3.12 -y
conda activate slicap5_env
pip install "SLiCAP==5.2.1"
pip install -e ".[test,ui]"
cd web-schematic
npm install
cd ..
```

SFG 算法 wheel 由独立仓库构建：

```powershell
cd C:\pr\learning\college\else\sitp_2\github\Intelligent-Symbolic-Analog-Circuit-Analyzer
python -m build sfg_prototype
pip install --force-reinstall --no-deps .\sfg_prototype\dist\sfg_prototype-0.2.0-py3-none-any.whl
```

## 本地运行

```powershell
conda activate slicap5_env
cd C:\pr\learning\college\else\sitp_2\github\Analog-Circuit-Analyzer-next
.\start-local.ps1
```

默认地址：

- Web Schematic：`http://127.0.0.1:5173`
- FastAPI 文档：`http://127.0.0.1:8000/docs`
- Gradio 页面：`http://127.0.0.1:7860`

只启动 Web Schematic 与 API：

```powershell
.\scripts\start-dev.ps1 -NoGradio
```

## 参数策略

参数优先级为：

```text
本次用户覆盖 > 网表 .param > 元件行直接数值 > 用户显式启用的 SLiCAP 默认值
```

符号分析允许保留未赋值符号；数值分析、根聚类和误差评估要求相关参数具有数值。
“使用 SLiCAP 默认值”必须显式开启，结果中会记录来源和版本。SLiCAP 5.2.1
的若干基础器件默认值为 0，它们是软件缺省值，不等同于合理的物理设计值。

## API

| 方法 | 路径 | 作用 |
|---|---|---|
| `GET` | `/api/v1/catalog/devices` | 5.2.1 器件、引脚和默认参数目录 |
| `POST` | `/api/v1/circuits/normalize` | 规范化文本或 `.cir` 网表 |
| `POST` | `/api/v1/schematics/convert` | 内部 JSON、`.slicap_sch`、`.cir` 转换 |
| `POST` | `/api/v1/analyses` | 提交数值或 SFG 分析任务 |
| `GET` | `/api/v1/analyses/{job_id}` | 查询任务状态和结构化结果 |
| `GET` | `/api/v1/analyses/{job_id}/artifacts/{name}` | 获取网表和报告制品 |

## 验证

```powershell
.\scripts\check-environment.ps1
```

当前已验证：

- SFG 算法在 SLiCAP 4.0.8 与 5.2.1 下均为 `52 passed`。
- 本仓库后端为 `16 passed`。
- React/TypeScript 生产构建通过。
- 20 个显式数值测试在 SLiCAP 4.0.8 与 5.2.1 间全部通过：传递函数均符号
  等价，采样最大相对误差约 `5.39e-16`，极点和零点最大相对差为 0。
- `demo_2_numeric` 可从 API 完成 SLiCAP 数值分析与 4 个 SFG 子频段化简，
  自动生成 `simplification.md`、`subrange_simplification.md`、
  `operation_ranking.md`、`error_trace.md` 和 `root_localization.md`。

运行 60 个测试网表的结构回归：

```powershell
python .\scripts\run-circuit-regression.py `
  --library-root "C:\pr\learning\college\else\sitp_2\测试样例\测试样例合集" `
  --output .\runs\regression\slicap521-structure.json
```

加上 `--numeric` 时，只对数值参数完整的网表执行 `doLaplace/doPZ`；其余案例仍会
记录结构解析结果和缺失参数，不会自动填 `1`。

首次完整回归中，20 个参数完整案例通过 `doLaplace/doPZ`，24 个符号案例通过结构
展平，另有 16 个失败。16 个失败文件均为多管目录中的旧草稿，
使用了未定义 PMOS 模型 `P`；case2 草稿还使用了非法电流源格式 `DC`。其对应的
“审查修正版”均通过，详情见迁移回归报告。该结果用于区分数据版本，不能简化成
“44/60 电路受支持”。

## 已知边界

- SLiCAP 5.2.1 GUI 仍在发展，本分支固定版本，不跟随 `latest`。
- Web `X` 块可生成 SLiCAP 网表，但尚不能创建带自定义符号库的原生
  `.slicap_sch` 元件。
- SFG 算法对 `demo_2_numeric` 已能生成分频段解释；部分高阶局部闭环根仍可能
  返回较长表达式或 `outside_error_limit`，不能描述为已达到任意复杂电路的论文级
  最简形式。
- 旧 Gradio 结果展示仍保留部分旧实现；新功能应优先通过 FastAPI 结构化结果读取，
  后续再逐页替换旧逻辑。
- 视觉模型和多用户服务器部署不在本阶段验收范围内。

迁移细节见 [docs/migration/README.md](docs/migration/README.md)。
