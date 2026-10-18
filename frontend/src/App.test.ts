import { describe, expect, it } from 'vitest';
import { isVerifiedCitation } from './App';

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
