// The three sub-scores (relation/thread/convergence) are the primary,
// trustworthy numbers -- each computed over enough data points per story to
// be stable. AWT-F1's harmonic mean is deliberately NOT shown here as the
// headline: it's exactly 0 whenever convergence_f1 (often based on just 1-2
// gold pairs per story) misses, which makes it a poor "at a glance" number
// even when the other two dimensions are fine. See metrics/awt_f1.py's
// pooled_convergence_f1 docstring for the full reasoning.
export default function SubscoreRow({ scores }) {
  // Convergence is shown as precision against the pool of genuinely
  // simultaneous pairs, not the old exact-set-match F1. Gold annotates only
  // the narratively salient moments while the intervals imply many more true
  // ones, so exact match scored a model wrong for correctly finding an
  // unannotated simultaneity -- which read as 0.00 everywhere and hid real
  // differences between the methods.
  const convergence = scores.convergence_precision_vs_pool ?? scores.convergence_f1
  const hasPool = scores.convergence_pool_available

  return (
    <div className="hud-subscores">
      <div className="hud-subscore">
        <div className="hud-subscore-value">{scores.relation_score.toFixed(2)}</div>
        <div className="hud-subscore-label">relation</div>
      </div>
      <div className="hud-subscore">
        <div className="hud-subscore-value">{scores.thread_attribution_accuracy.toFixed(2)}</div>
        <div className="hud-subscore-label">thread</div>
      </div>
      <div className="hud-subscore">
        <div className="hud-subscore-value">{convergence.toFixed(2)}</div>
        <div className="hud-subscore-label">{hasPool ? 'converg. prec' : 'convergence'}</div>
      </div>
    </div>
  )
}
