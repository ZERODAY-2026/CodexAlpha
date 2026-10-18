import { Scale } from 'lucide-react';
import PrivacyBadge from './PrivacyBadge';

const NAV = [
  { href: '#upload', label: 'Upload' },
  { href: '#analysis', label: 'Analysis' },
  { href: '#about', label: 'Privacy & limits' },
];

export default function Header({ useMock, processing }) {
  return (
    <header className="site-header">
      <div className="container site-header__inner">
        <a className="brand" href="#top" aria-label="Private Legal Triage home">
          <span className="brand__mark" aria-hidden="true">
            <Scale size={20} />
          </span>
          <span className="brand__text">
            <span className="brand__name">Private Legal Triage</span>
            <span className="brand__tagline">Evidence-linked review of rental agreements and legal documents</span>
          </span>
        </a>

        <nav className="site-nav" aria-label="Main">
          <ul>
            {NAV.map((item) => (
              <li key={item.href}>
                <a href={item.href}>{item.label}</a>
              </li>
            ))}
          </ul>
        </nav>

        <PrivacyBadge useMock={useMock} processing={processing} />
      </div>
    </header>
  );
}
