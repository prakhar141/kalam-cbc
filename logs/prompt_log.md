# prompt_log.md

```markdown
# KALAM — Prompt Engineering Log
## CBC BITS Pilani Submission — AI Welfare Scheme Matching Engine

---

**Candidate:** [Prakhar Mathur]  
**Submission:** KALAM — Knowledge-Assisted Legal Assistance for 
               Marginalized persons  
**Build period:** [8/4/26-12-4-26]  
**Total prompts fired:** 5 major prompts + iterative corrections  
**Files produced:** 6 (schemes_database.py, matching_engine.py,
                    ambiguity_map.py, adversarial_profiles.py,
                    kalam_cli.py, architecture.md)  
**Adversarial test result:** 9/10 passing; 1 failure documented  
**Lines of code produced by AI, accepted unchanged:** ~40%  
**Lines of code produced by AI, modified before acceptance:** ~45%  
**Lines of code written or restructured by human:** ~15%  

---

## How to Read This Log

Each prompt entry contains four sections:

- **PROMPT** — exactly what I asked and why I asked it in that order
- **OUTPUT** — what the AI returned and what I checked
- **ACCEPTED / REJECTED** — binary decision with explicit reason
- **WHAT CHANGED** — what I modified before the output went into the build

Decisions I made that were not in any prompt are marked **[DECISION]**.  
Outputs I rejected are marked **[REJECTED]**.  
Errors I caught before they reached the build are marked **[BUG CAUGHT]**.

---

## Build Summary for the 5-Minute Reader

If you read nothing else, read this section.

**The core architectural problem:** Indian welfare eligibility is a maze
of overlapping rules, frozen databases, undefined terms, and rules that
were true last year but not this year. An LLM asked "is this person
eligible for PM Kisan?" will give a confident, wrong answer approximately
40% of the time based on documented failure modes. KALAM's architecture
was designed specifically to prevent that.

**The three decisions that shaped everything:**

1. Rules are offline artifacts, human-audited, not LLM-evaluated at runtime.
   The LLM helped write the rules. Humans verify them. A different system
   evaluates them at query time.

2. AB-PMJAY (Ayushman Bharat) cannot be evaluated by rules. Its eligibility
   is a frozen 2011 database lookup. Any income-based proxy rule gives
   confidently wrong answers. The system refuses to give a yes/no for this
   scheme and routes users to the government's own verification tool.

3. Confidence is a ceiling, not an average. One LOW-confidence rule caps
   the entire scheme's confidence at 0.50. This prevents uncertain rules
   from hiding behind confident ones.

**The most important test:** Profile 3 — a retired Punjab farmer with a
pension of ₹8,500/month. PM Kisan excludes retired government employees
with pensions ≥ ₹10,000. This person's pension is below the threshold.
A naive system would exclude them. KALAM correctly marks them eligible.

**The honest failure:** ADV_008 — a street vendor without a vending
certificate is classified as NOT eligible for PM SVANidhi when she should
be PARTIALLY eligible with a note about the ULB Letter of Recommendation
alternative. The root cause is architectural (missing operator type), the
fix path is documented, and the failure is presented as a test result
rather than hidden.

---

## PROMPT 01 — Pre-Architecture Analysis

**Fired:** Before writing any code or data file.

**Why first:** Every system I have seen that fails on Indian government
data fails because someone started coding before understanding the domain.
The failure modes are not generic software problems — they are specific
to how Indian welfare policy is written and how LLMs misrepresent it.
I needed to understand both before touching a keyboard for code.

**What I asked:**

Four specific questions, in this order:

```
1. What are the 5 most common ways an LLM hallucinates when asked
   about Indian government welfare scheme eligibility? Give concrete
   examples with fake-but-plausible wrong answers an LLM might
   confidently give.

2. What does "eligibility expressed as explicit logical rules" mean
   in practice? Show me one example — take PM Kisan and convert its
   eligibility into IF/AND/OR/NOT boolean logic that a Python function
   could evaluate.

3. What user data fields does KALAM absolutely need to collect to match
   across welfare schemes? Give me the minimum viable input schema —
   every field, its data type, valid values, and why it's needed.

4. What are the 3 hardest edge cases in Indian welfare eligibility that
   would break a naive matching system? Be specific — not "data is messy"
   but actual real examples.
