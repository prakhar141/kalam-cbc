# KALAM Ambiguity Report
## Contradictions, Overlaps, and Gaps in 15 Indian Welfare Schemes

**Document version:** 1.0  
**Schemes analyzed:** 15 central government schemes  
**Total ambiguities documented:** 29  
**Severity breakdown:** 13 HIGH · 11 MEDIUM · 5 LOW  
**Most ambiguous scheme:** PM Kisan Samman Nidhi (7 ambiguities)  
**Schemes with zero ambiguities:** None  

---

## Executive Summary

A systematic audit of the 15 central government welfare schemes in
KALAM's database found 29 distinct ambiguities — points where the
official scheme guidelines either contradict themselves, use terms
without operational definitions, overlap with other schemes in ways
that create false mutual exclusions, or reference data that changes
faster than any static system can track.

**13 of these 29 ambiguities are HIGH severity**, meaning they can
cause a matching engine to give the wrong eligibility answer with
full confidence. This is the most dangerous failure mode in welfare
technology: not a system that says "I don't know," but a system that
says "you qualify" or "you don't qualify" with authority, when the
underlying rule is genuinely uncertain.

The remaining ambiguities cause confidence reductions (MEDIUM) or
serve as informational flags for caseworkers (LOW). None are trivial.
Every ambiguity in this document represents a real person who could
be wrongly matched or wrongly excluded.

The single most consequential finding is documented separately in
Section 4: the BPL definition problem. The phrase "BPL household"
appears as an eligibility criterion in 6 of the 15 schemes in this
database. It refers to at least 4 operationally distinct lists that
do not agree with each other. No software fix resolves this. It
requires government data harmonization.

---

## Why This Document Exists

Indian welfare eligibility language is intentionally vague in many
places — not by accident, but because vagueness preserves administrative
discretion. A guideline that says "destitute household" rather than
"household with income below ₹X" gives the district welfare officer
the authority to make judgment calls in ambiguous cases, which is
sometimes appropriate given ground realities that no income threshold
can capture. The problem arises when a computer system must translate
that discretion into a binary yes/no: the system is forced to choose
an interpretation that the guideline deliberately left open, and that
choice — made invisibly, at scale — determines whether real families
receive benefits they are entitled to.

---

## Section 1 — HIGH SEVERITY Ambiguities

*These 13 ambiguities can cause a wrong eligibility decision.
Every KALAM output involving these schemes must carry an explicit
flag. They are presented in plain English, organized by scheme.*

---

### INT_001 · PM Kisan · The Group D Pension Carve-Out

**What the rule says:** Retired government employees with a monthly
pension of ₹10,000 or more are excluded from PM Kisan. However,
Multi-Tasking Staff (MTS) and Group D government employees are exempt
from this exclusion — even if they receive a pension above ₹10,000.

**Why it breaks a matching system:** The intake form asks whether the
user is a retired government employee and what their pension amount is.
It does not ask what grade or category they retired from. So when a
retired employee with a pension of ₹12,000 fills out the form, the
engine sees "retired govt employee, pension > ₹10,000" and correctly
triggers the exclusion — but cannot determine whether the carve-out
applies because it has no information about employment grade.

**Real-world impact:** A sweeper or peon who retired from a government
job and receives a small Group D pension could be wrongly excluded from
PM Kisan. Group D workers represent the lowest-paid tier of government
service — precisely the people the scheme is meant to reach.

**What KALAM does:** Flags this as an ambiguous rule and asks a
clarifying question: "Were you or your household member retired from
a Group D or Multi-Tasking Staff (MTS) government post?"

---

### INT_002 · PM Kisan · The Elected Representative Asymmetry

**What the rule says:** Former MPs, MLAs, and MLCs are excluded from
PM Kisan. Former Zila Panchayat Presidents and Mayors of Municipal
Corporations are NOT excluded — only current holders of these offices
are.

**Why it breaks a matching system:** This asymmetry — former
parliamentarians excluded, former local body heads not excluded — is
almost universally missed by automated systems and LLMs. A single
boolean field (`is_elected_representative`) cannot capture it. A system
that excludes all former elected representatives wrongly disqualifies
former Panchayat Presidents. A system that only excludes current
representatives wrongly includes former MPs.

**Real-world impact:** A retired Zila Panchayat President who now
farms his land is legitimately eligible for PM Kisan. A retired MP
who farms identical land is not. Same activity, same land size, same
economic situation — different eligibility based on which office they
previously held.

