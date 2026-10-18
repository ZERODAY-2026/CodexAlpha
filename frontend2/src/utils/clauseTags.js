// Clause tags used to highlight obligations, deadlines, penalties and termination
// conditions. If the backend sends `category`/`tags`, those win; otherwise we fall
// back to a simple keyword match on the clause text. Keyword tags are a reading aid
// only and are labelled as such in the UI.

export const TAGS = {
  obligation: { label: 'Obligation', plural: 'Obligations', tone: 'info' },
  deadline: { label: 'Deadline', plural: 'Deadlines', tone: 'warning' },
  penalty: { label: 'Penalty', plural: 'Penalties', tone: 'danger' },
  termination: { label: 'Termination', plural: 'Terminations', tone: 'neutral' },
};

const KEYWORDS = {
  obligation: /\b(shall|must|obliged|obligation|responsible for|required to|agrees? to|undertakes?)\b/i,
  deadline: /\b(within \d+|days?|weeks?|months?|by the \d+|due|deadline|no later than|before the|notice period|on or before)\b/i,
  penalty: /\b(penalt(y|ies)|fine|late fee|forfeit|deduct|liquidated damages|interest at|charge of|surcharge)\b/i,
  termination: /\b(terminat(e|ion|ed)|evict(ion)?|vacate|end the (lease|agreement|tenancy)|break clause|cancel(lation)?)\b/i,
};

function normalizeKey(value) {
  const key = String(value || '').trim().toLowerCase();
  if (key.startsWith('oblig')) return 'obligation';
  if (key.startsWith('deadl') || key === 'date' || key === 'timeline') return 'deadline';
  if (key.startsWith('penal') || key === 'fee' || key === 'fine') return 'penalty';
  if (key.startsWith('termin')) return 'termination';
  return null;
}

export function getClauseTags(clause) {
  const fromBackend = [clause.category, ...(Array.isArray(clause.tags) ? clause.tags : [])]
    .map(normalizeKey)
    .filter(Boolean);
  if (fromBackend.length > 0) {
    return { keys: [...new Set(fromBackend)], source: 'backend' };
  }

  const text = [clause.title, clause.explicit_meaning, clause.source_quote].join(' ');
  const keys = Object.keys(KEYWORDS).filter((key) => KEYWORDS[key].test(text));
  return { keys, source: 'keyword' };
}
