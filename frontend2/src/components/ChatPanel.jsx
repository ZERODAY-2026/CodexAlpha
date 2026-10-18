import { useEffect, useRef, useState } from 'react';
import { askDocument } from '../services/api';

function Citation({ item }) {
  return (
    <blockquote className="chat-citation">
      <p>“{item.quote}”</p>
      <cite>{item.clause_id} · page {item.page}</cite>
    </blockquote>
  );
}

function Answer({ answer }) {
  const hasContent = answer.stated_in_document.length > 0
    || answer.possible_interpretations.length > 0
    || answer.concerns.length > 0
    || answer.uncertainty_notes.length > 0
    || Boolean(answer.escalation);

  return (
    <div className="chat-answer">
      <span className="answer-status">{answer.answer_status.replaceAll('_', ' ')}</span>

      {answer.answer_status === 'document_silent' && (
        <p className="chat-silent">I could not find this addressed in the document.</p>
      )}
      {!hasContent && answer.answer_status !== 'document_silent' && (
        <p className="chat-silent">No verified answer was returned for this question.</p>
      )}

      {answer.stated_in_document.length > 0 && (
        <section className="chat-answer-section">
          <h3>The document says</h3>
          {answer.stated_in_document.map((item, index) => (
            <article key={`${item.clause_id}-${index}`}>
              <p>{item.text}</p>
              <Citation item={item} />
            </article>
          ))}
        </section>
      )}

      {answer.possible_interpretations.length > 0 && (
        <section className="chat-answer-section">
          <h3>Possible interpretation</h3>
          {answer.possible_interpretations.map((item, index) => (
            <article key={`${item.clause_id}-${index}`}>
              <p>{item.text}</p>
              <Citation item={item} />
            </article>
          ))}
        </section>
      )}

      {answer.concerns.length > 0 && (
        <section className="chat-answer-section">
          <h3>Potential concerns</h3>
          {answer.concerns.map((item, index) => (
            <article key={`${item.clause_id}-${index}`}>
              <p><strong>{item.severity}:</strong> {item.reason}</p>
              <Citation item={item} />
            </article>
          ))}
        </section>
      )}

      {answer.uncertainty_notes.length > 0 && (
        <section className="chat-answer-section">
          <h3>Uncertainty</h3>
          <ul>{answer.uncertainty_notes.map((note, index) => <li key={index}>{note}</li>)}</ul>
        </section>
      )}

      {answer.escalation && <p className="chat-escalation">{answer.escalation}</p>}
    </div>
  );
}

export default function ChatPanel({ sessionId }) {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);
  const [asking, setAsking] = useState(false);
  const nextMessageId = useRef(0);
  const threadRef = useRef(null);

  useEffect(() => {
    setQuestion('');
    setMessages([]);
  }, [sessionId]);

  useEffect(() => {
    if (threadRef.current) {
      threadRef.current.scrollTop = threadRef.current.scrollHeight;
    }
  }, [messages]);

  async function submitQuestion(event) {
    event.preventDefault();
    const text = question.trim();
    if (!text || asking) return;

    const id = nextMessageId.current++;
    setQuestion('');
    setMessages((current) => [...current, { id, question: text, answer: null, error: '' }]);
    setAsking(true);
    try {
      const answer = await askDocument(sessionId, text);
      setMessages((current) => current.map((message) => (
        message.id === id ? { ...message, answer } : message
      )));
    } catch (error) {
      setMessages((current) => current.map((message) => (
        message.id === id
          ? { ...message, error: error instanceof Error ? error.message : 'Could not answer that question.' }
          : message
      )));
    } finally {
      setAsking(false);
    }
  }

  return (
    <section className="card chat-panel" aria-labelledby="chat-heading">
      <div className="chat-heading">
        <div>
          <h2 id="chat-heading" className="card__title">Chat about this document</h2>
          <p className="muted small">Ask questions and get answers with cited passages from the document.</p>
        </div>
      </div>

      <div
        ref={threadRef}
        className="chat-thread"
        role="log"
        aria-label="Chat messages"
        aria-live="polite"
        aria-relevant="additions text"
      >
        {messages.length === 0 && (
          <p className="chat-empty">Ask about a clause, deadline, payment, or anything else in the document.</p>
        )}
        {messages.map((message) => (
          <article className="chat-turn" key={message.id}>
            <p className="chat-question">{message.question}</p>
            {message.answer && <Answer answer={message.answer} />}
            {message.error && <p className="chat-error" role="alert">{message.error}</p>}
            {!message.answer && !message.error && asking && message.id === messages[messages.length - 1]?.id && (
              <p className="chat-pending">Checking the document…</p>
            )}
          </article>
        ))}
      </div>

      <form className="chat-form" onSubmit={(event) => void submitQuestion(event)}>
        <label className="visually-hidden" htmlFor="document-question">Ask a question about this document</label>
        <textarea
          id="document-question"
          value={question}
          maxLength={4000}
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault();
              event.currentTarget.form?.requestSubmit();
            }
          }}
          placeholder="Ask a question about the document…"
          disabled={asking}
          required
        />
        <button className="btn btn--primary" type="submit" disabled={asking || !question.trim()}>
          {asking ? 'Checking…' : 'Send'}
        </button>
      </form>
    </section>
  );
}
