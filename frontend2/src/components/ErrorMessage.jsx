import { CircleAlert } from 'lucide-react';

const TITLES = {
  network: 'Backend unreachable',
  timeout: 'Analysis timed out',
  http: 'The backend returned an error',
  'invalid-response': 'Unexpected response from backend',
};

export default function ErrorMessage({ error, onRetry }) {
  if (!error) return null;
  const title = TITLES[error.kind] || 'Something went wrong';

  return (
    <section className="card alert alert--danger" role="alert">
      <CircleAlert size={22} aria-hidden="true" className="alert__icon" />
      <div className="alert__body">
        <h2 className="alert__title">
          {title}
          {error.status ? <span className="muted small"> (HTTP {error.status})</span> : null}
        </h2>
        <p>{error.message}</p>
        {error.hint && <p className="muted small">{error.hint}</p>}
        {onRetry && (
          <div className="button-row">
            <button type="button" className="btn btn--primary" onClick={onRetry}>
              Try again
            </button>
          </div>
        )}
      </div>
    </section>
  );
}
