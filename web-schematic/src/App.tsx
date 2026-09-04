import { useEffect, useState } from 'react'
import {
  addEdge,
  Background,
  ConnectionMode,
  Controls,
  MiniMap,
  ReactFlow,
  useEdgesState,
  useNodesState,
  type Connection,
  type Edge,
} from '@xyflow/react'
import { convertSchematic, fetchCatalog, getAnalysis, importSlicapSchematic, submitAnalysis } from './api'
import { CircuitNode, type CircuitFlowNode } from './CircuitNode'
import type { AnalysisJob, DeviceDefinition, Diagnostic, SchematicComponent, SchematicDocument } from './types'

const nodeTypes = { circuit: CircuitNode }

const emptyDocument = (): SchematicDocument => ({
  schema_version: '1.0',
  title: 'Untitled circuit',
  components: [],
  wires: [],
  parameters: {},
  analysis: { source: null, detector: null, lgref: null },
  passthrough: {},
})

function parseParameters(text: string): Record<string, string> {
  const result: Record<string, string> = {}
  for (const line of text.split('\n')) {
    const [name, ...parts] = line.split('=')
    if (name.trim() && parts.length) result[name.trim()] = parts.join('=').trim()
  }
  return result
}

function parameterText(parameters: Record<string, string>): string {
  return Object.entries(parameters).map(([name, value]) => `${name}=${value}`).join('\n')
}

function download(name: string, content: string, type: string) {
  const url = URL.createObjectURL(new Blob([content], { type }))
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = name
  anchor.click()
  URL.revokeObjectURL(url)
}

function pinsFor(component: SchematicComponent, definition: DeviceDefinition): string[] {
  if (component.device !== 'X') return definition.pins
  const pins = component.properties.pins
  return Array.isArray(pins) ? pins.filter((pin): pin is string => typeof pin === 'string' && pin.length > 0) : []
}

function definitionFor(component: SchematicComponent, catalog: Record<string, DeviceDefinition>): DeviceDefinition {
  const definition = catalog[component.device]
  if (!definition) throw new Error(`器件目录中不存在 ${component.device}`)
  return component.device === 'X' ? { ...definition, pins: pinsFor(component, definition) } : definition
}

