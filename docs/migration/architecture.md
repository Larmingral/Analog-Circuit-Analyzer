# 本地系统架构

## 数据流

所有输入先转换为 `CircuitDocument`。它保存规范化网表、参数来源、诊断和输入来源，
因此数值分析与符号分析不需要知道电路最初来自图片、文本还是 schematic。

```text
Input adapters
  -> SchematicDocument / raw netlist
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

内部 JSON 描述器件、引脚、线、节点名、参数和分析端口；SLiCAP 5.2.1 原生 JSON
适配器负责坐标和官方符号引脚。未知官方字段按只读 passthrough 保留，避免往返保存
时无声丢失未来版本数据。