**What KALAM does:** Documents this as unresolved in the intake schema.
The field `is_or_was_elected_representative` collapses the distinction
and is flagged for schema redesign in v2.

---

### STALE_001 · PM Kisan · The 2019 Amendment

**What older sources say:** PM Kisan is for small and marginal farmers
with land holdings up to 2 hectares.

**What the current rule says:** The 2-hectare cap was removed in
June 2019 when the scheme was universalized to all landowning farmer
families regardless of land size.

**Why it breaks a matching system:** The pre-2019 rule is still cited
on many secondary websites, in older government publications, and in
LLM training data. A system that applies the 2-hectare cap would
wrongly exclude large farmers who are fully eligible under current rules.

**Real-world impact:** A farmer owning 5 hectares is eligible for PM
Kisan under the 2019 amendment. A system using the pre-amendment rule
would tell him he is not eligible — and he might believe it.

**What KALAM does:** The PM Kisan inclusion rules contain no land size
ceiling. The `common_hallucinations` field explicitly flags this:
"Only for small/marginal farmers under 2 hectares — WRONG. Cap removed
June 2019."

---

### STALE_005 · PMAY Urban · The 2.0 Transition

**What the current situation is:** PMAY Urban Phase 1 ended March 31,
2022. PMAY Urban 2.0 was announced in the Union Budget 2024 but
operational guidelines have not been released as of this document's
verification date.

**Why it breaks a matching system:** The scheme exists and will cover
new beneficiaries, but the eligibility criteria, income categories,
and benefit structure for PMAY-U 2.0 are not yet defined in official
guidelines. Any system showing users PMAY-U eligibility is drawing on
Phase 1 criteria that may not apply to the new scheme.

**Real-world impact:** A user told they are eligible for PMAY Urban
may go to a government office, find the scheme not currently accepting
applications, and conclude the matching system was wrong.

**What KALAM does:** Flags PMAY Urban as a scheme in active transition.
MIG-I and MIG-II income thresholds are marked LOW confidence. The
scheme carries an ambiguous rule flag: "Scheme in policy transition —
eligibility criteria may change on guideline release."

---

### CSO_001 · PMAY Gramin / PMAY Urban · Self-Reported Rural/Urban

**What the rule requires:** PMAY Gramin is for rural residents. PMAY
Urban is for urban residents. "Rural" and "urban" are defined by Census
classification of the area, not by the resident's self-perception.

**Why it breaks a matching system:** Residents of peri-urban areas —
the expanding grey zones around Indian cities — frequently do not know
whether their locality is Census-classified as urban or rural. A
resident of an unplanned settlement on the edge of a municipal boundary
may call themselves rural while living in a Census urban area, or call
themselves urban while living in a Census village. The matching engine
takes their answer at face value.

**Real-world impact:** A peri-urban resident who calls themselves rural
gets matched to PMAY-G and potentially applies — only to be rejected
because their locality is Urban Local Body jurisdiction. The opportunity
cost of that application failure falls entirely on them.

**What KALAM does:** Displays an explanation of the rural/urban
distinction at the point of asking and recommends checking with the
local Gram Panchayat or Ward Office if the user is uncertain.

---

### CSO_002 · PMAY Gramin · The Pan-India Pucca House Rule

**What the rule says:** An applicant must not own a pucca house anywhere
in India — not just in their current location.

**Why it breaks a matching system:** A user who has a kutcha house in
their village but has purchased a flat in a city, or whose spouse owns
a flat in another state, is excluded from PMAY-G. The intake question
asks whether the user has a pucca house anywhere in India. Self-report
on this question is unreliable — users may not consider a spouse's
property, an inherited property they rarely visit, or a property owned
jointly with siblings as "their" house.

**Real-world impact:** PMAY-G benefit wrongly allocated to a household
that technically owns urban property means a genuinely houseless family
loses that slot.

**What KALAM does:** Asks the question explicitly with the phrase
"anywhere in India — including your spouse's name, inherited property,
or a house in another city." Marks the response as self-reported and
applies MEDIUM confidence to the PMAY-G match when this field is
answered affirmatively (no house anywhere).

---

### DEF_001 · PM Kisan · Cultivable Land

**What the rule says:** PM Kisan is for "landholder farmer families."

