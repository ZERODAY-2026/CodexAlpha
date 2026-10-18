import { useState } from 'react';
import { ChevronRight } from 'lucide-react';
import VerificationLabel from './VerificationLabel';

const BASE_FILTERS = [
  { id: 'all', label: 'All', test: () => true },
  { id: 'concerns', label: 'Has concern', test: (c) => Boolean(c.potential_concern) },
  { id: 'unverified', label: 'Unverified', test: (c) => !c.evidence_verified },
];

export default function ClauseList({ clauses, selectedId, onSelect }) {
  const [filterId, setFilterId] = useState('all');
  const active = BASE_FILTERS.find((filter) => filter.id === filterId) || BASE_FILTERS[0];
  const visible = clauses.filter(active.test);

  return (
    <section className="card clause-list" aria-labelledby="clauses-heading">
      <div className="card__header card__header--tight">
        <h2 id="clauses-heading" className="card__title">Clauses</h2>
        <span className="muted small">
          {visible.length} of {clauses.length}
        </span>
      </div>

      <div className="filter-row" role="group" aria-label="Filter clauses">
        {BASE_FILTERS.map((filter) => {
          const count = clauses.filter(filter.test).length;
          return (
            <button
              key={filter.id}
              type="button"
              className={`chip ${filter.id === active.id ? 'is-active' : ''}`}
              aria-pressed={filter.id === active.id}
              onClick={() => setFilterId(filter.id)}
              disabled={count === 0 && filter.id !== 'all'}
            >
              {filter.label} <span className="chip__count">{count}</span>
            </button>
          );
        })}
      </div>

      {clauses.length === 0 ? (
        <p className="muted empty-inline">The backend did not identify any clauses in this document.</p>
      ) : visible.length === 0 ? (
        <p className="muted empty-inline">No clauses match this filter.</p>
      ) : (
        <ul className="clause-items">
          {visible.map((clause) => {
            const selected = clause.id === selectedId;
            return (
              <li key={clause.id}>
                <button
                  type="button"
                  className={`clause-item ${selected ? 'is-selected' : ''} ${clause.evidence_verified ? '' : 'is-unverified'}`}
                  aria-pressed={selected}
                  onClick={() => onSelect(clause.id)}
                >
                  <span className="clause-item__head">
                    <span className="clause-item__title">{clause.title}</span>
                    <span className="clause-item__page">{clause.page ? `p. ${clause.page}` : 'page n/a'}</span>
                  </span>
                  {clause.potential_concern && <span className="clause-item__concern">{clause.potential_concern}</span>}
                  <span className="clause-item__meta">
                    <VerificationLabel verified={clause.evidence_verified} />
                  </span>
                  <ChevronRight size={18} aria-hidden="true" className="clause-item__chevron" />
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
