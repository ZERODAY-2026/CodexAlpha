import { CircleAlert, FileText, ListChecks, TriangleAlert } from 'lucide-react';

function Stat({ icon: Icon, label, value, tone }) {
  return (
    <div className={`stat ${tone ? `stat--${tone}` : ''}`}>
      <Icon size={18} aria-hidden="true" className="stat__icon" />
      <span className="stat__value">{value}</span>
      <span className="stat__label">{label}</span>
    </div>
  );
}

export default function SummaryCards({ result }) {
  const total = result.clauses.length;
  const verified = result.clauses.filter((c) => c.evidence_verified).length;
  const concerns = result.clauses.filter((c) => c.potential_concern).length;

  return (
    <div className="summary">
      <section className="card summary-card" aria-labelledby="summary-heading">
        <div className="summary-card__top">
          <div>
            <h2 id="summary-heading" className="summary-card__type">
              <FileText size={18} aria-hidden="true" /> Document overview
            </h2>
            <p className="muted small summary-card__filename">
              {result.fileName}
            </p>
          </div>
        </div>

        <h3 className="section-label">Summary</h3>
        {result.summary ? (
          <p className="summary-card__text">{result.summary}</p>
        ) : (
          <p className="muted">The backend did not return a summary.</p>
        )}

        <div className="stats">
          <Stat icon={ListChecks} label="Clauses found" value={total} />
          <Stat icon={CircleAlert} label="Concerns to review" value={concerns} tone={concerns ? 'warning' : undefined} />
          <Stat
            icon={TriangleAlert}
            label="Unverified quotes"
            value={total - verified}
            tone={total - verified ? 'danger' : undefined}
          />
        </div>

      </section>

      {result.missing_information.length > 0 && (
        <section className="card alert alert--warning" aria-labelledby="missing-heading">
          <TriangleAlert size={20} aria-hidden="true" className="alert__icon" />
          <div className="alert__body">
            <h3 id="missing-heading" className="alert__title">Missing or unclear information</h3>
            <ul className="plain-list">
              {result.missing_information.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
          </div>
        </section>
      )}

    </div>
  );
}
