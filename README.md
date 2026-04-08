
# KALAM — Welfare Scheme Matching Engine
## CBC BITS Pilani | Mission 03 | Backend
## KALAM — Key Metrics
════════════════════
15 schemes covered
29 ambiguities documented (13 HIGH severity)
9/10 adversarial tests passing (1 documented failure)
1 architecture decision that most systems get wrong
  (AB-PMJAY: database_membership, not rule_based)
Profile 3 pension edge case: PASSES
  (₹8,500 pension → eligible, ₹10,500 → not eligible)
Empty profile: handled without crash
  (0 eligible, 54 data gaps identified)

### What This Is
One paragraph. Problem, solution, what it does not do.

### Run It In 60 Seconds
pip install colorama
python kalam_cli.py          ← Start here (Hinglish conversation)
python matching_engine.py    ← See all 3 test profiles
python adversarial_profiles.py ← See 9/10 edge case results
python ambiguity_map.py      ← See 29 documented ambiguities

### The Most Important Test
python matching_engine.py
→ Look at Profile 3 output
→ PM Kisan should show FULLY ELIGIBLE
→ Pension is ₹8,500 — below ₹10,000 threshold
→ This is the edge case most systems get wrong

### File Map
schemes_database.py     — 15 scheme rules (read this first)
matching_engine.py      — core logic + 3 test profiles
ambiguity_map.py        — 29 contradictions documented
adversarial_profiles.py — 10 edge cases, 9/10 passing
kalam_cli.py            — Hinglish conversational interface
architecture.md         — technical decisions
confidence_audit.md     — every LOW confidence rule listed
prompt_log.md           — full iteration history

### The One Failure (ADV_008)
PM SVANidhi street vendor without certificate is incorrectly
routed to NOT ELIGIBLE instead of PARTIALLY ELIGIBLE.
Root cause and v2 fix documented in architecture.md Section 5.
This is documented deliberately — not hidden.
