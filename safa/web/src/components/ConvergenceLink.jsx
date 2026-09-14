import { Line } from '@react-three/drei'

export default function ConvergenceLink({ from, to }) {
  const mid = {
    x: (from.x + to.x) / 2,
    y: (from.y + to.y) / 2 - 0.6,
    z: (from.z + to.z) / 2,
  }
  return (
    <>
      <Line
        points={[
          [from.x, from.y, from.z],
          [mid.x, mid.y, mid.z],
          [to.x, to.y, to.z],
        ]}
        color="#f5d442"
        lineWidth={2.5}
        dashed
        dashSize={0.2}
        gapSize={0.12}
      />
      <mesh position={[mid.x, mid.y, mid.z]}>
        <sphereGeometry args={[0.12, 16, 16]} />
        <meshStandardMaterial color="#f5d442" emissive="#f5d442" emissiveIntensity={1.2} />
      </mesh>
    </>
  )
}
