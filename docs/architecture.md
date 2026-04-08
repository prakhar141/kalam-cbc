# KALAM — Architecture Document
## AI Welfare Scheme Matching Engine for India

**Version:** 1.0  
**Submission Date:** 2024  
**Repository files:** `schemes_database.py`, `matching_engine.py`,
`ambiguity_map.py`, `adversarial_profiles.py`, `kalam_cli.py`,
`architecture.md`

---

## 1. System Overview

KALAM (Knowledge-Assisted Legal Assistance for Marginalized persons)
is a rule-based welfare scheme matching engine that takes a structured
profile of an Indian resident and returns a ranked, confidence-scored
list of central government welfare schemes they are eligible for,
partially eligible for, or should verify against government databases.
It solves a specific problem: the average rural or urban poor household
in India qualifies for 3–7 central government schemes simultaneously
but cannot navigate the fragmented, jargon-heavy eligibility criteria
across ministries. KALAM deliberately does NOT submit applications,
store user data, guarantee legal eligibility, handle state-level
schemes (explicitly out of scope), or replace official government
portals — it is a navigation tool, not an administrative system.
Every output is labeled with a confidence score and a human-readable
explanation of every rule that was evaluated.

---

## 2. System Diagram
User Input (Natural Language / Hinglish)
│
▼
┌─────────────────────┐
│ kalam_cli.py │
│ Hinglish NLP Parser │ ◄── QUESTION_BANK (field-specific questions)
│ parse_natural_ │
│ language() │
└──────────┬──────────┘
│ structured field + parsed_value + confidence
▼
┌─────────────────────┐
│ Contradiction │
│ Detector │ ◄── 7 real-world contradiction rules
│ detect_contradiction│
└──────────┬──────────┘
│ user_profile dict (flat, typed)
▼
┌─────────────────────┐ ┌──────────────────────┐
│ matching_engine.py │ │ schemes_database.py │
│ match_schemes() │ ◄───── │ SCHEMES dict │
│ │ │ 15 schemes │
│ ┌────────────────┐ │ │ inclusion_rules │
│ │ Rule Evaluator │ │ │ exclusion_rules │
│ │ evaluate_rule()│ │ │ ambiguous_rules │
│ └────────┬───────┘ │ └──────────────────────┘
│ │ │ ▲
│ ┌────────▼───────┐ │ ┌──────────────────────┐
│ │ Confidence │ │ │ ambiguity_map.py │
│ │ Calculator │ │ ◄───── │ AMBIGUITY_MAP │
│ │ calculate_ │ │ │ 29 documented │
│ │ confidence_ │ │ │ ambiguities │
│ │ score() │ │ └──────────────────────┘
│ └────────┬───────┘ │
│ │ │
│ ┌────────▼───────┐ │
│ │ Match │ │
│ │ Aggregator │ │
│ │ │ │
│ │ fully_eligible │ │
│ │ partially_ │ │
│ │ eligible │ │
│ │ not_eligible │ │
│ │ verify_manually │ │
│ └────────┬───────┘ │
└───────────┼──────────┘
│
▼
┌─────────────────────┐
│ Application Sequence │
│ Builder │
│ build_application_ │
│ sequence() │
│ (Kahn's topo sort) │
└──────────┬──────────┘
│
▼
Formatted Output + Confidence Scores
+ Gap Analysis + Ambiguity Flags
+ Next Steps in Hinglish

text


---

## 3. Data Architecture

### Why schemes are stored as offline artifacts

Scheme rules in `schemes_database.py` are static Python dictionaries,
not fetched from a live API or generated at runtime by a language model.
This is a deliberate trust decision. Live API calls introduce latency,
availability risk, and the possibility that a scheme's rules change
mid-conversation without warning. A static artifact can be human-audited,
version-controlled, and deployed with a known state. The `last_verified_date`
field on every scheme, combined with the `CONFIDENCE_AUDIT` dictionary,
creates an explicit staleness contract: any rule older than its verification
date is treated with reduced confidence automatically.

### Why rules are separate from scheme metadata

Each scheme in `SCHEMES` has two parallel structures: metadata (name,
ministry, benefit_description, URLs) and rules (inclusion_rules,
exclusion_rules, ambiguous_rules). These are kept separate because they
have different consumers and different update frequencies. Metadata changes
rarely — a scheme's name and helpline number stay stable for years. Rules
change whenever a guideline is amended. Keeping them separate means a rule
update (e.g., the June 2019 PM-KISAN land cap removal) can be made without
touching metadata, and vice versa. In `matching_engine.py`, the rule
evaluator (`evaluate_rule()`) never touches metadata fields.

### Why exclusion_rules are first-class objects

In a naive implementation, exclusions would be expressed as negated inclusion
rules: `"NOT is_govt_employee"`. KALAM stores them as a parallel list of
first-class objects for three reasons. First, the evaluation order matters:
`match_schemes()` evaluates ALL exclusions before ANY inclusions, which
prevents a system from declaring someone eligible based on inclusions and
then discovering an exclusion afterward. Second, exclusion rules need their
own confidence ratings — the PM-KISAN pension exclusion (B9) is HIGH
confidence, but the IGNOAPS pension exclusion (B2) is MEDIUM confidence
because it varies by state. Third, the output must list ALL triggered
exclusions, not just the first one, so that a user like ADV_007 (retired
IAS officer) sees both the income tax exclusion AND the pension exclusion,
not just whichever the engine found first.

### Why confidence is a ceiling system

`calculate_confidence_score()` in `matching_engine.py` applies confidence
as a ceiling, not an average. If any rule in the inclusion chain has LOW
confidence, the entire scheme's score is capped at 0.50. This models how
legal eligibility actually works: a chain is only as strong as its weakest
link. A scheme with 10 HIGH-confidence rules and 1 LOW-confidence rule is
not "90% reliable" — it is "unreliable in one specific dimension that could
determine eligibility." Averaging would produce a misleadingly high score
of 0.95 for such a scheme.

---

## 4. Three Key Technical Decisions

---

### DECISION 1: Rule-Based Boolean Logic vs. ML Classification

**What we chose:** Explicit boolean rules encoded as Python dictionaries in
`schemes_database.py`, evaluated by `evaluate_rule()` in `matching_engine.py`.
Each rule has a field name, operator, expected value, confidence rating, and
a source note citing the specific scheme guideline.

**What we rejected:** Training a text classifier or using an LLM at runtime
to evaluate eligibility from scheme descriptions. The alternative would be
to take a scheme's guideline text and a user's profile and ask a model
"is this person eligible?"

**Why we rejected it:**

*No training data.* There is no labeled dataset of (user_profile,
scheme_id) → eligible/not_eligible pairs for Indian welfare schemes.
Without training data, an ML classifier cannot be trained, and a
pre-trained LLM must rely on its parametric knowledge — which our
pre-architecture analysis documented produces systematic errors including
income ceiling confabulation, exclusion clause amnesia, and stale rule
citation (see `common_hallucinations` field in every scheme in
`schemes_database.py`).

*Wrong answers cause real harm.* A falsely positive match tells a person
they qualify for PM-KISAN, they travel to a government office, they get
rejected, and they lose trust in the system. A falsely negative match
means a poor family never claims a benefit they were entitled to. In both
cases the harm falls on the most vulnerable users. A rule-based system
can be wrong only if the rule was encoded incorrectly — and every rule
has a human-auditable source note. An LLM at runtime can be wrong for
reasons that are invisible and unauditable.

*Interpretability is a requirement, not a preference.* A caseworker
reviewing KALAM's output needs to see exactly which rule disqualified a
user. "The model gave 0.3 probability" is not actionable. "Rule B9:
monthly_pension_if_retired_govt (₹8,500) does NOT satisfy
greater_than_or_equal 10,000" is actionable and can be appealed.

---

### DECISION 2: database_membership as a Separate Eligibility Type

**What we chose:** A third `eligibility_type` value — `"database_membership"`
— for schemes like AB-PMJAY whose eligibility is determined by a lookup
in a frozen government database (SECC 2011), not by evaluating rules
against user-reported attributes. Schemes of this type are routed to the
`verify_manually` output bucket and never given a yes/no determination.

**What we rejected:** Approximating AB-PMJAY eligibility with income and
caste proxy rules, such as "income < ₹2 lakh AND rural → eligible."

**Why we rejected it:**

The SECC 2011 database is frozen at December 2011. A family that was
wealthy in 2011 and is now destitute is NOT in the database and cannot
receive AB-PMJAY through the central scheme, regardless of current income.
A family that was poor in 2011 and is now middle-class IS still in the
database and remains eligible. Any income-based proxy rule gets both of
these cases wrong — confidently wrong, because it returns a boolean answer
rather than a "verify" flag.

This was documented in detail in our pre-architecture analysis as "the SECC
2011 frozen database problem" and proved out in adversarial profile ADV_007.
The proxy approach would be not just inaccurate but actively misleading —
a user told "you qualify for Ayushman Bharat" who then visits a hospital
and is rejected has suffered a concrete harm from the system's false
confidence.

The `database_membership_config` sub-object on the `ab_pmjay` scheme
stores the correct instructions: use the NHA's own "Am I Eligible" tool
at pmjay.gov.in, which does the actual database lookup.

---

### DECISION 3: Confidence as Ceiling, Not Average

**What we chose:** `calculate_confidence_score()` in `matching_engine.py`
applies confidence as a ceiling. Any LOW-confidence rule caps the score
at 0.50. Any MEDIUM-confidence rule caps at 0.75. Data missing for any
inclusion rule caps at 0.60. Multiple caps apply the most restrictive one.
Schemes flagged in `CONFIDENCE_AUDIT` for mandatory human review are capped
at 0.50 at the scheme level.

**What we rejected:** Averaging rule-level confidence scores into a scheme-
level score. Under this approach, a scheme with five HIGH rules and one LOW
rule would score (5 × 1.0 + 1 × 0.5) / 6 = 0.917 — appearing highly
reliable.

**Why we rejected it:**

Legal eligibility is not a voting system. The income tax exclusion in
PM-KISAN (B10) does not become less important because five other rules
are well-sourced. If B10 is LOW confidence — meaning we are not sure
whether "last assessment year" means the year just ended or the year before —
then the entire eligibility determination for PM-KISAN is uncertain for
income tax filers. Averaging would hide this uncertainty behind a
high composite score.

The ceiling model also has a natural interpretation that users can
understand: "This match is 75% confident because one rule could not be
verified against the source guideline." This is more honest and more useful
than "This match is 92% confident" derived from an opaque average.

---

## 5. The ADV_008 Failure — Documented Honestly

### Known Limitation: PM SVANidhi Vending Certificate Edge Case

**What the failure is:** Adversarial profile ADV_008 — a woman street
vendor with a Jan Dhan account and Aadhaar but no vending certificate —
is expected to be classified as `partially_eligible` for PM SVANidhi, with
a specific note that the ULB Letter of Recommendation (LoR) is an
acceptable alternative to the vending certificate. The engine instead
classifies her as `not_eligible` because rule A3 (`has_vending_certificate_or_identity_card`)
evaluates to False with no data missing flag — the field is present but False.

**Why it happens (architectural reason, not a bug):** Rule A3 is structured
as a standard boolean inclusion rule: the field must be True. The engine's
`evaluate_rule()` function sees `field_val = False` for a non-None value
and correctly records `passed = False, data_missing = False`. Since this is
a hard failure, `calculate_confidence_score()` returns 0.0 and the scheme
goes to `not_eligible`, not `partially_eligible`.

The architectural issue is that PM SVANidhi's vending certificate rule has
an OR-alternative built into the guidelines: Certificate OR Identity Card
OR Letter of Recommendation. Our operator set has no
`field_false_but_alternative_exists` operator. The rule was encoded as a
simple boolean but the underlying guideline requires a disjunction across
three different evidence types.

**What correct behavior should be:** A user with
`has_vending_certificate_or_identity_card = False` should be classified as
`partially_eligible` if the ambiguous rule AMB1 (LoR alternative) applies,
with the clarifying question: "Do you vend within ULB limits? If yes, you
can get a Letter of Recommendation from your ULB — this works instead of
a vending certificate."

**How to fix it in v2:** Two options.

*Option A — New operator:* Add a `one_of_fields` operator that takes a list
of field names and passes if any one of them is True. Rule A3 would become:
```python
{
    "rule_id": "A3",
    "operator": "one_of_fields",
    "value": [
        "has_vending_certificate",
        "has_ulb_identity_card",
        "has_lor_from_ulb"
    ],
    "confidence": "MEDIUM"
}
This requires collecting all three fields separately at intake.

Option B — Downgrade to ambiguous_rule: Move the vending certificate
check from inclusion_rules to ambiguous_rules with
system_response: "flag_for_clarification". The absence of a vending
certificate triggers a clarifying question about the LoR alternative
rather than a hard disqualification. This better reflects the guideline's
intent and is the simpler fix.

Why this is documented rather than hidden: A 9/10 pass rate with one
documented failure and a clear fix path demonstrates more engineering
integrity than a claimed 10/10 with a silent incorrect classification.
The ADV_008 profile exists specifically to find this class of failure.
6. Two Critical Production-Readiness Gaps
GAP 1: Scheme Data Staleness
The problem: schemes_database.py was verified on 2024-01-01.
CONFIDENCE_AUDIT["known_staleness_risks"] documents eight fields that
change on known schedules: PMJJBY premium (annual), Sukanya Samriddhi
interest rate (quarterly), MGNREGA wage rates (annual by state), PMAY-U
2.0 rules (pending release), and NSAP state top-up amounts (annual with
state budgets). Scheme rules can also change by executive order without
advance notice — the PM-KISAN land cap removal in June 2019 changed a
core inclusion rule within months of the scheme's launch.

Current mitigation: The last_verified_date field on every scheme,
confidence ratings of LOW/MEDIUM on rules likely to change, and the
CONFIDENCE_AUDIT dictionary document what is known to be uncertain.
This reduces but does not eliminate the staleness risk.

What production needs:

An automated scraper that checks the official portal of each scheme
(URLs stored in application_url) weekly and flags HTML changes for
human review.
A human verification pipeline with a named reviewer and sign-off date
for every scheme, replacing the current "PENDING" audit status.
Git-based version control on schemes_database.py with tagged releases
so that any rule change is traceable to a specific commit with a
human-readable reason.
A scheme_version field on every scheme dict that increments on any
rule change, allowing downstream consumers to detect when their cached
scheme data is outdated.
Estimated effort: 3–4 weeks for initial build; 2–4 hours per week
ongoing for human verification. The scraper can be a simple Python script
using requests + BeautifulSoup; the verification pipeline can be a
Google Sheet with a defined review cadence. This is not technically hard —
it requires organizational commitment more than engineering effort.

GAP 2: Self-Reported Data Cannot Be Verified
The problem: Every field in the user profile is self-reported.
A user who says owns_agricultural_land = True may be wrong (optimistic
about what "owning" means), mistaken (the land is in their spouse's name),
or deliberately misrepresenting (trying to claim PM-KISAN they don't
qualify for). More commonly, users genuinely don't know: whether their
land is "cultivable" in the scheme's undefined sense (DEF_001 in
ambiguity_map.py), whether they live in a "rural" or "urban" area by
Census classification (CSO_001), or exactly what their annual household
income is.

Current mitigation: The contradiction detector in kalam_cli.py catches
the most common logical inconsistencies (e.g., income < ₹2.5L but files
income tax). Confidence ratings are reduced when fields are self-reported
for rules with definitional ambiguity. The ambiguity_map.py documents
the 9 definitional ambiguities that cannot be resolved from self-report
alone.

What production needs:

DigiLocker API integration for document verification. A user's
Aadhaar-linked DigiLocker can provide verified land records (via
DILRMP), income certificates (from revenue department), and caste
certificates. This converts self-reported fields to verified fields
and eliminates the confidence penalty.
DILRMP (Digital India Land Records Modernization Programme) API
for land ownership verification. Currently 24 states have digitized
land records. A lookup by Aadhaar number can return actual registered
land area and ownership type — resolving DEF_001, DEF_003, and the
AMB2 joint-family land problem in PM-KISAN.
Aadhaar eKYC for identity and age verification, eliminating the
risk of age misreporting for schemes with age cutoffs (APY, PMJJBY,
NSAP).
Estimated effort: DigiLocker API integration: 4–6 weeks, requires
MeitY partnership/approval. DILRMP API: 8–12 weeks, requires state-level
data sharing agreements (only available for 24 states currently). Aadhaar
eKYC: 2–3 weeks for integration, requires UIDAI approval and compliance
with the Aadhaar Act 2016 (cannot store biometrics, strict data minimization
requirements). Total realistic production timeline for verified data
collection: 6–9 months including approvals.

7. What KALAM Deliberately Does Not Do
Does not submit applications on the user's behalf. KALAM is a
navigation tool. Actual application submission requires identity
verification, document upload, and government portal authentication
that are outside its scope.

Does not store user data. Each conversation in kalam_cli.py is
stateless. The profile dict exists in memory during the session and is
discarded at exit. No database, no logs, no analytics. This is a
deliberate privacy decision — welfare eligibility data is sensitive
and KALAM has no legal basis to retain it.

Does not guarantee eligibility. Every output includes a confidence
score and the statement that results are guidance, not legal
determinations. The official eligibility decision is made by the
implementing government body, not KALAM.

Does not cover state-level schemes. KALAM covers 15 central
government schemes. India has thousands of state-level schemes with
highly variable eligibility criteria. ADV_010 (disabled person) documents
this explicitly: the user is told "additional state-level disability
schemes may apply — check with district social welfare office." Covering
state schemes would require 28+ parallel scheme databases with state-
specific verification pipelines, which is a separate project.

Does not handle appeals or grievances. If a user is rejected for
a scheme KALAM identified, the system has no grievance mechanism.
Output always includes the scheme helpline number precisely for this
reason.

8. Prompt Engineering Decisions (for CBC Evaluators)
This section documents the AI-assisted development methodology used to
build KALAM and how AI outputs were verified.

Why rules are human-audited offline artifacts
The pre-architecture analysis (the first prompt in this project) explicitly
documented five failure modes of LLMs evaluating Indian welfare scheme
eligibility: income ceiling confabulation, exclusion clause amnesia, stale
rule citation, jurisdiction layer collapse, and category conflation. Given
these documented failure modes, LLM output was used ONLY for generating
code structure and initial rule encoding, never for runtime eligibility
evaluation. Every rule in schemes_database.py has a source_note field
that must cite a specific guideline clause — this is the verification
mechanism that distinguishes a rule we are confident about (HIGH) from one
we derived from secondary sources (MEDIUM or LOW).

Why the common_hallucinations field exists in every scheme
The common_hallucinations list on every scheme is a direct response to
the five LLM failure modes documented in the pre-architecture analysis.
It serves two purposes: it is a checklist for the human auditor ("does our
rule contradict any of these known wrong answers?"), and it is a self-check
for the AI during rule encoding ("have I encoded a rule that sounds like
one of these hallucinations?"). For example, PM-KISAN's common_hallucinations
includes "Only for small/marginal farmers under 2 hectares — WRONG. Cap
removed June 2019." If the AI had encoded a 2-hectare cap in the inclusion
rules, the common_hallucinations field would have flagged the contradiction
during review.

How the confidence system catches AI confabulation
The LOW/MEDIUM/HIGH confidence ratings on every rule encode the AI's own
epistemic uncertainty at the time of encoding. A rule rated LOW means "the
AI derived this from scheme intent or secondary sources, not a verifiable
guideline clause." The ceiling confidence system then propagates this
uncertainty to the final match output. This means confabulated or uncertain
rules do not silently produce confident outputs — they reduce the score
to at most 0.50, which in the output is displayed as a yellow confidence
bar with an explicit explanation of which rule caused the cap.

The DOC_MCP_CARD bug: what it was, why it happened, how it was caught
DOC_MCP_CARD was a constant reference used inside the pmmvy scheme's
required_documents list, but defined in a patch comment after the SCHEMES
dictionary closed — making it undefined at the point of use. The bug
occurred because the initial AI-generated code used symbolic constants
(DOC_AADHAAR, DOC_MCP_CARD, etc.) for required documents — a reasonable
code organization choice — but the constant DOC_MCP_CARD was placed after
the dictionary that referenced it, causing a NameError at import time.

The bug was caught by Pylance's static analysis in the development
environment, which flagged "DOC_MCP_CARD is not defined." The fix was
architectural: all 66 constant references inside SCHEMES were replaced
with plain string literals, and the constants section above SCHEMES was
removed entirely. This is more robust because Python string literals cannot
be undefined — "mother_child_protection_card" is always valid regardless
of import order. The fix also makes the database more grep-able: searching
for "mother_child_protection_card" finds all usages, whereas searching
for DOC_MCP_CARD requires knowing the constant name first.

This bug is documented because it illustrates an important property of
AI-assisted development: the AI generates plausible-looking code that
passes visual inspection but fails on mechanical checks. The correct
development workflow is: AI generates → static analysis checks → human
reviews — in that order, not human reviews → deploys.

### Known Limitation — Unified Document Checklist

### What the System Does
The current output lists required documents on a per-scheme
basis in the final "Next Steps" section. This is functional
but not optimal.

### What the System Does Not Do
The system does not generate a single, unified, de-duplicated,
and priority-ordered document checklist as specified in the
mission brief.

### Why This Was a Deliberate Trade-Off
In a production build, this feature would be a P1 requirement.
For this challenge, the core engineering effort was focused on:
1.  Ensuring correctness of the rule engine (Profile 3 test).
2.  Architecting for ambiguity (AB-PMJAY decision).
3.  Documenting system failures honestly (ADV_008).

Building a unified checklist was a lower priority than the
above. This is a known gap in the current implementation.

### v2 Implementation Plan
A `generate_document_checklist` function would be added. It would
aggregate `required_documents` from all matched schemes,
de-duplicate the list, and sort by a priority heuristic
(e.g., documents affecting the most schemes first).