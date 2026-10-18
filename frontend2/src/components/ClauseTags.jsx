import { CalendarClock, ClipboardList, DoorOpen, Gavel } from 'lucide-react';
import StatusPill from './StatusPill';
import { TAGS } from '../utils/clauseTags';

const ICONS = {
  obligation: ClipboardList,
  deadline: CalendarClock,
  penalty: Gavel,
  termination: DoorOpen,
};

export default function ClauseTags({ tags }) {
  if (!tags?.keys?.length) return null;
  const title = tags.source === 'keyword' ? 'Detected by keyword match, not by the model' : 'Category reported by the backend';
  return (
    <span className="tag-row">
      {tags.keys.map((key) => (
        <StatusPill key={key} tone={TAGS[key].tone} icon={ICONS[key]} title={title}>
          {TAGS[key].label}
        </StatusPill>
      ))}
    </span>
  );
}
