Post-Write Self-Check: Confidence Audit Report
Fields Where I Have LOW Confidence
Scheme	Rule	Issue	Risk if Wrong
pmay_urban	MIG-I / MIG-II income ceilings	PMAY-U 2.0 rules not finalized. CLSS is discontinued. Old figures used as placeholder.	Users told they qualify for a benefit structure that no longer exists
janani_suraksha_yojana	B2 birth order restriction	Cannot confirm if the original HPS birth-order restriction is still enforced or has been removed	Either falsely excluding qualifying mothers (if removed) or falsely including (if still active)
Fields Where I Have MEDIUM Confidence (Most Important)
Scheme	Rule	Issue
ab_pmjay	All state expansion rules	50+ state schemes not encoded. Only central SECC rule modeled. A user in Gujarat asking about PMJAY-MA gets no answer.
pmmvy	A3 second-girl benefit	PMMVY 2.0 implementation varies by state. Some states haven't operationalized it.
janani_suraksha_yojana	A4_LPS / A4_HPS	LPS/HPS state list from 2005, may have been revised.
pmuy	A3 qualifying categories	PMUY 2.0 expanded categories via multiple circulars — the full list may be incomplete here.
nsap_ignoaps	B2 pension exclusion	Implemented differently across states — rule is an approximation of common practice.
The Three Structural Gaps I Cannot Fill Without External Data
text

1. SECC-2011 database lookups (AB-PMJAY, PMAY-G)
   → These require API access to NHA/MoRD databases
   → This file can only output "check the database" — not a yes/no

2. State-level pension top-up amounts (IGNOAPS)
   → Change every state budget cycle
   → Cannot be encoded in a static file

3. PMAY-U 2.0 rules
   → Guidelines not yet released as of knowledge cutoff
   → Entire MIG section should be considered provisional
What Must Happen Before Production Deployment
text

MANDATORY HUMAN REVIEW CHECKLIST:
□ JSY B2 birth order rule — verify current MoHFW circular
□ PMAY-U 2.0 — replace MIG rules when guidelines released  
□ AB-PMJAY state expansion rules — add state-specific rules file
□ PMMVY 2.0 state implementation matrix — add per-state status
□ LPS/HPS state classification — verify against current MoHFW list
□ APY EPF member exclusion — verify PFRDA master circular language
□ Sign CONFIDENCE_AUDIT["audited_by"] field with reviewer name + date
□ Run _validate_schemes_at_import() and confirm zero errors
□ Set DATABASE_VALID check in application startup to block deploy if False