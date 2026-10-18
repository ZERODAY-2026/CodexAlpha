import { Lock, Scale, ShieldQuestion } from 'lucide-react';

export default function AboutSection() {
  return (
    <section id="about" className="about" aria-labelledby="about-heading">
      <h2 id="about-heading" className="about__heading">Privacy and limits</h2>
      <div className="about__grid">
        <div className="about__item">
          <Lock size={20} aria-hidden="true" />
          <h3>Designed for on-device processing</h3>
          <p>
            Analysis is performed by a local Gemma model run by the project backend. This interface sends your file only
            to the configured backend address and never to a cloud AI service.
          </p>
        </div>
        <div className="about__item">
          <ShieldQuestion size={20} aria-hidden="true" />
          <h3>Privacy is verified by the backend</h3>
          <p>
            A label in this page cannot prove where processing happens. The header shows on-device processing as
            confirmed only when the backend reports it for your request.
          </p>
        </div>
        <div className="about__item">
          <Scale size={20} aria-hidden="true" />
          <h3>Not legal advice</h3>
          <p>
            Results are a preliminary reading to help you spot clauses worth checking. Findings can be wrong or
            incomplete. Always read the original passage and consult a qualified lawyer before acting.
          </p>
        </div>
      </div>
    </section>
  );
}