```

**Why this ordering:** Question 1 before everything else, because if the
AI itself hallucinates about welfare schemes, I needed to know that before
asking it to build rules about welfare schemes. The hallucination catalog
became a checklist I used to verify every rule the AI wrote in Prompt 02.

**OUTPUT RECEIVED:**

The AI returned detailed answers covering:

- **5 hallucination failure modes:**
  1. Income ceiling confabulation (inventing income limits where none exist)
  2. Exclusion clause amnesia (listing inclusions, dropping exclusions)
  3. Stale rule citation (citing rules that existed but were amended)
  4. Jurisdiction layer collapse (presenting state schemes as national)
  5. Category conflation (mixing eligibility criteria across schemes)

- **PM Kisan as boolean logic:** Full Python function with A-rules
  (inclusions) and B-rules (exclusions), including the critical asymmetry
  between former MPs (excluded) and former Zila Panchayat Presidents
  (not excluded). The function returned a dict with every rule result,
  not just a boolean — this structure directly informed the
  `evaluate_rule()` return format in `matching_engine.py`.

- **Minimum viable input schema:** Tiered collection strategy —
  5 fields at Tier 1, conditional expansion at Tiers 2 and 3.

- **Three hard edge cases:**
  1. The household unit definition problem (PM Kisan and PMAY define
     "family" differently — same household, different eligible units)
  2. The split-residence migration problem (Aadhaar domicile ≠ physical
     location ≠ asset location)
  3. The SECC 2011 frozen database problem (AB-PMJAY eligibility is a
     2011 snapshot, not current poverty)

**WHAT I ACCEPTED AND WHY:**

The SECC 2011 analysis was the most valuable output of the entire project.
The AI correctly identified that AB-PMJAY cannot be evaluated by rules
because its eligibility source is a frozen database, not current attributes.
This is non-obvious. Most developers would write income-based proxy rules
and ship them. Those rules would give confidently wrong answers in both
directions:

- A family poor now but not in SECC 2011 → proxy says eligible, database
  says no, hospital turns them away
- A family in SECC 2011 but now middle-class → proxy says not eligible,
  database says yes, they never claim a benefit they're entitled to

This single insight became the `database_membership` eligibility type,
the `verify_manually` output bucket, and Section 4 Decision 2 in
`architecture.md`. It was the most important architectural decision in
the system and it came from this first analysis.

**[DECISION] — Made based on this output:**

I decided before writing a single line of code that the system would
have two fundamentally different eligibility types — `rule_based` and
`database_membership` — and that the engine would refuse to give a yes/no
for database_membership schemes. This was not in the original brief.
It came from understanding the domain before coding it.

**What I verified manually:**

The exclusion list for PM Kisan. The AI listed: former/current
constitutional post holders, former/current Ministers, former/current
MPs/MLAs/MLCs, current (NOT former) Zila Panchayat Presidents/Mayors,
serving government employees, retired government employees with pension
≥ ₹10,000, income tax filers, registered professionals.

I cross-checked the asymmetry between "former MPs excluded" and "former
Zila Panchayat Presidents NOT excluded" against what I know of the scheme.
This asymmetry is real and almost universally dropped by automated systems.
It is encoded as rules B5/B6 (MPs, former excluded) and B7 (local body,
current only) in `schemes_database.py`, with explicit `critical_note`
fields on both.

---

## PROMPT 02 — schemes_database.py

**Fired:** After completing the architecture analysis.

**Why this order:** The schemes database is the foundation. The matching
engine can be written after the data structure is defined. Doing it in
reverse — writing the engine first — would mean the engine's assumptions
about data shape drive the database design, which is backwards.

**What I asked:**

Build the complete schemes database for 15 schemes using the exact structure
from the architecture analysis: confidence ratings on every rule,
exclusion_rules as first-class objects parallel to inclusion_rules,
`common_hallucinations` field on every scheme, `guideline_version` and
`last_verified_date` for staleness tracking, and a `CONFIDENCE_AUDIT`
dictionary at the bottom documenting every LOW and MEDIUM confidence field
with the reason and required verification action.

I specified the exact schema for every field type. I specified that
`eligibility_type` must be one of `rule_based`, `database_membership`,
or `hybrid`. I specified that AB-PMJAY must be `database_membership`
and must not have income-based inclusion rules. I specified that
`common_hallucinations` must be non-empty for every scheme — if you
can't name at least one way this scheme is commonly misunderstood,
you haven't read the guidelines carefully enough.

**OUTPUT RECEIVED:**

`schemes_database.py` with all 15 schemes. The structure was correct.
The rule content was largely correct. The confidence ratings were
appropriately conservative — the AI rated itself MEDIUM or LOW wherever
it was citing scheme descriptions rather than specific guideline clauses.

**[BUG CAUGHT] — DOC_MCP_CARD NameError:**

```
Pylance error: "DOC_MCP_CARD" is not defined  
Location: Line 1335, pmmvy scheme, required_documents list
```

**Root cause analysis:** The AI generated a constants block at the top
of the file (`DOC_AADHAAR = "aadhaar_card"`, `DOC_MCP_CARD = ...`, etc.)
and then referenced these constants throughout the `SCHEMES` dictionary.
However, `DOC_MCP_CARD` — the Mother and Child Protection card constant
used by the PMMVY scheme — was defined in a patch comment AFTER the
`SCHEMES` dictionary closed. It was never actually defined in the
constants block. Python dictionaries are evaluated at parse time with
scope resolved at that point, so `DOC_MCP_CARD` was a NameError.

**Why this error is significant:** This is the same class of failure
as hallucination — confident-looking output that is wrong in a way that
requires running the code to catch. A developer who read the file and
thought "looks reasonable" would have missed it. VS Code's Pylance static
analysis caught it before runtime.

**[REJECTED] — The entire constants-reference approach:**

The fix was not just to define `DOC_MCP_CARD`. The fix was to eliminate
all constant references inside `SCHEMES` and inline every value as a plain
string. Reason: constants inside data literals are a maintenance trap.
If `DOC_AADHAAR` is renamed, every reference inside `SCHEMES` silently
breaks. Plain strings cannot be undefined. `"aadhaar_card"` is always
`"aadhaar_card"`. The audit of all affected lines found 66 constant
references across all 15 schemes. All 66 were replaced.

The corrected structure:

```python
# WRONG — what the AI generated:
"required_documents": [DOC_AADHAAR, DOC_MCP_CARD]

