import { FormEvent, useEffect, useRef, useState } from 'react';

type VerifiedCitation = {
  verified: true;
  quote: string;
  clause_id: string;
  page: number;
  quote_start: number;
  quote_end: number;
};

type KeyClause = VerifiedCitation & {
  category: string;
  plain_explanation: string;
  possible_concern: string | null;
};

type SourceClause = {
  id: string;
  page: number;
  text: string;
  suspicious_patterns: string[];
};

type RiskFlag = {
  type: string;
  severity: 'low' | 'medium' | 'high';
  quote: string;
  clause_id: string;
  page: string;
  note?: string;
};

type SessionData = {
  id: string;
  document_name: string;
  summary: string;
  status: { stage: string; done: number; total: number; error?: string };
  key_clauses: KeyClause[];
  source_clauses: SourceClause[];
  risks: RiskFlag[];
  suspicious_text: { clause_id: string; page: string; patterns: string }[];
  warnings: string[];
};

type AnswerItem = {
  verified: true;
  quote: string;
  clause_id: string;
  page: number;
  quote_start: number;
  quote_end: number;
};

type Answer = {
  answer_status: 'answered' | 'partially_answered' | 'document_silent';
  stated_in_document: (AnswerItem & { claim: string })[];
  possible_interpretations: (AnswerItem & { interpretation: string })[];
  concerns: (AnswerItem & { reason: string; severity: 'low' | 'med' | 'high' })[];
  uncertainty_notes: string[];
  escalation: string;
};

type ActiveHighlight = {
  clauseId: string;
  start: number;
  end: number;
};

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    const detail = typeof data?.detail === 'string' ? data.detail : `Request failed (${response.status}).`;
    throw new Error(detail);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export function isVerifiedCitation(value: unknown): value is VerifiedCitation {
  if (!value || typeof value !== 'object') return false;
  const item = value as Record<string, unknown>;
  return item.verified === true
    && typeof item.quote === 'string'
    && item.quote.length > 0
    && typeof item.clause_id === 'string'
    && typeof item.page === 'number'
    && typeof item.quote_start === 'number'
    && typeof item.quote_end === 'number';
}

function VerifiedPassage({
  citation,
  onSelect,
}: {
  citation: VerifiedCitation;
  onSelect: (citation: VerifiedCitation) => void;
}) {
  return (
    <button className="citation" type="button" onClick={() => onSelect(citation)}>
      <span className="citation-quote">“{citation.quote}”</span>
      <span className="citation-source">{citation.clause_id} · page {citation.page}</span>
    </button>
  );
}

