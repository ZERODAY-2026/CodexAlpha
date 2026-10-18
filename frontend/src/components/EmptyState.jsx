import { FileSearch } from 'lucide-react';

export default function EmptyState() {
  return (
    <section className="card empty-state">
      <FileSearch size={32} aria-hidden="true" />
      <h2 className="empty-state__title">No analysis yet</h2>
      <p className="muted">
        Upload a rental agreement or other legal document and select <strong>Analyze Document</strong>. You will see a
        summary, key clauses, potential concerns, and the exact passages each finding is based on.
      </p>
    </section>
  );
}
