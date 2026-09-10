export default function ExamplePicker({
  stories,
  selectedId,
  onSelect,
  variant,
  onVariantChange,
  viewMode,
  onViewModeChange,
  showDirectOption,
  showCrcOption,
  pooledConvergence,
}) {
  const showPredictedOption = variant === 'original'
  return (
    <div className="picker">
      <h1>Nonlinear Temporal Reasoning</h1>
      <p className="subtitle">5 hand-authored example stories, rendered as 3D temporal graphs.</p>

      {pooledConvergence && (
        <div className="picker-group dataset-stat">
          <h2>Dataset convergence recall</h2>
          <div className="dataset-stat-value">{pooledConvergence.recall.toFixed(2)}</div>
          <p className="dataset-stat-note">
            {pooledConvergence.nGoldPairs} gold pairs pooled across every story, precision{' '}
            {pooledConvergence.precision.toFixed(2)} · a single story's convergence score alone is
            too noisy to read on its own (often just 1-2 gold pairs) -- this pooled figure is the
            stable number.
          </p>
        </div>
      )}

      <div className="picker-group">
        <h2>Story</h2>
        <ul className="story-list">
          {stories.map((s) => (
            <li key={s.id}>
              <button
                className={s.id === selectedId ? 'active' : ''}
                onClick={() => onSelect(s.id)}
              >
                {s.title}
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div className="picker-group">
        <h2>Variant</h2>
        <div className="toggle-row">
          <button className={variant === 'original' ? 'active' : ''} onClick={() => onVariantChange('original')}>
            Original
          </button>
          <button
            className={variant === 'counterfactual' ? 'active' : ''}
            onClick={() => onVariantChange('counterfactual')}
          >
            Counterfactual
          </button>
        </div>
      </div>

      <div className="picker-group">
        <h2>View</h2>
        <div className="toggle-row">
          <button className={viewMode === 'gold' ? 'active' : ''} onClick={() => onViewModeChange('gold')}>
            Gold graph
          </button>
          {showPredictedOption && (
            <button className={viewMode === 'predicted' ? 'active' : ''} onClick={() => onViewModeChange('predicted')}>
              Predicted
            </button>
          )}
          <button className={viewMode === 'repaired' ? 'active' : ''} onClick={() => onViewModeChange('repaired')}>
            {showPredictedOption ? 'Repaired' : 'Predicted'}
          </button>
          {showDirectOption && (
            <button className={viewMode === 'direct' ? 'active' : ''} onClick={() => onViewModeChange('direct')}>
              Direct baseline
            </button>
          )}
          {showCrcOption && (
            <button className={viewMode === 'crc' ? 'active' : ''} onClick={() => onViewModeChange('crc')}>
              With Recall Critique
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