**What it does not say:** What counts as agricultural or cultivable
land. Is fallow land that could be farmed counted? Is an orchard?
A fishpond on agricultural-zoned land? Land that was cultivated three
years ago but not currently?

**Why it breaks a matching system:** The engine asks whether the user's
land is cultivable and takes their yes/no at face value. A user with
fallow land will likely say yes. A user with an orchard may say yes or
no depending on their interpretation. The scheme guideline provides no
operational definition.

**Real-world impact:** Inconsistent inclusion and exclusion of
borderline land types depending on how the user interprets the question.

**What KALAM does:** Marks the `land_is_cultivable` rule as MEDIUM
confidence. The clarification note to users specifies: "Does crops
grow on it, or could they? Wasteland or rocky land that cannot be
farmed usually does not count."

---

### DEF_003 · PM SVANidhi · Who Is a Street Vendor

**What the rule says:** PM SVANidhi is for street vendors as defined
by the Street Vendors (Protection of Livelihood and Regulation of
Street Vending) Act, 2014.

**What the Act says:** A street vendor is "a person engaged in
vending of articles, goods, wares, food items or merchandise of
everyday use or offering services to the general public, in a street,
lane, side walk, footpath, pavement, public park or any other public
place or private area, from a temporary built up structure or by moving
from place to place."

**What this leaves unclear:**

- A woman who sells pickles from her home to neighbors — is she a
  street vendor?
- A seasonal vendor who sells only during festivals — does "vendor"
  require year-round activity?
- A person who sells from a vehicle parked on a street — does the
  vehicle count as a temporary structure?
- An agricultural laborer who also sells produce informally — are
  they primarily a vendor?

**Real-world impact:** The vending certificate route resolves this
for vendors who have been formally enumerated by their Urban Local
Body — the ULB made the classification decision. But the Letter of
Recommendation route for unenumerated vendors puts this determination
in the hands of a Town Vending Committee member, with no standardized
criteria.

**What KALAM does:** Marks the SVANidhi vending certificate rule as
MEDIUM confidence and flags the LoR alternative. See also the
documented ADV_008 failure in Section 5.

---

### DEF_004 · Six Schemes · The BPL Definition Problem

*This ambiguity is given its own full section (Section 4) because it
affects 6 schemes simultaneously and represents the largest single
structural problem in Indian welfare targeting. See Section 4.*

---

### OVL_003 · APY / PMJJBY · The Exact Age 40 Boundary

**What the rules say:** Atal Pension Yojana enrollment is open to
persons "between 18 and 40 years of age." PM Jeevan Jyoti Bima
Yojana enrollment is open to persons between 18 and 50 years.

**What "between 18 and 40" means:** This is a genuine ambiguity.
"Between" in ordinary English typically excludes the endpoints:
"between 3 and 5" means 4. "Between 18 and 40" would then mean
19 to 39, excluding both 18 and 40. But in government scheme
language, "between X and Y years" conventionally means X ≤ age ≤ Y
— inclusive of endpoints.

**Why this matters:** A person who is exactly 40 years old today.
Under the inclusive reading, they can still enroll in APY. Under the
exclusive reading, they cannot. This is not a hypothetical — hundreds
of thousands of people turn 40 on any given day in India.

**Real-world impact:** A 40-year-old who is wrongly told they cannot
enroll in APY misses the last opportunity to enter the scheme.
A 40-year-old who is wrongly told they can enroll, applies, and is
rejected by the implementing bank has lost time and been given false
information.

**What KALAM does:** The APY rule uses `"operator": "between"` with
`"value": [18, 40]`, implemented as `18 <= age <= 40` (inclusive).
This matches conventional government interpretation. The boundary
ambiguity is documented in the ambiguity map as OVL_003 with a note
that the inclusive interpretation is used.

---

### OVL_005 · AB-PMJAY · SECC 2011 Frozen Database

**What the rule requires:** Ayushman Bharat PM-JAY eligibility is
determined by the Socio-Economic Caste Census 2011. Families enumerated
as deprived in that census are eligible. Families not enumerated are not.

**The fundamental problem:** The SECC 2011 database was frozen on
completion of the census. It does not update. It does not add new
households. It does not remove households whose circumstances improved.

**Three populations this fails:**

*Population 1 — The newly poor:* A family that was middle-class in 2011
and is now destitute due to illness, death of breadwinner, or economic
shock. They are not in the SECC list. They cannot receive AB-PMJAY
through the central scheme. A rule-based system using income as a proxy
would tell them they qualify. The hospital would tell them they don't.

