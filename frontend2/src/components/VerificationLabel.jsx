import { CircleCheck, TriangleAlert } from 'lucide-react';
import StatusPill from './StatusPill';

export default function VerificationLabel({ verified }) {
  return verified ? (
    <StatusPill tone="success" icon={CircleCheck} title="The backend confirmed this quote appears in the document.">
      Evidence verified
    </StatusPill>
  ) : (
    <StatusPill tone="warning" icon={TriangleAlert} title="The backend did not confirm this quote against the document.">
      Unverified quote
    </StatusPill>
  );
}
