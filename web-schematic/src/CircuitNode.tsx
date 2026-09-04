import { Handle, Position, type Node, type NodeProps } from '@xyflow/react'
import type { CSSProperties } from 'react'
import type { DeviceDefinition, SchematicComponent } from './types'

export type CircuitNodeData = {
  component: SchematicComponent
  definition: DeviceDefinition
}

export type CircuitFlowNode = Node<CircuitNodeData, 'circuit'>

const pinStyle = (index: number, count: number): CSSProperties => {
  if (count === 1) return { left: '50%', top: 0 }
  if (count === 2) return index === 0 ? { left: '50%', top: 0 } : { left: '50%', top: '100%' }
  const fourPin = [
    { left: '72%', top: 0 },
    { left: '72%', top: '100%' },
    { left: 0, top: '25%' },
    { left: 0, top: '75%' },
  ]
  return fourPin[index] ?? { left: index % 2 ? '100%' : 0, top: `${30 + index * 12}%` }
}

export function CircuitNode({ data, selected }: NodeProps<CircuitFlowNode>) {
  const { component, definition } = data
  const value = component.parameters.value
  return (
    <div className={`circuit-node ${selected ? 'selected' : ''} device-${component.device.toLowerCase()}`}>
      {definition.pins.map((pin, index) => (
        <Handle
          className="circuit-pin"
          id={pin}
          key={pin}
          position={index < 2 ? (index === 0 ? Position.Top : Position.Bottom) : Position.Left}
          style={pinStyle(index, definition.pins.length)}
          title={pin}
          type="source"
        />
      ))}
      <span className="node-refdes">{component.refdes}</span>
      <span className="node-symbol">{component.device}</span>
      {value && <span className={`node-value ${value === '?' ? 'missing' : ''}`}>{value}</span>}
    </div>
  )
}
