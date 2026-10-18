import { describe, expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { isVerifiedCitation, JurisdictionWarningPanel } from './App';

describe('verified citations', () => {
  it('rejects unverified model quotes before they can be rendered', () => {
    expect(isVerifiedCitation({
      verified: false,
      quote: 'fabricated text',
      clause_id: 'p1-c001',
      page: 1,
      quote_start: 0,
      quote_end: 15,
    })).toBe(false);
  });

  it('accepts a quote only when the API marks it verified and supplies source offsets', () => {
    expect(isVerifiedCitation({
      verified: true,
      quote: 'The tenant shall pay rent.',
      clause_id: 'p1-c001',
      page: 1,
      quote_start: 0,
      quote_end: 26,
    })).toBe(true);
  });
});

describe('jurisdiction background warnings', () => {
  it('renders a distinct panel labelled as background and offers a clause highlight', () => {
    const markup = renderToStaticMarkup(createElement(JurisdictionWarningPanel, {
      warnings: [{
        rule_id: 'rental_security_deposit',
        clause_type: 'security deposit and refund',
        warning_text: 'Fixed background text.',
        triggering_clauses: [{ clause_id: 'p1-c001', page: 1 }],
        statutory_snapshot: 'v2026.08',
        statutory_background: [{
          act_title: 'Example Act',
          state: 'central',
          year: 2020,
          section_number: '4',
          section_title: 'Example provision',
          excerpt: 'Verbatim fixture excerpt.',
          status: 'in_force',
          snapshot: 'v2026.08',
          source_url: 'https://example.test/source',
        }],
      }],
      onHighlight: () => undefined,
    }));
    expect(markup).toContain('aria-label="Background — not from your document"');
    expect(markup).toContain('Background — not from your document');
    expect(markup).toContain('Fixed background text.');
    expect(markup).toContain('Highlight triggering clause p1-c001, page 1');
    expect(markup).toContain('Possibly relevant law (background only).');
    expect(markup).toContain('Possibly relevant law (background only). It may not apply to your situation, may have been amended since this snapshot, and is not a conclusion about your document. Check with a qualified local professional.');
    expect(markup).toContain('Dataset status: In Force');
    expect(markup).toContain('Dataset: Open India Law by Vaquill AI, CC BY 4.0.');
    expect(markup).toContain('target="_blank" rel="noopener noreferrer"');
    for (const forbidden of ['is legal', 'is illegal', 'is valid', 'is void', 'is enforceable']) {
      expect(markup.toLowerCase()).not.toContain(forbidden);
    }
  });
});
