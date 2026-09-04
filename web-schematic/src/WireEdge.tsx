import { BaseEdge, EdgeLabelRenderer, type Edge, type EdgeProps } from '@xyflow/react'
import type { Point } from './types'

export type WireEdgeData = { waypoints?: Point[] }
export type WireFlowEdge = Edge<WireEdgeData, 'wire'>

export function WireEdge({
  sourceX,
  sourceY,
  targetX,
  targetY,
  data,
  label,
  markerEnd,
  style,
}: EdgeProps<WireFlowEdge>) {
  const waypoints = data?.waypoints ?? []
  const points = waypoints.length > 0
    ? [{ x: sourceX, y: sourceY }, ...waypoints, { x: targetX, y: targetY }]
    : [
        { x: sourceX, y: sourceY },
        { x: (sourceX + targetX) / 2, y: sourceY },
        { x: (sourceX + targetX) / 2, y: targetY },
        { x: targetX, y: targetY },
      ]
  const path = points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`).join(' ')
  const labelX = (sourceX + targetX) / 2
  const labelY = (sourceY + targetY) / 2
  return <>
    <BaseEdge markerEnd={markerEnd} path={path} style={style} />
    {label && <EdgeLabelRenderer>
      <span
        className="wire-label nodrag nopan"
        style={{ transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)` }}
      >
        {label}
      </span>
    </EdgeLabelRenderer>}
  </>
}
