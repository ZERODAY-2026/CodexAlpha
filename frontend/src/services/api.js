// All backend communication lives here. Presentation components never call fetch.
//
// Uses the Python backend's session endpoints for upload, polling, and results.

import { apiUrl, config } from '../config';

export class AnalysisError extends Error {
  constructor(kind, message, details = {}) {
    super(message);
    this.name = 'AnalysisError';
    this.kind = kind; // 'network' | 'timeout' | 'http' | 'invalid-response' | 'cancelled'
    this.status = details.status ?? null;
    this.hint = details.hint ?? null;
  }
}

function asText(value) {
  return typeof value === 'string' ? value.trim() : '';
}

function normalizePage(value) {
  const page = Number(value);
  return Number.isInteger(page) && page > 0 ? page : null;
}

function normalizeClause(raw, index) {
  if (!raw || typeof raw !== 'object') return null;
  const category = asText(raw.category);
  const title = category
    ? category
        .split(/[_\s-]+/)
        .filter(Boolean)
        .map((word) => `${word[0].toUpperCase()}${word.slice(1).toLowerCase()}`)
        .join(' ')
    : `Clause ${index + 1}`;
  return {
    id: asText(raw.clause_id) || `clause-${index + 1}`,
    title,
    page: normalizePage(raw.page),
    source_quote: asText(raw.quote),
    explicit_meaning: asText(raw.plain_explanation),
    potential_concern: asText(raw.possible_concern),
    evidence_verified: raw.verified === true,
  };
}

// Validates and normalizes a backend payload. Throws AnalysisError when the shape
// is unusable so the UI never renders half-parsed data as if it were complete.
function normalizeAnalysis(payload, sessionId) {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    throw new AnalysisError('invalid-response', 'The backend returned an unexpected response format.');
  }
  if (!Array.isArray(payload.key_clauses)) {
    throw new AnalysisError(
      'invalid-response',
      'The backend response is missing the "key_clauses" list.',
      { hint: 'Check that the backend session response matches the expected API contract.' },
    );
  }

  const seen = new Set();
  const clauses = payload.key_clauses
    .map(normalizeClause)
    .filter(Boolean)
    .map((clause, index) => {
      // Guarantee unique ids so selection works even if the backend repeats one.
      const id = seen.has(clause.id) ? `${clause.id}-${index}` : clause.id;
      seen.add(id);
      return { ...clause, id };
    });

  const missing = Array.isArray(payload.warnings)
    ? payload.warnings
        .map((item) => (typeof item === 'string' ? item.trim() : asText(item?.description || item?.item)))
        .filter(Boolean)
    : [];

  return {
    sessionId,
    summary: asText(payload.summary),
    clauses,
    missing_information: missing,
  };
}

async function readErrorMessage(response) {
  try {
    const text = await response.text();
    if (!text) return '';
    try {
      const data = JSON.parse(text);
      const detail = data.detail ?? data.error ?? data.message;
      if (typeof detail === 'string') return detail;
      if (Array.isArray(detail)) return detail.map((d) => d.msg || JSON.stringify(d)).join('; ');
    } catch {
      // Not JSON; fall through to the plain text (trimmed).
    }
    return text.slice(0, 300);
  } catch {
    return '';
  }
}

function httpErrorFor(status, serverMessage) {
  // The Vite dev proxy answers 502 with an empty body when the backend is not running.
  if (status === 502 && !serverMessage) {
    return new AnalysisError('network', 'Could not reach the analysis backend.', {
      status,
      hint: 'Make sure the Python backend is running. In development, /api is proxied to VITE_BACKEND_PROXY_TARGET (default http://localhost:8000).',
    });
  }
  const fallback = {
    400: 'The backend could not process this file.',
    404: 'The analysis endpoint was not found.',
    413: 'The file is too large for the backend to accept.',
    415: 'The backend does not accept this file type.',
    422: 'The backend rejected the upload as invalid.',
    500: 'The backend hit an internal error while analysing the document.',
    502: 'The backend is unreachable through the proxy.',
    503: 'The analysis service is temporarily unavailable (the model may still be loading).',
    504: 'The backend took too long to respond.',
  };
  const hint =
    status === 404
      ? 'The requested session API route was not found. Check that the current Python backend is running.'
      : status >= 500
        ? 'Check the backend logs for details.'
        : null;
  const message = serverMessage || fallback[status] || `The backend responded with HTTP ${status}.`;
  return new AnalysisError('http', message, { status, hint });
}

async function request(path, init, signal) {
  const response = await fetch(apiUrl(path), { ...init, signal });
  if (!response.ok) throw httpErrorFor(response.status, await readErrorMessage(response));
  if (response.status === 204) return null;
  try {
    return await response.json();
  } catch {
    throw new AnalysisError('invalid-response', 'The backend response was not valid JSON.');
  }
}

function delay(ms, signal) {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(new AnalysisError('cancelled', 'Analysis cancelled.'));
      return;
    }
    const timer = setTimeout(done, ms);
    function done() {
      signal?.removeEventListener('abort', cancel);
      resolve();
    }
    function cancel() {
      clearTimeout(timer);
      signal?.removeEventListener('abort', cancel);
      reject(new AnalysisError('cancelled', 'Analysis cancelled.'));
    }
    signal?.addEventListener('abort', cancel, { once: true });
  });
}