export default function App() {
  const [catalog, setCatalog] = useState<Record<string, DeviceDefinition>>({})
  const [nodes, setNodes, onNodesChange] = useNodesState<CircuitFlowNode>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])
  const [document, setDocument] = useState<SchematicDocument>(emptyDocument)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [diagnostics, setDiagnostics] = useState<Diagnostic[]>([])
  const [netlist, setNetlist] = useState('')
  const [job, setJob] = useState<AnalysisJob | null>(null)
  const [symbolic, setSymbolic] = useState(false)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('正在加载 SLiCAP 5.2.1 器件目录...')

  useEffect(() => {
    fetchCatalog()
      .then((items) => { setCatalog(items); setMessage('器件目录已就绪') })
      .catch((error: Error) => setMessage(`API 连接失败: ${error.message}`))
  }, [])

  useEffect(() => {
    if (!job || !['queued', 'running'].includes(job.status)) return
    const timer = window.setInterval(() => {
      getAnalysis(job.id).then(setJob).catch((error: Error) => setMessage(error.message))
    }, 1200)
    return () => window.clearInterval(timer)
  }, [job])

  const selected = nodes.find((node) => node.id === selectedId)

  const buildDocument = (): SchematicDocument => ({
    ...document,
    components: nodes.map((node) => ({ ...node.data.component, position: node.position })),
    wires: edges.map((edge, index) => ({
      id: edge.id || `W${index + 1}`,
      source: { component_id: edge.source, pin_id: edge.sourceHandle ?? '?' },
      target: { component_id: edge.target, pin_id: edge.targetHandle ?? '?' },
      waypoints: [],
      net_name: typeof edge.label === 'string' && edge.label ? edge.label : null,
    })),
  })

  const addComponent = (device: string) => {
    const definition = catalog[device]
    if (!definition) return
    const prefix = definition.prefix ?? device.slice(0, 1)
    const usedRefdes = new Set(nodes.map((node) => node.data.component.refdes))
    let sequence = 1
    while (usedRefdes.has(`${prefix || device}${sequence}`)) sequence += 1
    const id = `${prefix || device}${sequence}-${crypto.randomUUID().slice(0, 6)}`
    const refdes = definition.prefix ? `${definition.prefix}${sequence}` : id
    const properties = device === 'GROUND'
      ? { name: '0' }
      : device === 'PORT'
        ? { name: refdes }
        : device === 'X'
          ? { pins: ['p1', 'p2'] }
          : {}
    const component: SchematicComponent = {
      id,
      refdes,
      device,
      position: { x: 120 + (nodes.length % 4) * 170, y: 100 + Math.floor(nodes.length / 4) * 150 },
      rotation: 0,
      model: definition.model,
      parameters: device === 'GROUND' || device === 'PORT' ? {} : { ...definition.defaults },
      control_ref: null,
      properties,
      passthrough: {},
    }
    setNodes((current) => [...current, {
      id,
      type: 'circuit',
      position: component.position,
      data: { component, definition: definitionFor(component, catalog) },
    }])
    setSelectedId(id)
  }

  const connect = (connection: Connection) => {
    if (!connection.sourceHandle || !connection.targetHandle) return
    setEdges((current) => addEdge({
      ...connection,
      id: `W-${crypto.randomUUID()}`,
      type: 'smoothstep',
    }, current))
  }

  const updateSelected = (patch: Partial<SchematicComponent>) => {
    if (!selectedId) return
    setNodes((current) => current.map((node) => {
      if (node.id !== selectedId) return node
      const component = { ...node.data.component, ...patch }
      return { ...node, data: { component, definition: definitionFor(component, catalog) } }
    }))
  }

  const exportFormat = async (format: 'cir' | 'internal_json' | 'slicap_sch') => {
    setBusy(true)
    try {
      const current = buildDocument()
      const response = await convertSchematic(current, format)
      setDiagnostics(response.diagnostics)
      if (format === 'cir' && response.netlist_text) {
        setNetlist(response.netlist_text)
        download('circuit.cir', response.netlist_text, 'text/plain')
      } else if (format === 'slicap_sch' && response.slicap_schematic) {
        download('circuit.slicap_sch', JSON.stringify(response.slicap_schematic, null, 2), 'application/json')
      } else {
        download('circuit.isaca.json', JSON.stringify(current, null, 2), 'application/json')
      }
      setMessage(`已生成 ${format}`)
    } catch (error) {
      setMessage((error as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const runAnalysis = async () => {
    setBusy(true)
    try {
      const response = await convertSchematic(buildDocument(), 'cir')
      setDiagnostics(response.diagnostics)
      setNetlist(response.netlist_text ?? '')
      if (response.diagnostics.some((item) => item.level === 'error')) throw new Error('请先修复电路连接错误。')
      const submitted = await submitAnalysis(response.netlist_text ?? '', symbolic)
      setJob(submitted)
      setMessage(`任务 ${submitted.id.slice(0, 8)} 已提交`)
    } catch (error) {
      setMessage((error as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const importNative = async (file: File) => {
    try {
      if (Object.keys(catalog).length === 0) throw new Error('器件目录尚未加载完成')
      const raw = JSON.parse(await file.text()) as Record<string, unknown>
      const imported = await importSlicapSchematic(raw)
      setDocument(imported)
      setNodes(imported.components.map((component) => ({
        id: component.id,
        type: 'circuit',
        position: component.position,
        data: { component, definition: definitionFor(component, catalog) },
      })))
      setEdges(imported.wires.map((wire) => ({
        id: wire.id,
        source: wire.source.component_id,
        sourceHandle: wire.source.pin_id,
        target: wire.target.component_id,
        targetHandle: wire.target.pin_id,
        label: wire.net_name,
        type: 'smoothstep',
      })))
      setMessage('已导入 SLiCAP schematic')
    } catch (error) {
      setMessage(`导入失败: ${(error as Error).message}`)
    }
  }

  return (
    <main className="app-shell">
      <header>
        <div><span className="eyebrow">SLiCAP 5.2.1 + SFG</span><h1>Analog Circuit Workbench</h1></div>
        <div className="status"><span className="status-dot" />{message}</div>
      </header>
      <section className="workspace">
        <aside className="palette panel">
          <h2>器件</h2>
          <p>放置后从圆形引脚拖动连线。</p>
          <div className="device-grid">
            {Object.entries(catalog).map(([key, item]) => (
              <button key={key} onClick={() => addComponent(key)}><strong>{key}</strong><span>{item.label}</span></button>
            ))}
          </div>
          <label className="file-button">导入 .slicap_sch<input type="file" accept=".slicap_sch,.json" onChange={(event) => event.target.files?.[0] && importNative(event.target.files[0])} /></label>
        </aside>
        <section className="canvas panel">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={connect}
            onNodeClick={(_, node) => setSelectedId(node.id)}
            connectionMode={ConnectionMode.Loose}
            fitView
            snapToGrid
            snapGrid={[10, 10]}
          >
            <Background gap={20} size={1} color="#cbd5df" />
            <MiniMap pannable zoomable />
            <Controls />
          </ReactFlow>
        </section>
        <aside className="inspector panel">
          <h2>电路定义</h2>
          <label>标题<input value={document.title} onChange={(event) => setDocument({ ...document, title: event.target.value })} /></label>
          {selected ? <>
            <h3>选中器件</h3>
            <label>RefDes<input value={selected.data.component.refdes} onChange={(event) => updateSelected({ refdes: event.target.value })} /></label>
            <label>Model<input value={selected.data.component.model ?? ''} onChange={(event) => updateSelected({ model: event.target.value || null })} /></label>
            <label>Rotation
              <select value={selected.data.component.rotation} onChange={(event) => updateSelected({ rotation: Number(event.target.value) })}>
                <option value={0}>0 degrees</option><option value={90}>90 degrees</option><option value={180}>180 degrees</option><option value={270}>270 degrees</option>
              </select>
            </label>
            {selected.data.component.device === 'X' && <label>端口顺序（逗号分隔）<input
              value={pinsFor(selected.data.component, selected.data.definition).join(',')}
              onChange={(event) => updateSelected({
                properties: {
                  ...selected.data.component.properties,
                  pins: event.target.value.split(',').map((pin) => pin.trim()).filter(Boolean),
                },
              })}
            /></label>}
            {Object.entries(selected.data.component.parameters).map(([name, value]) => (
              <label key={name}>{name}<input className={value === '?' ? 'invalid' : ''} value={value} onChange={(event) => updateSelected({ parameters: { ...selected.data.component.parameters, [name]: event.target.value } })} /></label>
            ))}
            {(selected.data.component.device === 'F' || selected.data.component.device === 'H') && <label>控制支路<input value={selected.data.component.control_ref ?? ''} onChange={(event) => updateSelected({ control_ref: event.target.value || null })} /></label>}
            <button className="danger" onClick={() => { setNodes((items) => items.filter((node) => node.id !== selectedId)); setEdges((items) => items.filter((edge) => edge.source !== selectedId && edge.target !== selectedId)); setSelectedId(null) }}>删除器件</button>
          </> : <p className="muted">选择画布中的器件以编辑参数。</p>}
          <h3>分析端口</h3>
          <label>Source<input placeholder="V1" value={document.analysis.source ?? ''} onChange={(event) => setDocument({ ...document, analysis: { ...document.analysis, source: event.target.value || null } })} /></label>
          <label>Detector<input placeholder="V_out" value={document.analysis.detector ?? ''} onChange={(event) => setDocument({ ...document, analysis: { ...document.analysis, detector: event.target.value || null } })} /></label>
          <h3>.param</h3>
          <textarea rows={6} placeholder={'R=1k\nC=1u'} value={parameterText(document.parameters)} onChange={(event) => setDocument({ ...document, parameters: parseParameters(event.target.value) })} />
        </aside>
      </section>
      <section className="bottom-grid">
        <article className="panel actions">
          <h2>转换与分析</h2>
          <div className="button-row">
            <button disabled={busy} onClick={() => exportFormat('cir')}>导出 .cir</button>
            <button disabled={busy} onClick={() => exportFormat('slicap_sch')}>导出 .slicap_sch</button>
            <button disabled={busy} onClick={() => exportFormat('internal_json')}>保存工程 JSON</button>
          </div>
          <label className="check"><input type="checkbox" checked={symbolic} onChange={(event) => setSymbolic(event.target.checked)} />运行 SFG 分频段符号化简</label>
          <button className="primary" disabled={busy || nodes.length === 0} onClick={runAnalysis}>提交分析</button>
          <div className="diagnostics">
            {diagnostics.map((item, index) => <p className={item.level} key={`${item.code}-${index}`}><strong>{item.code}</strong> {item.message}</p>)}
          </div>
        </article>
        <article className="panel output"><h2>规范化网表</h2><pre>{netlist || '导出或提交分析后显示 .cir'}</pre></article>
        <article className="panel output"><h2>任务结果</h2><pre>{job ? JSON.stringify(job, null, 2) : '尚未提交任务'}</pre></article>
      </section>
    </main>
  )
}
