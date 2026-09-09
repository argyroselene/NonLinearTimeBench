import { Canvas } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import { computeLayout, computeDegrees } from '../lib/layout'
import GraphNode, { threadColor } from './GraphNode'
import GraphEdge from './GraphEdge'
import ConvergenceLink from './ConvergenceLink'

// `convergence_points` (gold/direct) is already a flat list of [nodeA, nodeB]
// tuples. `candidate_convergence_pairs` (graph-pipeline predictions, pre-COC)
// is instead a list of cluster objects `{ members: [id, ...], shared_detail }`
// with 2+ members — normalize both shapes into a flat list of node pairs so
// the renderer below never has to know which one it received.
function toPairs(convergencePoints) {
  const pairs = []
  for (const entry of convergencePoints ?? []) {
    if (Array.isArray(entry)) {
      pairs.push(entry)
      continue
    }
    const members = entry?.members ?? []
    for (let i = 0; i < members.length - 1; i += 1) {
      pairs.push([members[i], members[i + 1]])
    }
  }
  return pairs
}

export default function Graph3D({ story, comparison, selectedNode, onSelectNode }) {
  const { positions, laneIndex } = computeLayout(story)
  const degrees = computeDegrees(story)

  const edges = comparison
    ? comparison.scored_edges.map((e) => ({
        node_i: e.node_i,
        node_j: e.node_j,
        allen_relation: e.gold_relation,
        score: e.score,
      }))
    : story.edges

  // Graph-pipeline predictions record pre-COC-verification candidates
  // separately (candidate_convergence_pairs); the direct baseline has no
  // such intermediate stage, so its convergence_points is already final.
  const convergencePoints = toPairs(
    comparison
      ? comparison.candidate_convergence_pairs ?? comparison.convergence_points ?? []
      : story.convergence_points
  )

  return (
    <Canvas camera={{ position: [4, 6, 12], fov: 45 }}>
      <color attach="background" args={['#0e0f13']} />
      <ambientLight intensity={0.6} />
      <pointLight position={[10, 10, 10]} intensity={1.2} />
      <pointLight position={[-10, 5, -10]} intensity={0.4} />

      {story.events.map((event) => (
        <GraphNode
          key={event.id}
          id={event.id}
          position={positions[event.id]}
          color={threadColor(laneIndex[event.thread_id] ?? 0)}
          degree={degrees[event.id]}
          selected={selectedNode === event.id}
          onSelect={onSelectNode}
        />
      ))}

      {edges.map((edge, i) => {
        const from = positions[edge.node_i]
        const to = positions[edge.node_j]
        if (!from || !to) return null
        return (
          <GraphEdge
            key={`${edge.node_i}-${edge.node_j}-${i}`}
            from={from}
            to={to}
            nodeI={edge.node_i}
            nodeJ={edge.node_j}
            relation={edge.allen_relation}
            score={comparison ? edge.score : undefined}
          />
        )
      })}

      {convergencePoints.map(([a, b], i) => {
        const from = positions[a]
        const to = positions[b]
        if (!from || !to) return null
        return <ConvergenceLink key={`conv-${a}-${b}-${i}`} from={from} to={to} />
      })}

      <OrbitControls makeDefault enableDamping dampingFactor={0.08} />
    </Canvas>
  )
}
