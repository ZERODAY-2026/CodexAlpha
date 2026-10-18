import StatusPill from './StatusPill';

const LABELS = {
  high: 'Model: high',
  medium: 'Model: medium',
  low: 'Model: low',
  unrated: 'Model: unrated',
};

// Confidence is a coarse self-assessment from the model, never shown as a percentage.
export default function ConfidenceLabel({ level }) {
  return (
    <StatusPill tone="outline" title="Model-reported confidence. This is not a calibrated probability.">
      {LABELS[level] || LABELS.unrated}
    </StatusPill>
  );
}
