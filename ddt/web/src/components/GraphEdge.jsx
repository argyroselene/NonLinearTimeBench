import { QuadraticBezierLine } from '@react-three/drei'
import { RELATION_STYLE } from '../lib/layout'

function scoreColor(score) {
  // 0 -> red, 1 -> green, via a simple linear HSL sweep.
  const hue = Math.max(0, Math.min(1, score)) * 120
  return `hsl(${hue}, 75%, 55%)`
}

// Deterministic hash of the edge's node ids, used to jitter each edge's arc
// so parallel edges into the same hub node fan out visibly instead of
// stacking exactly on top of one another.
function edgeHash(nodeI, nodeJ) {
  const key = `${nodeI}|${nodeJ}`
  let hash = 0
  for (let i = 0; i < key.length; i++) {
    hash = (hash * 31 + key.charCodeAt(i)) | 0
  }
  return hash
}

export default function GraphEdge({ from, to, relation, score, nodeI, nodeJ }) {
  const style = RELATION_STYLE[relation] ?? { color: '#999999', arc: 1.0 }
  const color = score === undefined ? style.color : scoreColor(score)
  const hash = edgeHash(nodeI ?? `${from.x},${from.y},${from.z}`, nodeJ ?? `${to.x},${to.y},${to.z}`)
  const heightJitter = ((hash % 100) / 100 - 0.5) * 0.6
  const sideJitter = (((hash >> 8) % 100) / 100 - 0.5) * 0.5
  const mid = {
    x: (from.x + to.x) / 2 + sideJitter,
    y: Math.max(from.y, to.y) + style.arc + heightJitter,
    z: (from.z + to.z) / 2,
  }
  return (
    <QuadraticBezierLine
      start={[from.x, from.y, from.z]}
      end={[to.x, to.y, to.z]}
      mid={[mid.x, mid.y, mid.z]}
      color={color}
      lineWidth={score !== undefined && score < 0.5 ? 3 : 1.5}
    />
  )
}