async function analyzeWithBackend(file, signal) {
  const controller = new AbortController();
  let timedOut = false;
  let sessionId = null;
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, config.requestTimeoutMs);
  const onExternalAbort = () => controller.abort();
  signal?.addEventListener('abort', onExternalAbort);

  try {
    try {
      const body = new FormData();
      body.append('file', file, file.name);
      const created = await request('/api/sessions', {
        method: 'POST',
        body,
        headers: { Accept: 'application/json' },
      }, controller.signal);
      sessionId = asText(created?.id);
      if (!sessionId) {
        throw new AnalysisError('invalid-response', 'The backend did not return an analysis session ID.');
      }

      while (true) {
        if (signal?.aborted) throw new AnalysisError('cancelled', 'Analysis cancelled.');
        await delay(config.pollIntervalMs, controller.signal);
        const status = await request(`/api/sessions/${encodeURIComponent(sessionId)}/status`, {
          headers: { Accept: 'application/json' },
        }, controller.signal);
        const stage = asText(status?.status?.stage);
        if (stage === 'failed') {
          throw new AnalysisError('http', asText(status.status.error) || 'Document analysis failed.');
        }
        if (stage === 'done') break;
      }

      const result = await request(`/api/sessions/${encodeURIComponent(sessionId)}`, {
        headers: { Accept: 'application/json' },
      }, controller.signal);
      return normalizeAnalysis(result, sessionId);
    } catch (error) {
      if (sessionId && (signal?.aborted || timedOut)) {
        void fetch(apiUrl(`/api/sessions/${encodeURIComponent(sessionId)}`), { method: 'DELETE' }).catch(() => {});
      }
      if (timedOut) {
        throw new AnalysisError(
          'timeout',
          `The analysis did not finish within ${Math.round(config.requestTimeoutMs / 1000)} seconds.`,
          { hint: 'Large documents can take a while on a local model. Try a shorter document or raise VITE_API_TIMEOUT_MS.' },
        );
      }
      if (signal?.aborted) {
        throw new AnalysisError('cancelled', 'Analysis cancelled.');
      }
      if (error instanceof AnalysisError) throw error;
      throw new AnalysisError('network', 'Could not reach the analysis backend.', {
        hint: `Make sure the backend is running and reachable at ${apiUrl('/api/sessions')}. ${error?.message || ''}`.trim(),
      });
    }
  } catch (error) {
    if (error instanceof AnalysisError) throw error;
    if (timedOut) {
      throw new AnalysisError('timeout', 'The analysis timed out while reading the response.');
    }
    if (signal?.aborted) throw new AnalysisError('cancelled', 'Analysis cancelled.');
    throw new AnalysisError('network', error?.message || 'Unexpected error while contacting the backend.');
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener('abort', onExternalAbort);
  }
}

function normalizeCitation(value) {
  if (!value || typeof value !== 'object' || value.verified !== true) return null;
  const page = Number(value.page);
  const quoteStart = Number(value.quote_start);
  const quoteEnd = Number(value.quote_end);
  const quote = asText(value.quote);
  const clauseId = asText(value.clause_id);
  if (
    !quote
    || !clauseId
    || !Number.isInteger(page)
    || page < 1
    || !Number.isInteger(quoteStart)
    || quoteStart < 0
    || !Number.isInteger(quoteEnd)
    || quoteEnd <= quoteStart
  ) return null;
  return {
    verified: true,
    quote,
    clause_id: clauseId,
    page,
    quote_start: quoteStart,
    quote_end: quoteEnd,
  };
}

function normalizeAnswer(payload) {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    throw new AnalysisError('invalid-response', 'The backend returned an unexpected answer format.');
  }
  const answerStatuses = ['answered', 'partially_answered', 'document_silent'];
  if (!answerStatuses.includes(payload.answer_status)) {
    throw new AnalysisError('invalid-response', 'The backend answer is missing a valid answer status.');
  }
  if (
    !Array.isArray(payload.stated_in_document)
    || !Array.isArray(payload.possible_interpretations)
    || !Array.isArray(payload.concerns)
    || !Array.isArray(payload.uncertainty_notes)
    || typeof payload.escalation !== 'string'
  ) {
    throw new AnalysisError('invalid-response', 'The backend answer is missing required fields.');
  }
  const normalizeItems = (items, textKey) => (Array.isArray(items) ? items : [])
    .map((item) => {
      const citation = normalizeCitation(item);
      const text = asText(item?.[textKey]);
      return citation && text ? { ...citation, text } : null;
    })
    .filter(Boolean);

  return {
    answer_status: payload.answer_status,
    stated_in_document: normalizeItems(payload.stated_in_document, 'claim'),
    possible_interpretations: normalizeItems(payload.possible_interpretations, 'interpretation'),
    concerns: (Array.isArray(payload.concerns) ? payload.concerns : [])
      .map((item) => {
        const citation = normalizeCitation(item);
        const reason = asText(item?.reason);
        return citation && reason
          ? { ...citation, reason, severity: asText(item.severity) || 'unrated' }
          : null;
      })
      .filter(Boolean),
    uncertainty_notes: (Array.isArray(payload.uncertainty_notes) ? payload.uncertainty_notes : [])
      .map(asText)
      .filter(Boolean),
    escalation: asText(payload.escalation),
    statutory_background_available: payload.statutory_background_available === true,
  };
}

export function analyzeDocument(file, { signal } = {}) {
  return analyzeWithBackend(file, signal);
}

export async function askDocument(sessionId, question, { signal } = {}) {
  const payload = await request(`/api/sessions/${encodeURIComponent(sessionId)}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ question }),
  }, signal);
  return normalizeAnswer(payload);
}

export async function deleteSession(sessionId) {
  await request(`/api/sessions/${encodeURIComponent(sessionId)}`, { method: 'DELETE' });
}