function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [documentData, setDocumentData] = useState<SessionData | null>(null);
  const [progress, setProgress] = useState({ stage: '', done: 0, total: 0 });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [asking, setAsking] = useState(false);
  const [highlight, setHighlight] = useState<ActiveHighlight | null>(null);
  const sourceRefs = useRef<Record<string, HTMLElement | null>>({});
  const activeSession = useRef<string | null>(null);

  useEffect(() => {
    activeSession.current = sessionId;
  }, [sessionId]);

  useEffect(() => {
    if (!sessionId || !busy) return undefined;
    let cancelled = false;
    const poll = async () => {
      try {
        const result = await api<{ id: string; status: SessionData['status'] }>(
          `/api/sessions/${sessionId}/status`,
        );
        if (cancelled || activeSession.current !== sessionId) return;
        setProgress(result.status);
        if (result.status.stage === 'failed') {
          setError(result.status.error || 'Analysis failed. Please try a text-based PDF or plain-text file.');
          setBusy(false);
          return;
        }
        if (result.status.stage === 'done') {
          const data = await api<SessionData>(`/api/sessions/${sessionId}`);
          if (cancelled || activeSession.current !== sessionId) return;
          setDocumentData(data);
          setBusy(false);
        }
      } catch (pollError) {
        if (!cancelled) {
          setError(pollError instanceof Error ? pollError.message : 'Could not check analysis status.');
          setBusy(false);
        }
      }
    };
    void poll();
    const interval = window.setInterval(() => void poll(), 1000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [sessionId, busy]);

  const onUpload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const fileInput = form.elements.namedItem('document') as HTMLInputElement;
    const file = fileInput.files?.[0];
    if (!file) {
      setError('Choose a PDF or plain-text file first.');
      return;
    }
    setError('');
    setAnswer(null);
    setDocumentData(null);
    setBusy(true);
    setProgress({ stage: 'uploading', done: 0, total: 1 });
    const body = new FormData();
    body.append('file', file);
    try {
      const result = await api<{ id: string; status: SessionData['status'] }>('/api/sessions', {
        method: 'POST',
        body,
      });
      setSessionId(result.id);
      setProgress(result.status);
    } catch (uploadError) {
      setBusy(false);
      setError(uploadError instanceof Error ? uploadError.message : 'Upload failed.');
    }
  };

  const removeSession = async () => {
    if (!sessionId) return;
    try {
      await api<void>(`/api/sessions/${sessionId}`, { method: 'DELETE' });
      activeSession.current = null;
      setSessionId(null);
      setDocumentData(null);
      setAnswer(null);
      setProgress({ stage: '', done: 0, total: 0 });
      setHighlight(null);
      setError('');
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : 'Could not delete session data.');
    }
  };

  const ask = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!sessionId || !question.trim()) return;
    setAsking(true);
    setError('');
    setAnswer(null);
    try {
      const result = await api<Answer>(`/api/sessions/${sessionId}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question.trim() }),
      });
      setAnswer({
        ...result,
        stated_in_document: result.stated_in_document.filter((item) => isVerifiedCitation(item)),
        possible_interpretations: result.possible_interpretations.filter((item) => isVerifiedCitation(item)),
        concerns: result.concerns.filter((item) => isVerifiedCitation(item)),
      });
    } catch (askError) {
      setError(askError instanceof Error ? askError.message : 'Could not answer that question.');
    } finally {
      setAsking(false);
    }
  };

  const selectCitation = (citation: VerifiedCitation) => {
    setHighlight({
      clauseId: citation.clause_id,
      start: citation.quote_start,
      end: citation.quote_end,
    });
    requestAnimationFrame(() => {
      sourceRefs.current[citation.clause_id]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });
  };

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">PRIVATE · ON-DEVICE DOCUMENT TRIAGE</p>
          <h1>Understand the document, clause by clause.</h1>
          <p className="intro">Upload a rental or employment agreement for a preliminary, cited review.</p>
        </div>
        <div className="privacy-mark" aria-label="Local processing">Local only</div>
      </header>

      <div className="legal-banner" role="note">
        <strong>Preliminary understanding, not legal advice.</strong>
        <span>This tool cannot determine legal status or tell you whether to sign.</span>
      </div>

      <section className="panel upload-panel" aria-labelledby="upload-heading">
        <h2 id="upload-heading">Start a document review</h2>
        <form onSubmit={onUpload}>
          <label htmlFor="document">Agreement file</label>
          <div className="upload-row">
            <input id="document" name="document" type="file" accept=".pdf,.txt,application/pdf,text/plain" disabled={busy} />
            <button className="primary-button" type="submit" disabled={busy}>Review document</button>
          </div>
          <p className="help-text">PDF or .txt · up to 25 MB. Scanned image-only PDFs cannot be read.</p>
        </form>
        {busy ? (
          <div className="progress" role="status" aria-live="polite">
            <div className="progress-head">
              <span>{progress.stage || 'Preparing analysis'}…</span>
              {progress.total > 0 && <span>{progress.done} / {progress.total}</span>}
            </div>
            <progress value={progress.done} max={Math.max(progress.total, 1)} />
            <p>Analysis runs with the local Ollama model. Keep this page open.</p>
          </div>
        ) : null}
        {error ? <div className="error-message" role="alert">{error}</div> : null}
      </section>

      {documentData ? (
        <>
          <div className="document-heading">
            <div>
              <p className="eyebrow">CURRENT DOCUMENT</p>
              <h2>{documentData.document_name}</h2>
            </div>
            <button className="secondary-button" type="button" onClick={() => void removeSession()}>
              Delete session data
            </button>
          </div>

          {documentData.suspicious_text.length > 0 ? (
            <section className="notice-panel" aria-labelledby="suspicious-heading">
              <h2 id="suspicious-heading">Suspicious text in document</h2>
              <p>Instruction-like text was found and treated only as document content, not followed.</p>
              <ul>
                {documentData.suspicious_text.map((item) => (
                  <li key={`${item.clause_id}-${item.patterns}`}>
                    <button className="text-button" type="button" onClick={() => {
                      const source = documentData.source_clauses.find((clause) => clause.id === item.clause_id);
                      if (source) {
                        sourceRefs.current[item.clause_id]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                      }
                    }}>
                      {item.patterns} · {item.clause_id} · page {item.page}
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}
          {documentData.warnings.length > 0 ? (
            <section className="notice-panel" aria-label="Analysis limitations">
              <h2>Some analysis was omitted</h2>
              <ul>{documentData.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul>
            </section>
          ) : null}

          <div className="content-grid">
            <div className="analysis-column">
              <section className="panel" aria-labelledby="summary-heading">
                <h2 id="summary-heading">Cited overview</h2>
                <p className="summary-text">{documentData.summary}</p>
              </section>

              <section className="panel" aria-labelledby="clauses-heading">
                <h2 id="clauses-heading">Key clauses</h2>
                {documentData.key_clauses.length ? (
                  <div className="clause-list">
                    {documentData.key_clauses.map((clause, index) => (
                      <article className="key-clause" key={`${clause.clause_id}-${index}`}>
                        <div className="clause-meta">
                          <span className="category-label">{clause.category.split('_').join(' ')}</span>
                          <span>{clause.clause_id} · page {clause.page}</span>
                        </div>
                        <h3>The document says</h3>
                        {isVerifiedCitation(clause) ? (
                          <VerifiedPassage citation={clause} onSelect={selectCitation} />
                        ) : <p className="muted">No verified passage is available for this item.</p>}
                        <p>{clause.plain_explanation}</p>
                        {clause.possible_concern ? (
                          <div className="interpretation-box">
                            <h3>Possible concern</h3>
                            <p>{clause.possible_concern}</p>
                          </div>
                        ) : null}
                      </article>
                    ))}
                  </div>
                ) : <p>No key clauses could be verified by the local model. Check the source clauses below.</p>}
              </section>

              <section className="panel" aria-labelledby="risks-heading">
                <h2 id="risks-heading">Review flags</h2>
                {documentData.risks.length ? (
                  <ul className="risk-list">
                    {documentData.risks.map((risk, index) => (
                      <li key={`${risk.type}-${risk.clause_id}-${index}`}>
                        <strong>{risk.type} · severity: {risk.severity}</strong>
                        <span>{risk.quote}</span>
                        {risk.note ? <span>{risk.note}</span> : null}
                        {risk.clause_id ? <span>{risk.clause_id} · page {risk.page}</span> : null}
                      </li>
                    ))}
                  </ul>
                ) : <p>No flags were detected by the basic review checks. This is not a guarantee that none exist.</p>}
              </section>

              <section className="panel" aria-labelledby="qa-heading">
                <h2 id="qa-heading">Ask about this document</h2>
                <form onSubmit={(event) => void ask(event)}>
                  <label htmlFor="question">Question</label>
                  <textarea
                    id="question"
                    value={question}
                    maxLength={4000}
                    onChange={(event) => setQuestion(event.target.value)}
                    placeholder="For example: When is rent due? What notice does the agreement mention?"
                  />
                  <button className="primary-button" type="submit" disabled={asking || !question.trim()}>
                    {asking ? 'Checking the document…' : 'Ask'}
                  </button>
                </form>
                {answer ? (
                  <div className="answer" aria-live="polite">
                    <p className="answer-status">Answer status: {answer.answer_status.split('_').join(' ')}</p>
                    {answer.stated_in_document.length ? (
                      <div className="answer-section">
                        <h3>The document says</h3>
                        {answer.stated_in_document.map((item, index) => (
                          <article key={`${item.clause_id}-${index}`}>
                            <p>{item.claim}</p>
                            <VerifiedPassage citation={item} onSelect={selectCitation} />
                          </article>
                        ))}
                      </div>
                    ) : null}
                    {answer.possible_interpretations.length ? (
                      <div className="answer-section interpretation-box">
                        <h3>Possible interpretation</h3>
                        {answer.possible_interpretations.map((item, index) => (
                          <article key={`${item.clause_id}-${index}`}>
                            <p>{item.interpretation}</p>
                            <VerifiedPassage citation={item} onSelect={selectCitation} />
                          </article>
                        ))}
                      </div>
                    ) : null}
                    {answer.concerns.length ? (
                      <div className="answer-section concern-box">
                        <h3>Possible concerns</h3>
                        <ul>
                          {answer.concerns.map((item, index) => (
                            <li key={`${item.clause_id}-${index}`}>
                              <strong>Severity: {item.severity}</strong>
                              <p>{item.reason}</p>
                              <VerifiedPassage citation={item} onSelect={selectCitation} />
                            </li>
                          ))}
                        </ul>
                      </div>
                    ) : null}
                    {answer.answer_status === 'document_silent' ? (
                      <p className="silent-message">The document does not address this.</p>
                    ) : null}
                    {answer.uncertainty_notes.length ? (
                      <div className="answer-section">
                        <h3>Uncertainty</h3>
                        <ul>{answer.uncertainty_notes.map((note, index) => <li key={index}>{note}</li>)}</ul>
                      </div>
                    ) : null}
                    {answer.escalation ? (
                      <div className="answer-section">
                        <h3>When to get help</h3>
                        <p>{answer.escalation}</p>
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </section>
            </div>

            <aside className="source-column" aria-labelledby="source-heading">
              <section className="panel source-panel">
                <h2 id="source-heading">Source text</h2>
                <p className="help-text">Select a citation to locate its passage here.</p>
                {documentData.source_clauses.map((clause) => {
                  const active = highlight?.clauseId === clause.id;
                  const start = active ? Math.max(0, highlight.start) : -1;
                  const end = active ? Math.min(clause.text.length, highlight.end) : -1;
                  return (
                    <article
                      className={`source-clause${active ? ' source-clause-active' : ''}`}
                      key={clause.id}
                      id={`source-${clause.id}`}
                      ref={(node) => { sourceRefs.current[clause.id] = node; }}
                    >
                      <h3>{clause.id} · page {clause.page}</h3>
                      <p>
                        {active && start >= 0 && end > start ? (
                          <>
                            {clause.text.slice(0, start)}
                            <mark>{clause.text.slice(start, end)}</mark>
                            {clause.text.slice(end)}
                          </>
                        ) : clause.text}
                      </p>
                    </article>
                  );
                })}
              </section>
            </aside>
          </div>
        </>
      ) : null}
      <footer>This is automated triage output, not legal advice. Consult a qualified solicitor.</footer>
    </main>
  );
}

export default App;