*Population 2 — The newly formed household:* A couple who married after
2011 and live in a new household. Neither the husband nor wife appears in
SECC as their own household unit — they may appear as members of their
parental households. The children born after 2011 appear in no database.

*Population 3 — The previously poor, now stable:* A family enumerated
as deprived in 2011 who now has stable income, a government job, or
owns significant assets. They remain in the SECC list and remain eligible
for AB-PMJAY. This is not a bug in their favor — it is a design
consequence of a frozen database.

**Why this breaks a matching system:** Any income-based or asset-based
proxy rule for AB-PMJAY will incorrectly classify all three populations.
The correct answer for AB-PMJAY eligibility cannot be computed from
user-reported attributes. It requires a database lookup.

**What KALAM does:** AB-PMJAY is classified as `database_membership`
eligibility type. The engine refuses to give a yes/no. Every user is
directed to the NHA's own "Am I Eligible" tool at pmjay.gov.in, which
performs the actual SECC lookup. This is documented as Decision 2 in
`architecture.md`.

---

### STALE_006 · PMJJBY · Premium Amount

**What secondary sources say:** PMJJBY annual premium is ₹330/year.

**What the current rule says:** Premium was revised to ₹436/year in
June 2022. The ₹330 figure is stale and still circulates widely.

**Why it breaks a matching system:** A user told the premium is ₹330
who then contacts their bank and is told ₹436 will be debited has
been given wrong information. A user who cannot afford ₹436 but was
told ₹330 may enroll and then have the auto-debit fail.

**What KALAM does:** The premium is stored as `"premium_amount_inr": 436`
with a note: "Premium revised to ₹436/year from June 2022. Was ₹330
earlier." The `common_hallucinations` field includes: "Premium is ₹330/year
— WRONG. Revised to ₹436/year from June 2022."

---

### STALE_007 · Atal Pension Yojana · Taxpayer Exclusion

**What older sources say:** APY is open to all Indian citizens between
18 and 40 years who are not covered by statutory social security schemes.

**What the current rule says:** Income taxpayers have been excluded from
APY since October 2022. This rule was added by a PFRDA circular. It is
absent from most published descriptions of the scheme, including many
government-published summaries that have not been updated.

**Why it breaks a matching system:** A user who files income tax, is
between 18 and 40, and has a savings bank account meets all the criteria
in the older scheme description. Under current rules, they do not qualify.

**Real-world impact:** A young professional who files income tax and
tries to open an APY account at their bank will be turned away. If a
matching system told them they qualify, that system was wrong.

**What KALAM does:** Rule B1 for APY checks `is_income_taxpayer == True`
as an exclusion criterion. The `critical_note` on this rule reads:
"Taxpayer exclusion added Oct 2022 — frequently absent from older
descriptions."

---

## Section 2 — MEDIUM Severity Ambiguities

*These 11 ambiguities cause confidence reductions in match outputs.
They do not necessarily produce wrong eligibility decisions, but they
introduce enough uncertainty that outputs cannot carry HIGH confidence.*

---

**MIG-I / MIG-II income thresholds (PMAY Urban):** The income ceiling
for Middle Income Groups is under revision with PMAY-U 2.0. The stored
figures (₹12L for MIG-I, ₹18L for MIG-II) reflect Phase 1 CLSS
criteria. CLSS has been discontinued. The new benefit structure may
use different thresholds or eliminate the MIG categories entirely.
KALAM marks these LOW confidence.

**PMMVY second-child benefit implementation:** PMMVY 2.0 (announced
November 2022) extended maternity benefits to second children if the
second child is a girl. State-level implementation of this amendment
is not uniform as of verification date — some states continue operating
under PMMVY 1.0 processes. KALAM marks the second-child rule MEDIUM
confidence.

**IGNOAPS government pensioner exclusion:** NSAP guidelines discourage
duplicate pension payments to government service pensioners, but the
exclusion is implemented differently across states. Some states
explicitly exclude all government pensioners regardless of amount.
Others allow IGNOAPS for pensioners below a threshold. The central
guideline is ambiguous, making state-level implementation the
determinative factor. KALAM marks this exclusion MEDIUM confidence.

