import { Text } from '@react-three/drei'

const THREAD_COLORS = ['#e5484d', '#5b8dee', '#5fd97a', '#f5a623', '#b47ee5', '#4fd1c5']

export function threadColor(laneIndex) {
  return THREAD_COLORS[laneIndex % THREAD_COLORS.length]
}

const BASE_RADIUS = 0.18
const RADIUS_PER_DEGREE = 0.045
const MAX_RADIUS = 0.5

// Degree-based node sizing: leaf nodes stay small, hub nodes (many edges)
// visibly balloon -- the single biggest lever for reading a dense graph as
// hub-and-spoke instead of noise.
export function radiusForDegree(degree = 0) {
  return Math.min(MAX_RADIUS, BASE_RADIUS + degree * RADIUS_PER_DEGREE)
}

export default function GraphNode({ id, position, color, degree, selected, onSelect }) {
  const radius = radiusForDegree(degree) * (selected ? 1.3 : 1)
  return (
    <group position={[position.x, position.y, position.z]}>
      <mesh
        onClick={(e) => {
          e.stopPropagation()
          onSelect(id)
        }}
      >
        <sphereGeometry args={[radius, 24, 24]} />
        <meshStandardMaterial
          color={color}
          emissive={selected ? color : '#000000'}
          emissiveIntensity={selected ? 0.6 : 0}
        />
      </mesh>
      <Text position={[0, radius + 0.25, 0]} fontSize={0.22} color="#e8e8e8" anchorX="center" anchorY="bottom">
        {id}
      </Text>
    </group>
  )
}
