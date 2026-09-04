import { Handle, Position, type Node, type NodeProps } from '@xyflow/react'
import type { CSSProperties } from 'react'
import type { DeviceDefinition, Point, SchematicComponent } from './types'

export type CircuitNodeData = {
  component: SchematicComponent
  definition: DeviceDefinition
}

export type CircuitFlowNode = Node<CircuitNodeData, 'circuit'>

function transformedPin(
  pin: Point,
  definition: DeviceDefinition,
  component: SchematicComponent,
): CSSProperties {
  const view = definition.view_box
  const centerX = view.x + view.width / 2
  const centerY = view.y + view.height / 2
  let x = pin.x - centerX
  let y = pin.y - centerY
  if (component.passthrough.h_flip) x = -x
  if (component.passthrough.v_flip) y = -y
  const angle = component.rotation * Math.PI / 180
  const rotatedX = x * Math.cos(angle) - y * Math.sin(angle)
  const rotatedY = x * Math.sin(angle) + y * Math.cos(angle)
  const extent = Math.max(view.width, view.height, 1)
  return {
    left: `${50 + rotatedX / extent * 72}%`,
    top: `${50 + rotatedY / extent * 72}%`,
  }
}

export function CircuitNode({ data, selected }: NodeProps<CircuitFlowNode>) {
  const { component, definition } = data
  const value = component.parameters.value
  const hFlip = Boolean(component.passthrough.h_flip)
  const vFlip = Boolean(component.passthrough.v_flip)
  const transform = `rotate(${component.rotation}deg) scale(${hFlip ? -1 : 1}, ${vFlip ? -1 : 1})`

  return (
    <div
      className={`circuit-node ${selected ? 'selected' : ''} device-${component.device.toLowerCase()}`}
      title={definition.description}
    >
      {definition.pins.map((pin) => (
        <Handle
          className="circuit-pin"
          id={pin}
          key={pin}
          position={Position.Top}
          style={transformedPin(definition.pin_positions[pin], definition, component)}
          title={pin}
          type="source"
        />
      ))}
      <span className="node-refdes">{component.refdes}</span>
      {component.device === 'JUNCTION' ? (
        <span className="junction-symbol" />
      ) : definition.symbol_url ? (
        <img
          alt={definition.description || definition.symbol}
          className="official-symbol"
          draggable={false}
          src={definition.symbol_url}
          style={{ transform }}
        />
      ) : (
        <span className="subcircuit-symbol">{component.model || 'X'}</span>
      )}
      {definition.show_pinnames && definition.pins.map((pin) => (
        <span
          className="pin-name"
          key={`label-${pin}`}
          style={transformedPin(definition.pin_positions[pin], definition, component)}
        >
          {pin}
        </span>
      ))}
      {value && <span className={`node-value ${value === '?' ? 'missing' : ''}`}>{value}</span>}
    </div>
  )
}