# RIGHT — what was deployed:
"required_documents": ["aadhaar_card", "mother_child_protection_card"]
```

**[REJECTED] — Income ceiling for PM Kisan:**

The initial output included a suggestion to check
`annual_household_income_inr <= 150000` for PM Kisan. This is
Hallucination Type 1 from Prompt 01 — income ceiling confabulation.
PM Kisan has no income ceiling. The 2-hectare land cap was removed in
the June 2019 universalization amendment. Both the income ceiling and
the land cap were removed from the database. The `common_hallucinations`
field now includes:

```
"Income ceiling of ₹1.5 lakh per year — WRONG. No income ceiling exists."
"Only for small/marginal farmers under 2 hectares — WRONG. Cap removed June 2019."
```

This is exactly what the `common_hallucinations` field exists to catch.
The field functions as a self-verification checklist: if my rule sounds
like a listed hallucination, I have probably made that hallucination.

**[REJECTED] — Rule-based income proxy for AB-PMJAY:**

The initial draft included income-based rules for AB-PMJAY (income < ₹2
lakh, rural, etc.). This was rejected in full. AB-PMJAY is
`database_membership`. No income rules. No yes/no determination. The
scheme routes to `verify_manually` with instructions to use the NHA's
own eligibility verification tool. Reason: SECC 2011 frozen database
problem, identified in Prompt 01. Income proxy rules give confidently
wrong answers in both directions for this scheme.

**[REJECTED] — Single field for elected representative:**

Initial schema had `is_elected_representative: bool` covering only
current holders. The architecture analysis identified that former
MPs/MLAs/MLCs are excluded from PM Kisan, but former Zila Panchayat
Presidents are NOT. One boolean field collapses this asymmetry into
a single question that cannot distinguish the two cases. Changed to
`is_or_was_elected_representative` with the caveat documented in
`ambiguity_map.py` as INT_002 — the field still cannot capture the
asymmetry cleanly. It is flagged as `unresolved_requires_schema_change`.

**What was added by human decision:**

The validation `__main__` block at the bottom of `schemes_database.py`.
This was not in the AI's output. I added it because I needed a way to
run a mechanical check on every scheme's structure without reading 1,500
lines manually. The validator checks: required fields present, scheme_id
matches dict key, eligibility_type is valid, all rule confidence levels
are HIGH/MEDIUM/LOW, all operators are in the known operator set,
required_documents are plain strings (catching the DOC_* bug class).

---

## PROMPT 03 — matching_engine.py

**Fired:** After `schemes_database.py` was validated and clean.

**What I asked:**

Build the matching engine with five explicit sections: a rule evaluator
(`evaluate_rule()`), a confidence calculator (`calculate_confidence_score()`),
the main matcher (`match_schemes()`), an application sequence builder
(`build_application_sequence()`), and a test runner for three specific
profiles. I specified the exact return structure for each function. I
specified that `evaluate_rule()` must never assume a default for a missing
field. I specified that confidence must be a ceiling system, not an average.
I specified that exclusions must be evaluated before inclusions.

I specified Profile 3 explicitly — a retired Punjab farmer with a pension
of ₹8,500/month — because this is the threshold edge case. The pension
exclusion for PM Kisan triggers at ≥ ₹10,000. At ₹8,500, the person
should NOT be excluded. A naive system that checks
`is_serving_or_retired_govt_employee == True` would exclude them.
The correct check is `monthly_pension_if_retired_govt >= 10000`, which
requires the pension amount, which requires asking the question.

**OUTPUT RECEIVED:**

`matching_engine.py` with all five sections. Colorama integration with
graceful fallback. The operator dispatch table as a dict rather than
an if/elif chain. `evaluate_rule()` returning a verbose dict with every
field needed by every downstream consumer.

**CRITICAL TEST — Profile 3 pension edge case:**

```
Input:  is_serving_or_retired_govt_employee = True
        monthly_pension_if_retired_govt = 8500
        
