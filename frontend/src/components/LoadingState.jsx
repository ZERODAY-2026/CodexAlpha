import { useEffect, useState } from 'react';
import { LoaderCircle } from 'lucide-react';
import { formatDuration } from '../utils/format';

const SLOW_AFTER_SECONDS = 30;

export default function LoadingState({ fileName, onCancel }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const started = Date.now();
    const id = setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <section className="card state-card" role="status" aria-live="polite">
      <LoaderCircle className="spin" size={28} aria-hidden="true" />
      <div className="state-card__body">
        <h2 className="state-card__title">Analysing document…</h2>
        <p className="muted">
          {`Extracting text and reviewing clauses in ${fileName}. This may take a minute or more.`}
        </p>
        <p className="muted small">Elapsed: {formatDuration(elapsed)}</p>
        {elapsed >= SLOW_AFTER_SECONDS && (
          <p className="small notice-inline">
            This is taking longer than usual. Long documents are slower on an on-device model; you can keep waiting or cancel.
          </p>
        )}
      </div>
      <button type="button" className="btn btn--ghost" onClick={onCancel}>
        Cancel
      </button>
    </section>
  );
}
