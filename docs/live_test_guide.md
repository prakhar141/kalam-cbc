# KALAM — Live Evaluation Guide
## For CBC Evaluators

### Try These Inputs in the CLI

TEST 1 — The pension threshold edge case
Run: python matching_engine.py
Look at Profile 3
Pension = ₹8,500 → PM Kisan = ELIGIBLE ✓
Pension = ₹10,500 → PM Kisan = NOT ELIGIBLE ✓
Why it matters: Most systems apply a blanket 
"retired govt employee = excluded" rule.
Our system checks the actual pension amount.

TEST 2 — Empty profile
Run matching_engine.py and check the empty profile test
Expected: 0 fully eligible, 14 partially eligible
Engine should not crash on missing data.

TEST 3 — Institutional landholder
Set land_ownership_type = "institutional"
Expected: PM Kisan = NOT ELIGIBLE
The 'in' operator checks ["individual", "joint"] only.

TEST 4 — AB-PMJAY with any income
Set annual_household_income_inr to any value
Expected: AB-PMJAY always routes to VERIFY MANUALLY
Income rules never evaluate for this scheme.
This is deliberate — SECC 2011 cannot be approximated.

TEST 5 — Age exactly 40 for APY
Set age = 40
Expected: APY = FULLY ELIGIBLE
The between operator is inclusive on both bounds.
PFRDA guideline says "18-40 years" — we interpret
as inclusive. Ambiguity documented in CSO_003.

### Questions You Can Ask Me

"Why is AB-PMJAY not rule-based?"
→ SECC 2011 is frozen. Income proxies give wrong answers.
   See architecture.md Decision 2.

"Why is confidence a ceiling not an average?"
→ One uncertain rule can invalidate a determination.
   See architecture.md Decision 3.

"What breaks your system?"
→ ADV_008: SVANidhi without certificate.
   Multi-state residence (ADV_006 partial).
   Joint family PM Kisan (DEF_005).
   All documented in ambiguity_map.py.

"What would v2 look like?"
→ DigiLocker API for document verification
   DILRMP land records API
   New operator type for alternative pathways
   See architecture.md Section 6.