# 本地系统架构

## 数据流

所有输入先转换为 `CircuitDocument`。它保存规范化网表、参数来源、诊断和输入来源，
因此数值分析与符号分析不需要知道电路最初来自图片、文本还是 schematic。

```text
Input adapters
  -> official-compatible .slicap_sch / raw netlist
  -> CircuitDocument
  -> SLiCAP521Adapter
       -> public SLiCAP numeric analyses
       -> versioned sfg-prototype wheel
  -> AnalysisJob + artifacts
  -> FastAPI -> React / Gradio
```

## 并发边界

SLiCAP 当前具有解析器和项目配置的全局状态。`SLiCAP521Adapter` 使用进程内
`RLock` 串行化 SLiCAP 调用，并为每个任务创建独立工作目录。这个设计保证本地正确性；
未来服务器多进程部署应把每个分析放入独立 worker 进程，而不是移除锁。

## 算法边界

`sfg-prototype` 是独立发布物。前端只依赖其公开入口和报告函数，不复制源码，也不
直接导入旧 Conda `site-packages` 中的开发文件。这样可以单独升级算法、固定版本并
在出现问题时回滚 wheel。

## Schematic 边界

官方 `.slicap_sch` 是 schematic 的规范持久化格式。React 画布使用
`SchematicDocument` 作为临时视图模型，但导出和分析前必须转换为官方 JSON。
器件 SVG、引脚坐标、参数和引用来自 SLiCAP `SymbolLibrary`，`.cir` 由
`python -m SLiCAP.schematic.cli netlist` 生成。未知官方字段按只读 passthrough
保留，避免往返保存时无声丢失未来版本数据。

PySide6 只存在于服务端：官方 CLI 在 offscreen `QApplication` 中加载 scene 并
执行连通性与网表生成。浏览器不会运行或远程显示 Qt 桌面窗口。
