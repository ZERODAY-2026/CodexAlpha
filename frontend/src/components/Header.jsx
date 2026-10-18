import { Scale } from 'lucide-react';

export default function Header() {
  return (
    <header className="site-header">
      <div className="container site-header__inner">
        <a className="brand" href="#top" aria-label="Private Legal Triage home">
          <span className="brand__mark" aria-hidden="true">
            <Scale size={20} />
          </span>
          <span className="brand__text">
            <span className="brand__name">Private Legal Triage</span>
            <span className="brand__tagline">Private document review</span>
          </span>
        </a>
      </div>
    </header>
  );
}
