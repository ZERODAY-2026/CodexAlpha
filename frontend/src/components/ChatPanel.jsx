import { useEffect, useRef, useState } from 'react';
import { askDocument } from '../services/api';

function Citation({ item }) {
  return (
    <details className="chat-citation">
      <summary>Source: {item.clause_id} · page {item.page}</summary>
      <blockquote>“{item.quote}”</blockquote>
    </details>
  );
}

function Answer({ answer }) {
  const points = [
    ...answer.stated_in_document.map((item) => ({ text: item.claim, citation: item })),
    ...answer.possible_interpretations.map((item) => ({ text: item.interpretation, citation: item })),
    ...answer.concerns.map((item) => ({ text: item.reason, citation: item })),
  ];

  return (
    <div className="chat-answer">
      {points.length ? (
        <>
          <p>{answer.concerns.length ? 'Here are the main points I would review:' : 'Here is what I found:'}</p>
          <ul className="chat-points">
            {points.map((point, index) => (
              <li key={`${point.citation.clause_id}-${index}`}>
                <p>{point.text}</p>
                <Citation item={point.citation} />
              </li>
            ))}
          </ul>
        </>
      ) : (
        <p className="chat-silent">I couldn’t find a relevant passage for that in the document. Try asking about a specific clause or topic.</p>
      )}
      {answer.uncertainty_notes.length > 0 && (
        <p className="chat-note">{answer.uncertainty_notes[0]}</p>
      )}
      {!answer.statutory_background_available && (
        <p className="chat-note">
          No matching local legal reference was available; this answer is based on the agreement text.
        </p>
      )}
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
          <p className="muted small">Ask a question about the agreement. Press Enter to send, or Shift+Enter for a new line.</p>
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
