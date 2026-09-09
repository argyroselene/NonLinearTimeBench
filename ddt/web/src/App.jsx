import { useMemo, useState } from 'react'
import { STORIES } from './data'
import ExamplePicker from './components/ExamplePicker'
import PassagePanel from './components/PassagePanel'
import Graph3D from './components/Graph3D'
import SubscoreRow from './components/SubscoreRow'
import { pooledConvergenceF1 } from './lib/pooledConvergence'
import './App.css'

function nodeScoreMap(comparison) {
  if (!comparison) return {}
  const totals = {}
  const counts = {}
  for (const edge of comparison.scored_edges) {
    for (const nodeId of [edge.node_i, edge.node_j]) {
      totals[nodeId] = (totals[nodeId] ?? 0) + edge.score
      counts[nodeId] = (counts[nodeId] ?? 0) + 1
    }
  }
  return Object.fromEntries(Object.keys(totals).map((id) => [id, totals[id] / counts[id]]))
}

export default function App() {
  const [selectedId, setSelectedId] = useState(STORIES[0].id)
  const [variant, setVariant] = useState('original')
  const [viewMode, setViewMode] = useState('gold')
  const [selectedNode, setSelectedNode] = useState(null)

  // Dataset-level convergence recall, pooled across every loaded story's
  // gold vs. real-pipeline prediction -- a stable, honest anchor number to
  // show alongside any single story's noisy per-story convergence_f1 (most
  // stories have only 1-2 gold convergence points; see
  // metrics/awt_f1.py's pooled_convergence_f1 docstring for why that's too
  // few to score individually). Independent of which story is selected.
  const pooledConvergence = useMemo(
    () =>
      pooledConvergenceF1(
        STORIES.filter((s) => s.prediction).map((s) => ({
          storyId: s.id,
          goldPoints: s.original.convergence_points,
          predictedPoints: s.prediction.convergence_points,
        }))
      ),
    []
  )

  const entry = STORIES.find((s) => s.id === selectedId)
  const story = entry[variant]
  const activePrediction = variant === 'original' ? entry.prediction : entry.counterfactualPrediction
  // The direct baseline and the CRC (Convergence Recall Critique) ablation
  // were only ever run against the original variant, so neither has a
  // counterfactual twin.
  const directPrediction = variant === 'original' ? entry.directPrediction : null
  const crcPrediction = variant === 'original' ? entry.crcPrediction : null
  const groqBaselinePrediction = variant === 'original' ? entry.groqBaselinePrediction : null
  // The counterfactual run only records the post-repair result (no unrepaired
  // split), so "predicted" isn't a meaningful view for that variant.
  const hasUnrepairedSplit = variant === 'original'
  const canCompare = Boolean(activePrediction)
  const showDirectOption = variant === 'original' && Boolean(directPrediction)
  const showCrcOption = variant === 'original' && Boolean(crcPrediction)
  const requestedViewMode =
    viewMode === 'direct'
      ? (showDirectOption ? 'direct' : 'gold')
      : viewMode === 'crc'
      ? (showCrcOption ? 'crc' : 'gold')
      : canCompare
      ? viewMode
      : 'gold'
  const effectiveViewMode =
    requestedViewMode === 'predicted' && !hasUnrepairedSplit ? 'repaired' : requestedViewMode

  const comparison =
    effectiveViewMode === 'direct'
      ? directPrediction
      : effectiveViewMode === 'crc'
      ? crcPrediction
      : effectiveViewMode === 'predicted'
      ? { ...activePrediction, scored_edges: activePrediction.scored_edges_unrepaired }
      : effectiveViewMode === 'repaired'
      ? activePrediction
      : null

  const scoreById = useMemo(() => nodeScoreMap(comparison), [comparison])

  const predictedAwt = hasUnrepairedSplit ? activePrediction?.awt_f1_scores_unrepaired : null
  const repairedAwt = activePrediction?.awt_f1_scores
  const shownAwt = effectiveViewMode === 'repaired' || !predictedAwt ? repairedAwt : predictedAwt
  const repairCount = activePrediction?.repair_log?.filter((e) => e.to_relation).length ?? 0
  const memorizationGap = variant === 'counterfactual' ? activePrediction?.memorization_gap : null
  const directAwt = directPrediction?.awt_f1_scores
  const relationDelta =
    directAwt && repairedAwt ? directAwt.relation_score - repairedAwt.relation_score : null
  const crcAwt = crcPrediction?.awt_f1_scores
  const groqBaselineAwt = groqBaselinePrediction?.awt_f1_scores
  const crcRecovered = crcPrediction?.recall_critique_added?.length ?? 0
  const convergenceDelta =
    crcAwt && groqBaselineAwt ? crcAwt.convergence_f1 - groqBaselineAwt.convergence_f1 : null

  return (
    <div className="app-shell">
      <ExamplePicker
        stories={STORIES}
        selectedId={selectedId}
        onSelect={(id) => {
          setSelectedId(id)
          setSelectedNode(null)
        }}
        variant={variant}
        onVariantChange={setVariant}
        viewMode={effectiveViewMode}
        onViewModeChange={setViewMode}
        showDirectOption={showDirectOption}
        showCrcOption={showCrcOption}
        pooledConvergence={pooledConvergence}
      />

      <main className="viewer">
        <Graph3D
          story={story}
          comparison={comparison}
          selectedNode={selectedNode}
          onSelectNode={setSelectedNode}
        />
        {comparison && effectiveViewMode === 'direct' && directAwt && (
          <div className="score-hud">
            <SubscoreRow scores={directAwt} />
            <div className="hud-headline">
              core (relation+thread): <strong>{directAwt.awt_core.toFixed(3)}</strong>
            </div>
            <div className="muted">
              (direct baseline only asserts before/after, never overlaps/during/etc.)
            </div>
            {repairedAwt && relationDelta !== null && (
              <>
                <hr />
                <div className="muted">graph-pipeline relation_score: {repairedAwt.relation_score.toFixed(3)}</div>
                <div className="muted">
                  Δ relation_score (direct − pipeline): {relationDelta >= 0 ? '+' : ''}
                  {relationDelta.toFixed(3)}
                </div>
              </>
            )}
          </div>
        )}
        {comparison && effectiveViewMode === 'crc' && crcAwt && (
          <div className="score-hud">
            <SubscoreRow scores={crcAwt} />
            <div className="hud-headline">
              core (relation+thread): <strong>{crcAwt.awt_core.toFixed(3)}</strong>
            </div>
            <hr />
            <div className="muted">
              Recall Critique found {crcRecovered} candidate{crcRecovered === 1 ? '' : 's'} the base
              pipeline missed{crcRecovered === 0 ? ' (none, for this story)' : ''}
            </div>
            {groqBaselineAwt && (
              <>
                <div className="muted">
                  same-model, no-CRC convergence: {groqBaselineAwt.convergence_f1.toFixed(3)}
                </div>
                {convergenceDelta !== null && (
                  <div className="muted">
                    Δ convergence_f1 (CRC − no-CRC, same model): {convergenceDelta >= 0 ? '+' : ''}
                    {convergenceDelta.toFixed(3)}
                  </div>
                )}
              </>
            )}
          </div>
        )}
        {comparison && effectiveViewMode !== 'direct' && effectiveViewMode !== 'crc' && repairedAwt && (
          <div className="score-hud">
            <SubscoreRow scores={shownAwt} />
            <div className="hud-headline">
              core (relation+thread): <strong>{shownAwt.awt_core.toFixed(3)}</strong>
            </div>
            {predictedAwt && (
              <>
                <hr />
                <div className="muted">predicted AWT-F1: {predictedAwt.awt_f1.toFixed(3)}</div>
                <div className="muted">repaired AWT-F1: {repairedAwt.awt_f1.toFixed(3)}</div>
                <div className="muted">
                  path-consistency repairs applied: {repairCount}
                  {repairCount > 0 && ` (Δ ${(repairedAwt.awt_f1 - predictedAwt.awt_f1 >= 0 ? '+' : '')}${(repairedAwt.awt_f1 - predictedAwt.awt_f1).toFixed(3)})`}
                </div>
              </>
            )}
            {memorizationGap !== null && memorizationGap !== undefined && (
              <>
                <hr />
                <div className="muted">
                  memorization gap (original − counterfactual AWT-F1): {memorizationGap >= 0 ? '+' : ''}
                  {memorizationGap.toFixed(3)}
                </div>
              </>
            )}
          </div>
        )}
        {!canCompare && variant === 'counterfactual' && (
          <div className="score-hud muted">No counterfactual prediction found for this story.</div>
        )}
      </main>

      <PassagePanel
        story={story}
        selectedNode={selectedNode}
        onSelectNode={setSelectedNode}
        scoreById={comparison ? scoreById : undefined}
      />
    </div>
  )
}
