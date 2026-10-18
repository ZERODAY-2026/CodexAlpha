import { useEffect, useRef, useState } from 'react';
import SummaryCards from './SummaryCards';
import ClauseList from './ClauseList';
import EvidencePanel from './EvidencePanel';
import ChatPanel from './ChatPanel';

const MOBILE_QUERY = '(max-width: 900px)';

export default function AnalysisDashboard({ result }) {
  const [selectedId, setSelectedId] = useState(result.clauses[0]?.id ?? null);
  const evidenceRef = useRef(null);

  // Reset the selection whenever a new result arrives.
  useEffect(() => {
    setSelectedId(result.clauses[0]?.id ?? null);
  }, [result]);

  const selected = result.clauses.find((c) => c.id === selectedId) ?? null;

  function handleSelect(id) {
    setSelectedId(id);
    // On stacked (mobile) layouts the evidence sits below the list; bring it into view.
    if (window.matchMedia(MOBILE_QUERY).matches) {
      requestAnimationFrame(() => {
        evidenceRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        evidenceRef.current?.focus({ preventScroll: true });
      });
    }
  }

  return (
    <div className="dashboard">
      <SummaryCards result={result} />
      <ChatPanel sessionId={result.sessionId} />
      <div className="analysis-grid">
        <ClauseList
          clauses={result.clauses}
          selectedId={selectedId}
          onSelect={handleSelect}
        />
        <div className="analysis-grid__aside">
          <EvidencePanel clause={selected} panelRef={evidenceRef} />
        </div>
      </div>
    </div>
  );
}
