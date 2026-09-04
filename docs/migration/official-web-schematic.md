# SLiCAP Core Web Schematic 决策

## 决策

浏览器继续使用 React 与 `@xyflow/react`，但不再自行定义电气元数据。SLiCAP
5.2.1 的 `SymbolLibrary`、`SchematicData` 和 headless CLI 分别作为符号、
持久化格式和网表生成的权威来源。

```text
React view model
  -> official-compatible .slicap_sch
  -> SLiCAP.schematic.cli netlist
  -> normalized .cir
  -> numeric and SFG analysis
```

## PySide6 的位置

PySide6 无法作为 React 组件在浏览器沙箱内运行，但它仍是后端直接依赖。官方
CLI 创建 offscreen `QApplication`、恢复 `QGraphicsScene` 并调用 SLiCAP 自己的
连通性和网表实现。这样既保留普通 Web 交互，也不复制官方电气规则。

## 兼容策略

- 固定 `SLiCAP==5.2.1`，启动时拒绝其他版本。
- 核心器件元数据在运行时从官方 SVG 提取。
- 未支持的官方对象按只读 passthrough 保存。
- 当前内部模型和自定义网表器仅用于兼容与回归对照。
- `VITE_SCHEMATIC_MODE=legacy` 可临时关闭官方 SVG 显示，但不会改变后端官方
  网表生成路径。

## 当前边界

项目子电路的符号位于项目 `lib/` 或 schematic 的 `.symbols` sidecar 中，无法只靠
一个 JSON 文件完整恢复。因此 `X` 的官方原生导出需要后续增加多文件工程制品；
当前不伪造系统 symbol。导线折点可以导入、保留和自动生成，手工拖拽折点仍待实现。