**PM SVANidhi LoR implementation variance:** The Letter of
Recommendation route for street vendors without formal certificates
is accepted in principle but implemented inconsistently. Some ULBs
issue LoRs promptly; others have non-functional Town Vending
Committees. KALAM notes this implementation risk but cannot encode
it as an eligibility rule.

**PMAY-G Awaas Plus parallel list:** PMAY-G primary targeting is
through SECC 2011, but the Awaas Plus survey (2018) identified
additional eligible households not in SECC. The two lists operate
in parallel. A household in Awaas Plus but not SECC is eligible —
but this cannot be determined from intake data. KALAM marks the
SECC listing rule MEDIUM confidence and flags that Gram Panchayat
verification is required.

**PMMVY Poshan Tracker integration:** Benefits under PMMVY 2.0 are
being routed through the Poshan Tracker application. States with
incomplete integration continue using older processes. Application
pathways differ by state. KALAM notes this as an implementation
variance without encoding it as an eligibility rule.

**JSY LPS/HPS state classification:** The Low Performing States list
that determines both JSY benefit amounts and the BPL/SC-ST restriction
was established in 2005 guidelines. State reclassification may have
occurred since then. KALAM uses the 2005 classification with a MEDIUM
confidence flag.

**JSY minimum age:** JSY guidelines specify benefit for mothers aged
19 and above. This threshold is not uniformly enforced — some states
provide JSY to all pregnant women regardless of age. KALAM applies
the 19-year threshold with MEDIUM confidence.

**APY EPF member soft exclusion:** APY is designed for workers not
covered by statutory social security. EPF members are not explicitly
barred by law but are outside the scheme's intended target population.
Whether an EPF member applying for APY would be rejected by the
implementing bank is unclear. KALAM marks this MEDIUM confidence.

**PMUY qualifying category expansion:** PMUY 2.0 expanded beyond BPL
to include SC/ST households, PMAY-G beneficiaries, AAY beneficiaries,
forest dwellers, tea garden workers, and others via multiple
notifications. The complete category list spans several circulars.
KALAM's encoding covers the major categories with MEDIUM confidence.

**MGNREGA household day-sharing:** The 100-day guarantee is per
household. Multiple adults in one household share the entitlement.
State implementations handle day-allocation differently — some track
at household level, some at individual level, some allow carryover.
KALAM notes this in the benefit description without encoding state
variations.

---

## Section 3 — LOW Severity Ambiguities

*These 5 ambiguities are informational. They do not change eligibility
decisions but should be disclosed to users.*

---

**NFBS "primary breadwinner" definition:** The National Family Benefit
Scheme pays on the death of the primary breadwinner. "Primary
breadwinner" is not defined in NSAP guidelines. In households with
multiple earners, the determination is made by the district welfare
officer. KALAM asks the clarifying question: "Was the person who
passed away the main income earner of your household?"

**MGNREGA drought-extension days:** Some states have extended the
100-day guarantee to 150 or more days in drought-declared or
disaster-declared years. This varies by state and by year and cannot
be encoded statically. KALAM notes that 100 days is the guaranteed
minimum.

**Sukanya Samriddhi interest rate:** The SSY interest rate is revised
quarterly by the Ministry of Finance. Any hardcoded rate is stale
within 90 days. KALAM explicitly does not store the interest rate
and directs users to the official portal for current rates.

**MGNREGA annual wage rates:** State-specific MGNREGA wage rates are
notified annually by the Ministry of Rural Development. KALAM does
not store specific wage rates and describes the benefit as a range
(approximately ₹200–₹350/day) with a note to check the current
state notification.

**IGNOAPS state top-up amounts:** The central government contributes
₹200/month (age 60–79) or ₹500/month (age 80+) to IGNOAPS. States
are required to contribute at least an equal amount and many contribute
significantly more. Total pensions range from ₹400 to over ₹2,000
per month depending on state. KALAM presents only the central
contribution and notes that the actual pension will be higher
depending on the state.

---

## Section 4 — The BPL Definition Problem

*This section stands alone because DEF_004 is not a software problem.
It is a policy infrastructure problem, and documenting it as such is
more honest than documenting it as a data quality issue to be fixed.*

---

### The Problem in Plain Terms

Six schemes in KALAM's database use "BPL household" as an eligibility
criterion:

