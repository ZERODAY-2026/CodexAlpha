import { FlaskConical, ShieldCheck, ShieldQuestion } from 'lucide-react';

// Reports only what is actually known. The UI cannot itself guarantee privacy:
// on-device processing is shown as verified only when the backend says so.
export default function PrivacyBadge({ useMock, processing }) {
  if (useMock) {
    return (
      <span className="privacy-badge privacy-badge--demo" title="Demo mode does not read or upload your file.">
        <FlaskConical size={16} aria-hidden="true" />
        <span>Demo mode: file stays in this browser</span>
      </span>
    );
  }

  if (processing?.onDeviceVerified) {
    return (
      <span className="privacy-badge privacy-badge--verified" title="Reported by the analysis backend for the last request.">
        <ShieldCheck size={16} aria-hidden="true" />
        <span>Backend reports on-device processing{processing.model ? ` (${processing.model})` : ''}</span>
      </span>
    );
  }

  return (
    <span
      className="privacy-badge privacy-badge--unverified"
      title="The backend has not confirmed that processing stays on this device."
    >
      <ShieldQuestion size={16} aria-hidden="true" />
      <span>On-device processing not yet verified</span>
    </span>
  );
}
