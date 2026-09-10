import manifest from './manifest.json'

const originals = import.meta.glob('./stories/*/original.json', { eager: true })
const counterfactuals = import.meta.glob('./stories/*/counterfactual.json', { eager: true })
const predictions = import.meta.glob('./predictions/*.json', { eager: true })

export const STORIES = manifest.stories.map((entry) => ({
  id: entry.id,
  title: entry.title,
  original: originals[`./stories/${entry.dir}/original.json`].default,
  counterfactual: counterfactuals[`./stories/${entry.dir}/counterfactual.json`].default,
  prediction: predictions[`./predictions/${entry.dir}.json`]?.default ?? null,
  counterfactualPrediction: predictions[`./predictions/${entry.dir}_counterfactual.json`]?.default ?? null,
  directPrediction: predictions[`./predictions/${entry.dir}_direct.json`]?.default ?? null,
  crcPrediction: predictions[`./predictions/${entry.dir}_crc.json`]?.default ?? null,
  // Same model, same everything, CRC stage OFF -- the fair baseline for the
  // CRC comparison, since the official story_XX.json prediction may have
  // been generated on a different model (see generate_crc_predictions.py).
  groqBaselinePrediction: predictions[`./predictions/${entry.dir}_groq_baseline.json`]?.default ?? null,
}))