| Scheme | How BPL is Used |
|--------|-----------------|
| NSAP IGNOAPS | Inclusion criterion: must be "destitute/BPL listed" |
| NSAP NFBS | Inclusion criterion: "BPL household" per state list |
| PMAY Gramin | Primary targeting via SECC 2011 deprivation |
| PM Ujjwala Yojana | Qualifying category includes BPL households |
| Janani Suraksha Yojana | High Performing States: BPL women only eligible |
| Pradhan Mantri Awaas Yojana Urban | EWS/LIG income categories approximate BPL |

A user who says "I have a BPL card" believes they have answered the
question. They have not. The relevant question is: **which BPL list?**

### The Four BPL Lists

**List 1 — 2002 BPL Survey**  
Conducted by the Ministry of Rural Development. Used a 13-point
socioeconomic index. Now more than two decades old. Many states still
issue BPL cards based on this survey because it has never been
formally replaced at the central level. Families whose economic
situations have changed significantly since 2002 — in either direction
— remain on or off this list based on 2002 data.

**List 2 — SECC 2011 (Rural)**  
The Socio-Economic Caste Census 2011 used deprivation and exclusion
criteria to identify rural households for welfare targeting. This list
was used to generate the PMAY-G beneficiary database and the AB-PMJAY
beneficiary database. Being on the 2002 BPL list does not guarantee
inclusion in SECC 2011, because the two surveys used different
methodologies. A family on the 2002 BPL list may or may not be on the
SECC 2011 list.

**List 3 — State-issued BPL cards**  
States maintain their own BPL lists for state schemes and for
distribution of ration card categories. The criteria for inclusion vary
by state. The cut-off income levels vary by state. Some states use the
central BPL survey as a base; others have conducted independent surveys.
A yellow or pink ration card in Maharashtra does not carry the same
eligibility implications as an equivalent card in Rajasthan.

**List 4 — Antyodaya Anna Yojana (AAY) list**  
The very poorest households — intended to be the bottom of the BPL
population — are separately identified under AAY, a sub-category of
the National Food Security Act targeting. Possession of an Antyodaya
card signals inclusion in the deepest poverty tier but does not
automatically mean the household appears on SECC 2011 or a state BPL
list in the form required by any specific scheme.

### Why This Cannot Be Fixed in Software

The four BPL lists exist in different databases maintained by different
government bodies at different levels of government. They were created
at different times, using different methodologies, for different
purposes. They are not synchronized. There is no master identity
number that links a household's entry across all four lists.

A welfare matching engine can ask a user "do you have a BPL card?" and
record the answer. It cannot determine which list that card was issued
against, whether that list matches the eligibility criteria of the
specific scheme being evaluated, or whether the user's household appears
on a different list that would be more relevant.

**This is a data infrastructure problem, not a data quality problem.**
Data quality problems can be fixed with better data collection or
validation. Data infrastructure problems require institutional
harmonization — agreement between central and state governments on a
common poverty identification methodology, linked to a common identifier,
updated on a defined schedule. This has been discussed in Indian policy
circles for more than a decade. It has not been implemented.

### What This Means for Any Welfare Matching System

Any system that treats "BPL" as a binary field — has BPL card or
doesn't — is making an implicit assumption about which BPL list is
relevant. In most cases that assumption is invisible and undocumented.

KALAM makes the assumption explicit: when a user reports a BPL card,
the system records `has_bpl_card = True` and uses this to inform
matching for schemes where BPL status is a stated criterion. The
CONFIDENCE_AUDIT documents that BPL-dependent rules carry MEDIUM
confidence because the BPL list relevant to any specific scheme cannot
be verified from self-report. For AB-PMJAY specifically, which uses
SECC 2011 and not state BPL lists, the BPL card is irrelevant —
and KALAM handles AB-PMJAY as a database_membership scheme regardless.

The user-facing language in `kalam_cli.py` does not ask "are you BPL"
in isolation. It asks: "Do you have a BPL card? (Below Poverty Line
card — yeh ration card se alag hota hai.)" This prompts the user to
think about whether they have the specific document, not just whether
they consider themselves poor.

That is the best a software system can do within the current data
infrastructure. The rest requires policy.

---

## Section 5 — Cross-Scheme Overlaps

*Where two schemes interact in ways that create false mutual exclusions
or opportunities that a naive system misses.*

---