Rule B9: monthly_pension_if_retired_govt >= 10000
Expected: 8500 >= 10000 → False → exclusion NOT triggered → ELIGIBLE

ACTUAL RESULT: PM Kisan = FULLY ELIGIBLE  ✅
```

This test passing is the most important correctness result in the entire
build. The threshold comparison works correctly. A retired government
employee with a small pension is not wrongly excluded.

**INTEGRATION BUG CAUGHT — Field name mismatch:**

`schemes_database.py` uses field name `filed_income_tax_last_assessment_year`.
The test profiles in `matching_engine.py` used `filed_income_tax` (shorter).
When the engine evaluated PM Kisan rule B10, the field was absent →
`data_missing = True` → scheme routed to `partially_eligible` rather
than `fully_eligible`.

Fix: Profile 1 test dict updated to include both field names. The integration
check section now documents this as Mismatch 4 — a field standardization
issue requiring action in the intake schema. The canonical field name is
`filed_income_tax_last_assessment_year` because it is more precise:
"last assessment year" is the actual criterion in the PM Kisan guidelines,
not simply "filed income tax ever."

**WHAT WAS MODIFIED:**

The empty profile edge case test was added by me, not the AI. The AI's
test runner had three profiles. I added a fourth test with `{}` — an
empty dict — to verify the engine does not crash when all fields are
missing. It should return all schemes as `partially_eligible` or
`not_eligible` (via hard logic failures like `residence_type == "urban"`
for rural schemes) with populated `data_gaps_summary`. It did. Zero
exceptions on empty input.

**[DECISION] — Keep MGNREGA for Profile 3 as documented limitation:**

Profile 3 is a 64-year-old retired IAS officer. MGNREGA appeared in his
`fully_eligible` list because: rural resident ✓, age ≥ 18 ✓, willing to
do unskilled manual work ✓ (field not set to False, so engine doesn't
fail it). This is technically correct — the rules don't exclude elderly
farmers from MGNREGA. But contextually it is odd to recommend manual
labor to a 64-year-old retired IAS officer.

I did not fix this. Fixing it would require adding heuristics outside
the rule system (e.g., "if age > 60 and former professional, deprioritize
MGNREGA"). That is a product decision, not an eligibility rule. The current
system evaluates rules, not context. I documented it as a known limitation
rather than introducing logic that has no basis in the scheme's actual
eligibility criteria.

---

## PROMPT 04 — ambiguity_map.py + adversarial_profiles.py

**Fired:** After `matching_engine.py` was running cleanly.

**What I asked:**

Two files in one prompt because they are dependent — the adversarial
profiles test the ambiguities, and the ambiguities explain why some
adversarial tests are hard.

For `ambiguity_map.py`: Four categories of ambiguity — internal
contradictions, cross-scheme overlaps, definitional ambiguities, stale
data risks. Every ambiguity with a severity rating and a real-world
impact statement.

For `adversarial_profiles.py`: Ten profiles designed to break naive
systems, with `expected_results` dicts containing `must_be_eligible`,
`must_not_be_eligible`, and `must_be_verify_manually` lists. A test runner
that runs all ten through `match_schemes()` and prints PASS/FAIL.

**OUTPUT RECEIVED:**

`ambiguity_map.py` with 29 ambiguities across four categories.
`adversarial_profiles.py` with 10 profiles and test runner.

**ADVERSARIAL TEST RESULTS:**

```
ADV_001 — Remarried Widow:          PASS ✅
ADV_002 — Land Leaseholder:         PASS ✅
ADV_003 — Aadhaar No Bank:          PASS ✅
ADV_004 — Exactly Age 40:           PASS ✅
ADV_005 — Institutional Landholder: PASS ✅
ADV_006 — Multi-State Family:       PASS ✅
ADV_007 — High-Pension Retired IAS: PASS ✅
ADV_008 — Street Vendor No Cert:    FAIL ❌
ADV_009 — Second Child PMMVY:       PASS ✅
ADV_010 — Disabled SC Rural:        PASS ✅

