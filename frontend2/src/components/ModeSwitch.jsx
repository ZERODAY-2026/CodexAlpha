import { FlaskConical, Server } from 'lucide-react';

// Segmented control for choosing between the real backend and demo data.
export default function ModeSwitch({ useMock, onChange, disabled }) {
  return (
    <fieldset className="mode-switch" disabled={disabled}>
      <legend className="mode-switch__legend">Data source</legend>
      <label className={`mode-switch__option ${!useMock ? 'is-active' : ''}`}>
        <input type="radio" name="data-source" checked={!useMock} onChange={() => onChange(false)} />
        <Server size={15} aria-hidden="true" />
        Local backend
      </label>
      <label className={`mode-switch__option ${useMock ? 'is-active' : ''}`}>
        <input type="radio" name="data-source" checked={useMock} onChange={() => onChange(true)} />
        <FlaskConical size={15} aria-hidden="true" />
        Demo data
      </label>
    </fieldset>
  );
}