**PMMVY and JSY — Complementary, Not Competing**  
Both PMMVY and Janani Suraksha Yojana provide cash benefits related
to pregnancy and childbirth. A pregnant woman might assume she must
choose between them. She does not. PMMVY provides maternity benefit
(₹5,000) for the first child, payable in installments during pregnancy.
JSY provides a delivery incentive (₹700–₹1,400 depending on state and
rural/urban classification) upon institutional delivery. A woman
eligible for both should claim both. KALAM matches both independently
and does not flag one as excluding the other.

**PM Kisan and MGNREGA — Same Rural Household, Both Valid**  
A small farmer who owns land and does agricultural work can receive
PM Kisan (₹6,000/year for owning land) and register for MGNREGA job
cards (100 days of wage employment guarantee for the household). These
are not competing schemes. The combination is the intended safety net
for small rural households. A naive system that sees "farmer" and
matches only agricultural schemes would miss MGNREGA. KALAM evaluates
both independently.

**PMAY-G and PMAY-U — Residence Determines Which, Not Income**  
A user cannot receive both PMAY-G and PMAY-U. The determining factor
is rural vs urban classification of their residence — not income,
not housing condition, not caste. Both schemes exclude people who
have already received central housing assistance. KALAM matches the
correct PMAY variant based on `residence_type` and checks
`already_received_govt_housing_benefit` as an exclusion criterion
on both.

**PMJJBY and PMSBY — Complementary Insurance, Both Recommended**  
PM Jeevan Jyoti Bima Yojana covers death from any cause (₹2 lakh,
₹436/year premium). PM Suraksha Bima Yojana covers accidental death
and disability (₹2 lakh / ₹1 lakh, ₹20/year premium). They are
designed to be held simultaneously. KALAM matches both and presents
them together with a note that the combined premium (₹456/year) covers
both life and accidental risk.

---

## Section 6 — What This Means for KALAM

Each category of ambiguity is handled differently by the matching engine.

---

**Internal contradictions** (5 documented, including INT_001 and INT_002)
are handled by the `ambiguous_rules` structure in `schemes_database.py`.
When a rule cannot be evaluated because the intake data is insufficient
to distinguish between two possible interpretations, the engine outputs
a clarifying question rather than a confidence estimate. The scheme is
routed to `partially_eligible` with a specific question in the
`gap_analysis` field.

**Cross-scheme overlaps** (6 documented) are handled at the matching
aggregator level in `match_schemes()`. Schemes are evaluated
independently against the user profile. No scheme's result is allowed
to influence another scheme's result unless an explicit
`prerequisite_schemes` relationship exists. This prevents false mutual
exclusions while correctly capturing genuine dependencies (Jan Dhan
account must precede DBT schemes).

**Definitional ambiguities** (9 documented, including DEF_004) are
handled in two ways. Where the definition affects a single field,
the intake question is written to give the user the most relevant
interpretation and the rule carries MEDIUM confidence. Where the
definition is irresolvably vague — as with BPL lists — the ambiguity
is surfaced in the output and the rule carries MEDIUM confidence with
an explanatory note.

**Stale data risks** (8 documented, including STALE_001 and STALE_005)
are handled through the `last_verified_date` field on every scheme and
the `CONFIDENCE_AUDIT` dictionary. Rules known to change frequently
carry MEDIUM or LOW confidence. Rules that were accurate at the time
of writing but may have changed since verification date carry explicit
staleness warnings. The `common_hallucinations` field documents the
most common stale rules — the ones that were once correct and still
circulate.

---

### The Honest Limitation

KALAM is a rule-based system operating on self-reported data, evaluating
rules that were encoded from scheme documents at a specific point in
time. Every ambiguity in this report represents a place where the
output could be wrong despite the system operating correctly.

The appropriate response to these ambiguities is not to hide them in
aggregate confidence scores but to surface them explicitly — in the
output, in this document, and in the design of the intake conversation.
A caseworker or a user who understands where and why the system is
uncertain can make better decisions than one who receives a confident
answer they have no reason to question.

The 29 ambiguities documented here are not failures of this system.
They are honest documentation of the gap between how welfare eligibility
is written and how it can be evaluated by any automated system, now or
in the future, until the underlying policy language and data
infrastructure become more precise.

---

*KALAM Ambiguity Report — End*

*This document should be read alongside `ambiguity_map.py` (machine-readable
ambiguity records with severity ratings and resolution status),
`schemes_database.py` (CONFIDENCE_AUDIT section), and `architecture.md`
Section 6 (production-readiness gaps).*

