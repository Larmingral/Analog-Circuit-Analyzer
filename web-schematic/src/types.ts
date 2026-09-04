export type Point = { x: number; y: number }

export type DeviceDefinition = {
  label: string
  description: string
  info: string
  prefix: string | null
  model: string | null
  model_show: boolean
  symbol: string
  symbol_url: string | null
  view_box: { x: number; y: number; width: number; height: number }
  pins: string[]
  pin_positions: Record<string, Point>
  refs: string[]
  defaults: Record<string, string>
  param_display: Record<string, { show_value: boolean; show_name: boolean }>
  show_pinnames: boolean
  slicap_defaults?: Record<string, string>
}

export type SchematicComponent = {
  id: string
  refdes: string
  device: string
  position: Point
  rotation: number
  model: string | null
  parameters: Record<string, string>
  control_ref: string | null
  properties: Record<string, unknown>
  passthrough: Record<string, unknown>
}

export type SchematicWire = {
  id: string
  source: { component_id: string; pin_id: string }
  target: { component_id: string; pin_id: string }
  waypoints: Point[]
  net_name: string | null
}

export type SchematicDocument = {
  schema_version: '1.0'
  title: string
  components: SchematicComponent[]
  wires: SchematicWire[]
  parameters: Record<string, string>
  analysis: { source: string | null; detector: string | null; lgref: string | null }
  passthrough: Record<string, unknown>
}

export type SlicapComponentData = {
  symbol_name: string
  instance_id: string
  x: number
  y: number
  rotation?: number
  h_flip?: boolean
  v_flip?: boolean
  params?: Record<string, string>
  model?: string
  refs?: string[]
  [key: string]: unknown
}

export type SlicapWireData = {
  points: [number, number][]
  net_name?: string | null
  user_net_name?: string | null
  [key: string]: unknown
}

export type SlicapSchematicDocument = {
  components: SlicapComponentData[]
  wires: SlicapWireData[]
  junctions: { x: number; y: number }[]
  parameters: Record<string, unknown>[]
  analysis_items: Record<string, unknown>[]
  model_defs: Record<string, unknown>[]
  properties: Record<string, unknown>
  [key: string]: unknown
}

export type Diagnostic = {
  level: 'info' | 'warning' | 'error'
  code: string
  message: string
  location: string | null
}

export type AnalysisJob = {
  id: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  result: Record<string, unknown> | null
  error: string | null
}