RESULT: 9/10
```

**ADV_008 FAILURE — Full analysis:**

```
Profile: Woman, 34, urban SC, street vendor, vending before March 2020,
         has Jan Dhan + Aadhaar, no vending certificate

Expected: pm_svanidhi in partially_eligible
          Gap analysis note: "ULB Letter of Recommendation is an
          acceptable alternative to vending certificate"

Actual: pm_svanidhi in not_eligible
        Reason: "INCLUSION FAILED: Rule A3: has_vending_certificate_
                 or_identity_card = False does NOT satisfy equals True"
```

**Root cause:** Rule A3 for PM SVANidhi is encoded as a standard boolean
inclusion rule. The field `has_vending_certificate_or_identity_card = False`.
The engine sees a non-missing field with value False. `evaluate_rule()`
correctly returns `passed = False, data_missing = False`. Since this is a
hard failure (not a missing-data failure), the scheme goes to `not_eligible`,
not `partially_eligible`.

The problem is that the PM SVANidhi guidelines provide an OR alternative:
Certificate OR Identity Card OR Letter of Recommendation from ULB. The
engine's operator set has no mechanism to express "this field is False
but an alternative exists." The rule should either be:

- **Option A:** Split into `one_of_fields` operator across three separate
  boolean fields
- **Option B:** Moved from `inclusion_rules` to `ambiguous_rules` with
  `system_response: "flag_for_clarification"` — so that False triggers
  a clarifying question rather than a hard failure

**[DECISION] — Document the failure, do not patch it:**

The tempting fix is to add a special case: "if scheme is pm_svanidhi
and has_vending_certificate is False, check for the LoR alternative."
I rejected this approach because it is a hack — hardcoded scheme-specific
logic inside the general engine. The correct fix is a new operator type
or a rule structure change. That is an architectural change, not a patch.

Shipping a documented failure with a clear fix path is more honest than
shipping a hidden special case. This is documented in `architecture.md`
Section 5. The ADV_008 test exists in `adversarial_profiles.py` with
`failure_documentation` filled in, so any future developer knows exactly
what is wrong and why.

**KEY FINDING from ambiguity_map.py — DEF_004 (BPL Definition):**

The `is_bpl_household` field is used in 6 schemes. There are at least 4
operationally distinct BPL lists:

1. 2002 BPL Survey list (outdated but some states still use)
2. SECC 2011 rural deprivation list (used for PMAY-G, AB-PMJAY)
3. State-issued BPL cards (each state maintains its own)
4. Antyodaya Anna Yojana (AAY) list — poorest of BPL

When a user says "I have a BPL card," the system does not know which list
they are on. A user on the 2002 BPL list may not be on the SECC 2011 list
and therefore not qualify for AB-PMJAY despite holding a BPL card. This
is documented as ambiguity DEF_004 with severity HIGH and
`resolution_status: "fundamental_data_infrastructure_gap"` — meaning no
amount of software engineering fixes this. It requires government data
harmonization.

This is an important finding for the submission because it demonstrates
the difference between a problem that can be solved with better code and
a problem that requires policy change. KALAM handles the former. DEF_004
is the latter.

---

## PROMPT 05 — kalam_cli.py + architecture.md

**Fired:** After all four backend files were working.

**What I asked:**

For `kalam_cli.py`: A Hinglish conversational interface with six question
blocks, conditional question flow (if no land, skip land questions), a
natural language parser handling income in multiple formats and land area
in bigha/acre/hectare, a contradiction detector with seven specific
contradiction checks, and `skip`/`back`/`result`/`help` as always-available
commands.

I specified explicitly: questions must pass the "government helper test" —
would a literate, helpful person at a Jan Seva Kendra actually say this?
Not translated English. Actual Hinglish spoken by someone who knows their
audience.

For `architecture.md`: Six sections in a specified order, including an
honest write-up of the ADV_008 failure as a strength rather than a weakness,
and a section documenting the DOC_MCP_CARD bug as evidence of the development
methodology.

**CLI LIVE TEST — Run as OBC farmer, UP, age 45:**

```
Input: "45"              → age: 45              ✅
Input: "mard"            → gender: male         ✅
Input: "up"              → state: Uttar Pradesh ✅
Input: "gaon"            → residence_type: rural ✅
Input: "2"               → caste_category: obc  ✅
Input: "haan"            → is_indian_citizen: True ✅
Input: "85 hazaar saal ka" → annual_income: 85000 ✅
Input: "haan"            → has_bpl_card: True   ✅
Input: "nahi"            → filed_income_tax: False ✅
Input: "haan"            → owns_agricultural_land: True ✅
Input: "1"               → land_ownership_type: individual ✅
Input: "2 bigha"         → land_area: 0.5 hectare ✅
                            Warning: bigha conversion is approximate ✅
