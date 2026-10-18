// DEMONSTRATION DATA ONLY. Used when the app runs in demo mode so the interface
// can be developed and shown before the backend is ready. It is not an analysis
// of any uploaded file, and the UI labels it as such everywhere it appears.

export const mockAnalysis = {
  document_type: 'Residential Rental Agreement',
  summary:
    'A 12-month residential lease for a two-bedroom apartment beginning 1 November 2026. The tenant pays monthly rent of ₹28,000 by the 5th of each month and a security deposit of two months’ rent. Either party may end the lease early with written notice, but the tenant faces a lock-in period and a late-payment fee. Maintenance duties are split between landlord and tenant, and the agreement is silent on how the deposit is returned.',
  clauses: [
    {
      id: 'clause-1',
      title: 'Rent and Payment Schedule',
      page: 1,
      source_quote:
        'The Tenant shall pay a monthly rent of Rs. 28,000 (Rupees Twenty-Eight Thousand only) on or before the 5th day of each calendar month by bank transfer to the account nominated by the Landlord.',
      explicit_meaning:
        'Rent is ₹28,000 per month, due by the 5th of every month, paid by bank transfer to the landlord’s chosen account.',
      potential_concern:
        'The landlord can nominate the account, but the clause does not say how a change of account must be communicated.',
      confidence: 'high',
      evidence_verified: true,
    },
    {
      id: 'clause-2',
      title: 'Late Payment Fee',
      page: 1,
      source_quote:
        'Any rent remaining unpaid after the due date shall attract a late fee of Rs. 500 per day until the date of payment.',
      explicit_meaning: 'A fee of ₹500 is charged for every day rent is paid after the 5th.',
      potential_concern:
        'There is no cap on the total late fee. Over a month this could exceed half the monthly rent; you may want to ask for a maximum.',
      confidence: 'high',
      evidence_verified: true,
    },
    {
      id: 'clause-3',
      title: 'Lock-in Period and Early Termination',
      page: 2,
      source_quote:
        'The Tenant may terminate this Agreement by giving two (2) months’ written notice, provided that no such notice shall be given during the first six (6) months (the “Lock-in Period”).',
      explicit_meaning:
        'The tenant can end the lease with two months’ written notice, but not during the first six months.',
      potential_concern:
        'The clause does not say what happens if the tenant must leave during the lock-in period, for example whether the remaining rent becomes payable.',
      confidence: 'medium',
      evidence_verified: true,
    },
    {
      id: 'clause-4',
      title: 'Termination by Landlord',
      page: 2,
      source_quote:
        'The Landlord may terminate this Agreement with one (1) month’s notice in the event of any breach of the terms herein by the Tenant.',
      explicit_meaning:
        'The landlord can end the lease with one month’s notice if the tenant breaches any term.',
      potential_concern:
        '“Any breach” is broad and could include minor issues. There is no opportunity to fix the breach before notice is given.',
      confidence: 'medium',
      evidence_verified: true,
    },
    {
      id: 'clause-5',
      title: 'Security Deposit',
      page: 3,
      source_quote:
        'The Tenant has paid an interest-free security deposit of Rs. 56,000, which shall be refunded subject to deductions for damages at the time of vacating.',
      explicit_meaning:
        'A ₹56,000 interest-free deposit is refundable when the tenant leaves, minus deductions for damage.',
      potential_concern:
        'No refund deadline is stated, and “damages” is not defined, so normal wear and tear could be deducted.',
      confidence: 'medium',
      evidence_verified: false,
    },
    {
      id: 'clause-6',
      title: 'Maintenance and Repairs',
      page: null,
      source_quote:
        'Minor repairs up to Rs. 2,000 per instance shall be borne by the Tenant. Structural repairs shall be the responsibility of the Landlord.',
      explicit_meaning:
        'The tenant pays for minor repairs up to ₹2,000 each; the landlord is responsible for structural repairs.',
      potential_concern:
        'It is unclear who decides whether a repair is minor or structural, and there is no limit on how many minor repairs the tenant must cover.',
      confidence: 'low',
      evidence_verified: true,
    },
  ],
  missing_information: [
    'No deadline for returning the security deposit after the tenant vacates.',
    'Rent escalation at renewal is not mentioned.',
    'Page 4 appears to contain a signature block only; no witness details were found.',
  ],
  disclaimer:
    'This tool provides preliminary document understanding only and does not provide definitive legal advice. Consult a qualified lawyer before acting on any finding.',
};
