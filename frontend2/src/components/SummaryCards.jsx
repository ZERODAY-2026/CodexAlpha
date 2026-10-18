import { CircleAlert, FileText, FlaskConical, Info, ListChecks, TriangleAlert } from 'lucide-react';
import { TAGS } from '../utils/clauseTags';

const DEFAULT_DISCLAIMER =
  'This tool provides preliminary document understanding only and does not provide definitive legal advice.';

function Stat({ icon: Icon, label, value, tone }) {
  return (
    <div className={`stat ${tone ? `stat--${tone}` : ''}`}>
      <Icon size={18} aria-hidden="true" className="stat__icon" />
      <span className="stat__value">{value}</span>
      <span className="stat__label">{label}</span>
    </div>
  );
}

export default function SummaryCards({ result, clauseTags }) {
  const total = result.clauses.length;
  const verified = result.clauses.filter((c) => c.evidence_verified).length;
  const concerns = result.clauses.filter((c) => c.potential_concern).length;
  const tagCounts = Object.keys(TAGS).map((key) => ({
    key,
    count: result.clauses.filter((c) => clauseTags[c.id]?.keys.includes(key)).length,
  }));
  const isMock = result.source === 'mock';

  return (
    <div className="summary">
      {isMock && (
        <div className="alert alert--demo" role="note">
          <FlaskConical size={20} aria-hidden="true" className="alert__icon" />
          <div className="alert__body">
            <p className="alert__title">Demonstration data</p>
            <p>
              These results are sample data, not an AI analysis of <strong>{result.fileName}</strong>. Switch the data
              source to “Local backend” to analyse your document.
            </p>
          </div>
        </div>
      )}

      <section className="card summary-card" aria-labelledby="summary-heading">
        <div className="summary-card__top">
          <div>
            <p className="eyebrow">
              <FileText size={14} aria-hidden="true" /> Document type
            </p>
            <h2 id="summary-heading" className="summary-card__type">{result.document_type}</h2>
            <p className="muted small">
              {result.fileName} · {isMock ? 'demo data' : 'analysed by local backend'} ·{' '}
              {result.analyzedAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
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

        <div className="topic-row" aria-label="Clause topics">
          {tagCounts.map(({ key, count }) => (
            <span key={key} className={`topic ${count ? '' : 'topic--empty'}`}>
              {TAGS[key].plural} <strong>{count}</strong>
            </span>
          ))}
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

      <div className="alert alert--info" role="note">
        <Info size={20} aria-hidden="true" className="alert__icon" />
        <div className="alert__body">
          <p>{result.disclaimer || DEFAULT_DISCLAIMER}</p>
        </div>
      </div>
    </div>
  );
}