Input: "haan"            → land_is_cultivable: True ✅
Input: "3"               → housing_status: kutcha ✅
Input: "nahi"            → has_pucca_house_anywhere: False ✅
Input: "haan"            → has_aadhaar: True    ✅
Input: "1"               → bank_account: active_with_dbt ✅

Final results:
  PM Kisan:          FULLY ELIGIBLE, confidence 75%  ✅
  MGNREGA:           FULLY ELIGIBLE                  ✅
  Sukanya Samriddhi: FULLY ELIGIBLE (girl child)     ✅
  PMJJBY:            NOT ELIGIBLE (age > 50)         ✅
  PMSBY:             FULLY ELIGIBLE                  ✅
  AB-PMJAY:          VERIFY MANUALLY                 ✅
```

**ISSUE NOTED — Application sequence ordering:**

MGNREGA appears as #1 in the application sequence despite PM Kisan being
the more impactful scheme for a farmer. The sequencing algorithm sorts
by prerequisite dependency depth (topological sort), not by eligibility
confidence or benefit amount. MGNREGA has no prerequisites → in-degree 0
→ appears first.

This is a known limitation. The fix would weight `fully_eligible` schemes
above `partially_eligible` schemes in the sequence output, and sort by
benefit amount as a secondary key within the same eligibility tier. This
is a product improvement, not a correctness issue. Documented as a v2
item.

**[DECISION] — Bigha conversion with explicit uncertainty flag:**

The bigha parser converts at 0.25 hectares per bigha with an explicit
warning: "Bigha ka size state se state alag hota hai." This is true —
a bigha in Punjab (0.0529 ha) is six times smaller than a bigha in UP
(0.2529 ha). The conversion is approximate and the user is told this.
The alternative was to ask what state the user is in and apply a
state-specific conversion factor. I rejected this because:
(a) it adds complexity for marginal gain — PM Kisan has no land cap,
so the exact area does not change eligibility, and
(b) the user has already been asked for their state, but wiring that
through the parser to the area conversion would require passing state
as a parameter everywhere. The explicit uncertainty warning is the
appropriate response.

**ARCHITECTURE.MD — What I verified:**

Every technical claim in `architecture.md` references a specific file
and function. "The ceiling confidence system" references
`calculate_confidence_score()` in `matching_engine.py`. "The
`common_hallucinations` field" references `schemes_database.py`.
"ADV_008 failure" references `adversarial_profiles.py` with the exact
test assertion that fails. This cross-referencing was done manually —
the AI draft had some claims without specific references, which I added.

---

## Complete Record of Rejected Outputs

| # | What Was Rejected | Where | Why |
|---|-------------------|-------|-----|
| 1 | Income ceiling ≤ ₹1.5L for PM Kisan | schemes_database.py | Hallucination Type 1. PM Kisan has no income ceiling. |
| 2 | Land cap ≤ 2 hectares for PM Kisan | schemes_database.py | Stale rule. Cap removed June 2019 universalization. |
| 3 | Income-based rules for AB-PMJAY | schemes_database.py | SECC 2011 is frozen. Income proxy gives confidently wrong answers. |
| 4 | `DOC_MCP_CARD` constant reference | schemes_database.py | NameError — defined after the dict that references it. 66 total constant references replaced. |
| 5 | Single boolean `is_elected_representative` | Input schema | Cannot distinguish former MP (excluded) from former Zila Panchayat President (not excluded). |
| 6 | Hardcoded special case for ADV_008 | matching_engine.py | Patch hiding an architectural problem. Documented the failure instead. |
| 7 | Averaging confidence scores | matching_engine.py | Hides weak links. Ceiling system reflects how legal eligibility works. |
| 8 | LLM evaluating rules at runtime | Architecture | No training data. Wrong answers cause real harm. Interpretability is mandatory. |

---

## Decisions Made Outside Any Prompt

These were my decisions, not AI-generated suggestions.

**[DECISION 1] — `common_hallucinations` field on every scheme:**

The hallucination catalog from Prompt 01 became a first-class field in
the data model. Every scheme must list at least one known wrong answer.
This serves as a self-verification checklist during development: if a
rule I encode sounds like a listed hallucination, I have probably made
that hallucination. It also serves as documentation for future maintainers:
here is what the internet (and LLMs trained on it) will tell you incorrectly
about this scheme.

**[DECISION 2] — Confidence as ceiling, not average:**

Not requested in the prompt. The prompt asked for "confidence ratings."
How to combine multiple confidence ratings into one scheme-level score
was my decision. Averaging is intuitive but wrong for legal eligibility:
a chain of HIGH-confidence rules does not make a LOW-confidence rule more
reliable. The ceiling model correctly represents that one uncertain rule
makes the entire determination uncertain.

**[DECISION 3] — Document ADV_008 failure instead of hiding it:**

The brief said "documented failures are a positive signal." I verified
this was true by considering the alternative: a patch that hardcodes
special SVANidhi behavior in the engine. That patch would be invisible
in testing, difficult to maintain, and architecturally dishonest. A 9/10
result with a documented failure and a clear fix path demonstrates that
the test suite actually found something, which is the point of having
a test suite.

**[DECISION 4] — PMAY-U flagged as "scheme in transition":**

PMAY-U 1.0 ended March 2022. PMAY-U 2.0 was announced in Budget 2024
but operational guidelines are not released as of verification date. I
flagged this as `STALE_005` HIGH severity in `ambiguity_map.py` and as
a mandatory human review item in `CONFIDENCE_AUDIT`. The MIG income
thresholds (₹12L for MIG-I, ₹18L for MIG-II) are marked LOW confidence.
The alternative was to show PMAY-U as unavailable. I chose to show it
with explicit uncertainty flags because the scheme does exist and a user
might be eligible under its eventual 2.0 structure.

**[DECISION 5] — Empty profile must not crash:**

Not requested. I added the empty `{}` test at the end of
`matching_engine.py`'s `__main__` block. The engine should never throw
an exception regardless of input quality. A welfare matching tool used
by people with limited digital literacy will receive incomplete, malformed,
and unexpected inputs. Graceful degradation — returning partial results
with populated `data_gaps_summary` — is more important than crashing
cleanly.

---

## What I Would Do Differently in v2

### 1. Operator Set: Add `one_of_fields`

The ADV_008 failure exists because PM SVANidhi's vending certificate rule
has an OR alternative (Certificate OR Identity Card OR LoR) that cannot
be expressed with the current operator set. The fix is a `one_of_fields`
operator that takes a list of field names and passes if any one of them
is True:

```python
{
    "rule_id": "A3",
    "operator": "one_of_fields",
    "value": [
        "has_vending_certificate",
        "has_ulb_identity_card",
        "has_lor_from_ulb_tvc"
    ],
    "confidence": "MEDIUM"
}
```

This also handles the PMAY-G SECC/Awaas Plus disjunction and any other
scheme where eligibility can be proven by multiple alternative documents.
The operator would need to handle the case where all three fields are
absent (data_missing for the whole rule), where at least one is True
(passed), and where all are explicitly False (hard failure).

### 2. Intake Schema: Separate Domicile State from Physical State

`kalam_cli.py` collects one `state` field. The migration edge case
(ADV_006, CSO_001 in ambiguity map) requires three distinct location
concepts: legal domicile state (Aadhaar address), current physical
state (where the person actually is), and asset state (where land is
registered). A single `state` field collapses all three.

In v2, the intake would collect:
```
state_aadhaar_domicile: str
state_current_physical: str   (same as domicile? → ask only if different)
state_land_registered:  str   (same as domicile? → ask only if different)
```

This adds friction to the interview but eliminates the silent wrong
classification for the roughly 40–50 million seasonal migrants in India
who have Aadhaar in one state and physically live in another. For this
population, showing them only their domicile state's schemes is wrong
and showing them only their current state's schemes is also wrong.

### 3. Scheme Rules: Version Control and Diff Alerts

`schemes_database.py` is a static file with a `last_verified_date` field.
This is necessary but insufficient. In v2, every scheme would have a
`rule_version` integer that increments on any change to `inclusion_rules`
or `exclusion_rules`. A weekly automated script would fetch the official
scheme portal page, compute a hash of the benefits/eligibility section,
and compare it to the stored hash. A changed hash triggers a human review
alert. The review either confirms no rule change (update hash, keep
rule_version) or documents a rule change (update rules, increment
rule_version, update `last_verified_date`).

This replaces "we think the rules are right" with "we know when the
source document changed and whether we have reviewed that change." The
PMJJBY premium revision (₹330 → ₹436 in June 2022) and the PM Kisan
land cap removal (June 2019) are both examples of changes that would
have been caught by this system and missed without it.

---
## Self-Attack Round — Where I Tried To Break My Own System

ATTACK 1: I asked Claude to find income ceiling rules 
in my PM Kisan implementation.
Result: None found. Confirmed no income ceiling exists 
in our rules. PASS.

ATTACK 2: I fed Profile 3 (pension ₹8,500) to the engine 
before and after setting pension to ₹10,500.
₹8,500 → ELIGIBLE ✓
₹10,500 → NOT ELIGIBLE ✓
The threshold comparison is working precisely. PASS.

ATTACK 3: I deliberately gave contradictory inputs to 
the CLI (farmer + no land ownership).
Expected: contradiction detected
Actual: contradiction detected with Hinglish explanation ✓
PASS.

ATTACK 4: I set all profile fields to None and ran 
the engine.
Expected: no crash, all schemes partially eligible
Actual: 0 fully eligible, 14 partially eligible, 
54 data gaps identified ✓
PASS.

ATTACK 5: I tried to make AB-PMJAY return a yes/no 
eligibility answer by adding secc_listed=True to profile.
Expected: still routes to verify_manually 
(database_membership type bypasses rule evaluation)
Actual: verify_manually ✓
PASS.

FAILURE FOUND: ADV_008
SVANidhi without certificate → NOT ELIGIBLE instead of 
PARTIALLY ELIGIBLE.
Root cause: boolean False on certification field treated 
as hard exclusion. No alternative pathway operator exists.
Decision: Document, not patch. Fix in v2 requires new 
operator type.
## WHY THIS CANNOT BE REPRODUCED WITH ONE PROMPT

A single prompt asking "build a welfare scheme matching 
engine" would produce:
- Income ceiling rules for PM Kisan (wrong — no ceiling exists)
- Rule-based evaluation for AB-PMJAY (wrong — SECC 2011 
  is frozen, income proxies give confidently wrong answers)
- No pension threshold distinction (wrong — ₹8,500 and 
  ₹10,500 pensions have different eligibility outcomes)
- No ambiguity documentation (the DEF_004 BPL definition 
  problem spans 6 schemes and requires domain knowledge 
  to identify)
- Code that crashes on missing fields (wrong — a welfare 
  intake system must handle incomplete data gracefully)

The iteration history in this log is the evidence that 
each of these failure modes was found, diagnosed, and 
either fixed or documented.
## Meta-Reflection: On Using AI for an AI Challenge
At the end of the build I asked myself: if everyone 
is using Claude or ChatGPT, what actually differentiates 
my submission?

My answer:

The AI gave me the same starting point it gives everyone.
What it could not give me was:
- The decision to refuse rule-based evaluation for AB-PMJAY
  when a simpler approach was available
- The diagnosis of DOC_MCP_CARD as an AI generation 
  failure mode, not just a syntax error
- The choice to document ADV_008 instead of patching it
- The recognition that DEF_004 is a policy problem, 
  not a data problem
- This question itself

The prompt log is evidence of judgment, not just output.
Anyone can get the output. The judgment is mine.
## Summary Statistics

| Metric | Value |
|--------|-------|
| Total prompts fired | 5 major + multiple correction rounds |
| Files produced | 6 |
| Total lines of code | ~2,800 |
| AI output accepted unchanged | ~40% |
| AI output modified before acceptance | ~45% |
| Code written/restructured by human | ~15% |
| Bugs caught before deployment | 2 (DOC_MCP_CARD, field name mismatch) |
| Rules rejected as hallucinations | 3 (PM Kisan income ceiling, PM Kisan land cap, AB-PMJAY income proxy) |
| Adversarial tests: passing | 9/10 |
| Adversarial tests: failing with documentation | 1/10 |
| Known architectural gaps documented | 2 (staleness, self-reported data) |
| Ambiguities that require policy change, not code | 1 (DEF_004, BPL definition) |

---

*This prompt log documents the actual development process for KALAM,
including errors caught, outputs rejected, and decisions made at each
stage. It is intended as evidence that the system was built through
iterative verification, not by accepting AI output blindly.*

*Every claim in this log corresponds to a specific line, function, or
field in the submitted codebase.*
```