"""
KALAM — Welfare Scheme Matching Engine
Scheme Rules Database

CRITICAL USAGE NOTES:
=====================
1. This file is a STATIC ARTIFACT. It must be human-audited before
   use in production. Do not treat it as ground truth without verification.

2. Confidence levels:
   HIGH   = Rule is unambiguous in official guidelines, cross-verified
   MEDIUM = Rule derived from scheme description but specific clause
            not pinned to exact section number
   LOW    = Rule inferred from scheme intent, secondary sources, or
            areas where the author has known uncertainty

3. eligibility_type values:
   "rule_based"          = Boolean logic on user profile fields
   "database_membership" = Lookup in government database (e.g., SECC-2011)
   "hybrid"              = Both rule AND database checks required

4. Every LOW confidence field is documented in the CONFIDENCE_AUDIT
   dictionary at the bottom of this file. Read it before deploying.

5. This file does NOT replace official scheme guidelines.
   Source documents must be independently verified.

6. DESIGN DECISION — No constant variables inside SCHEMES dict:
   All required_documents and prerequisite_schemes values are plain
   strings. Constants defined above SCHEMES were a maintenance hazard —
   renaming a constant would silently break all references inside the
   dict without a NameError at the usage site. Plain strings are
   explicit, grep-able, and immune to import-order bugs.

Generated: 2024-01-01
Verified by human: [PENDING — DO NOT DEPLOY UNTIL THIS IS FILLED]
"""


# =============================================================================
# CONFIDENCE LEVEL CONSTANTS
# Only truly safe constants — simple strings with no internal references.
# =============================================================================
HIGH   = "HIGH"
MEDIUM = "MEDIUM"
LOW    = "LOW"


# =============================================================================
# MAIN SCHEMES DATABASE
# All values inside SCHEMES are plain literals — no variable references.
# =============================================================================

SCHEMES = {

    # =========================================================================
    # 1. PM KISAN SAMMAN NIDHI
    # =========================================================================
    "pm_kisan": {
        "scheme_id": "pm_kisan",
        "name": "PM Kisan Samman Nidhi",
        "ministry": "Ministry of Agriculture & Farmers Welfare",
        "benefit_description": (
            "₹6,000 per year in 3 equal installments of ₹2,000 each, "
            "transferred directly to bank account via DBT"
        ),
        "benefit_amount_inr": 6000,
        "benefit_frequency": "annual_in_3_installments",
        "eligibility_type": "rule_based",
        "guideline_version": "PM-KISAN Operational Guidelines, amended June 2019",
        "last_verified_date": "2024-01-01",
        "scheme_launched": "2019-02-01",

        "inclusion_rules": [
            {
                "rule_id": "A1",
                "field": "is_indian_citizen",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": (
                    "Section 2.1 of PM-KISAN Operational Guidelines. "
                    "Scheme is for Indian citizen farmers only."
                )
            },
            {
                "rule_id": "A2",
                "field": "owns_agricultural_land",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": (
                    "Section 2.1 — 'landholder farmer families'. "
                    "Land must be cultivable agricultural land. "
                    "Wasteland or non-agricultural land does not qualify."
                )
            },
            {
                "rule_id": "A3",
                "field": "land_ownership_type",
                "operator": "in",
                "value": ["individual", "joint"],
                "confidence": "HIGH",
                "source_note": (
                    "Section 2.3 — institutional landholders explicitly excluded. "
                    "Individual and joint family ownership both valid."
                )
            },
            {
                "rule_id": "A4",
                "field": "land_area_hectares",
                "operator": "greater_than",
                "value": 0,
                "confidence": "HIGH",
                "source_note": (
                    "Land area must be positive. No upper cap since June 2019 "
                    "universalization amendment. Pre-2019 cap of 2 hectares "
                    "is REMOVED and must not be applied."
                )
            },
            {
                "rule_id": "A5",
                "field": "land_is_cultivable",
                "operator": "equals",
                "value": True,
                "confidence": "MEDIUM",
                "source_note": (
                    "Implied by 'farmer family' definition. Wasteland ownership "
                    "without cultivation does not appear to qualify, but the "
                    "operational guidelines do not define 'cultivable' with "
                    "precise legal criteria. Flag for field verification."
                )
            },
        ],

        "exclusion_rules": [
            {
                "rule_id": "B1",
                "field": "is_current_constitutional_post_holder",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": (
                    "Section 2.3(i) — President, VP, Chief Justice, Speaker, etc. "
                    "Both current AND former holders excluded."
                )
            },
            {
                "rule_id": "B2",
                "field": "is_former_constitutional_post_holder",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": "Section 2.3(i) — former holders explicitly included in exclusion"
            },
            {
                "rule_id": "B3",
                "field": "is_current_minister",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": "Section 2.3(i) — current Union and State Ministers excluded"
            },
            {
                "rule_id": "B4",
                "field": "is_former_minister",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": (
                    "Section 2.3(i) — former Ministers explicitly excluded. "
                    "This is commonly missed by automated systems."
                )
            },
            {
                "rule_id": "B5",
                "field": "is_current_mp_or_mla_or_mlc",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": "Section 2.3(i)"
            },
            {
                "rule_id": "B6",
                "field": "is_former_mp_or_mla_or_mlc",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": (
                    "Section 2.3(i) — FORMER MPs/MLAs/MLCs are ALSO excluded. "
                    "CRITICAL: This is the single most commonly missed rule."
                ),
                "critical_note": "Former elected reps excluded — verify this is in your intake form"
            },
            {
                "rule_id": "B7",
                "field": "is_current_zila_panchayat_president_or_mayor",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": (
                    "Section 2.3(i) — current Mayors and District Panchayat Presidents excluded. "
                    "ASYMMETRY: Former holders of THESE offices are NOT excluded. "
                    "Different from B5/B6 for MPs/MLAs."
                ),
                "critical_note": (
                    "Only CURRENT local body presidents excluded, not former. "
                    "Opposite asymmetry from MPs/MLAs — do not conflate."
                )
            },
            {
                "rule_id": "B8",
                "field": "is_serving_central_or_state_govt_employee",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": (
                    "Section 2.3(ii) — serving employees of Central/State Govt, "
                    "PSUs, Autonomous Bodies. "
                    "Exception: Multi-tasking staff and Group D employees exempt — see AMB1."
                )
            },
            {
                "rule_id": "B9",
                "field": "monthly_pension_if_retired_govt",
                "operator": "greater_than_or_equal",
                "value": 10000,
                "confidence": "HIGH",
                "source_note": (
                    "Section 2.3(ii) — retired govt employees with monthly pension "
                    "≥ ₹10,000 excluded. "
                    "IMPORTANT: Pension BELOW ₹10,000/month does NOT trigger exclusion. "
                    "Exception: MTS/Group D retirees exempt — see AMB1."
                ),
                "critical_note": "Threshold is ₹10,000/month pension. Below threshold = NOT excluded."
            },
            {
                "rule_id": "B10",
                "field": "filed_income_tax_last_assessment_year",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": (
                    "Section 2.3(iii) — paid income tax in the last assessment year. "
                    "Note: 'last assessment year' not 'current year'."
                )
            },
            {
                "rule_id": "B11",
                "field": "is_registered_professional",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": (
                    "Section 2.3(iv) — professionals registered with professional bodies: "
                    "doctors (NMC), lawyers (Bar Council), CAs (ICAI), "
                    "engineers, architects."
                )
            },
        ],

        "ambiguous_rules": [
            {
                "rule_id": "AMB1",
                "description": (
                    "Multi-tasking staff (MTS) and Group D government employees "
                    "are exempt from the pension exclusion (B9) and possibly B8."
                ),
                "affects_rules": ["B8", "B9"],
                "why_ambiguous": (
                    "Employment grade (Group D vs others) is not captured "
                    "in standard intake forms. Cannot evaluate without this data."
                ),
                "system_response": "flag_for_clarification",
                "clarifying_question": (
                    "Were you or your household member retired from a "
                    "Group D / Multi-Tasking Staff (MTS) government post?"
                )
            },
            {
                "rule_id": "AMB2",
                "description": (
                    "Joint family land ownership: if land is registered to an "
                    "excluded person but farmed by a non-excluded family member."
                ),
                "affects_rules": ["A3", "B5", "B6"],
                "why_ambiguous": (
                    "Operational guidelines define the eligible unit as "
                    "'husband, wife, and minor children' but do not clearly "
                    "address joint family land registered to an excluded person."
                ),
                "system_response": "flag_for_human_review",
                "clarifying_question": (
                    "Is the agricultural land registered in your name specifically?"
                )
            },
        ],

        "prerequisite_schemes": ["pm_jan_dhan_yojana"],
        "prerequisite_note": (
            "DBT requires active bank account linked to Aadhaar."
        ),

        "required_documents": [
            "aadhaar_card",
            "land_records_khatoni_or_ror_or_patta",
            "bank_account_linked_to_aadhaar",
        ],

        "application_url": "https://pmkisan.gov.in",
        "helpline": "155261",

        "state_variations": {
            "has_variations": True,
            "states_with_variations": ["telangana", "odisha", "west_bengal"],
            "variation_note": (
                "Telangana has Rythu Bandhu, Odisha has KALIA scheme. "
                "State-level implementation status should be verified separately."
            )
        },

        "common_hallucinations": [
            "Income ceiling of ₹1.5 lakh per year — WRONG. No income ceiling exists.",
            "Only for small/marginal farmers under 2 hectares — WRONG. Cap removed June 2019.",
            "Landless agricultural laborers included — WRONG. Must own land.",
            "Only current MPs/MLAs excluded, not former — WRONG. Former also excluded.",
            "Any government employee excluded — PARTIALLY WRONG. Group D/MTS exempt.",
            "Scheme requires BPL card — WRONG. No BPL requirement.",
        ],
    },

    # =========================================================================
    # 2. MGNREGA
    # =========================================================================
    "mgnrega": {
        "scheme_id": "mgnrega",
        "name": "Mahatma Gandhi National Rural Employment Guarantee Act",
        "ministry": "Ministry of Rural Development",
        "benefit_description": (
            "Guaranteed 100 days of wage employment per financial year "
            "per rural household. Wage rates vary by state, notified annually."
        ),
        "benefit_amount_inr": None,
        "benefit_amount_note": (
            "Wage rate is state-specific, notified annually by MoRD. "
            "Ranges approximately ₹200–₹350/day depending on state. "
            "Maximum 100 days per household per financial year."
        ),
        "benefit_frequency": "per_day_worked_up_to_100_days_per_year",
        "eligibility_type": "rule_based",
        "guideline_version": "MGNREGA Act 2005, Schedule II; MoRD operational guidelines",
        "last_verified_date": "2024-01-01",
        "scheme_launched": "2005-09-02",

        "inclusion_rules": [
            {
                "rule_id": "A1",
                "field": "is_indian_citizen",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": "MGNREGA Act, Schedule II — adult members of rural household"
            },
            {
                "rule_id": "A2",
                "field": "residence_type",
                "operator": "equals",
                "value": "rural",
                "confidence": "HIGH",
                "source_note": (
                    "MGNREGA Act, Section 1(4) — applies to rural areas only. "
                    "Rural/urban classification per Census definitions."
                )
            },
            {
                "rule_id": "A3",
                "field": "age",
                "operator": "greater_than_or_equal",
                "value": 18,
                "confidence": "HIGH",
                "source_note": (
                    "MGNREGA Act, Schedule II — 'adult members', "
                    "defined as persons who have completed 18 years."
                )
            },
            {
                "rule_id": "A4",
                "field": "is_willing_to_do_unskilled_manual_work",
                "operator": "equals",
                "value": True,
                "confidence": "MEDIUM",
                "source_note": (
                    "MGNREGA Act, Schedule II — work provided is unskilled manual work. "
                    "Applicant must be willing. This is a self-declaration at registration."
                )
            },
        ],

        "exclusion_rules": [
            {
                "rule_id": "B1",
                "field": "residence_type",
                "operator": "equals",
                "value": "urban",
                "confidence": "HIGH",
                "source_note": "Urban residents not covered under MGNREGA."
            },
            {
                "rule_id": "B2",
                "field": "age",
                "operator": "less_than",
                "value": 18,
                "confidence": "HIGH",
                "source_note": "MGNREGA Act — only adult members (18+) eligible"
            },
        ],

        "ambiguous_rules": [
            {
                "rule_id": "AMB1",
                "description": (
                    "100 days per HOUSEHOLD, not per person. Multiple adults "
                    "in one household share the 100-day entitlement."
                ),
                "why_ambiguous": "Household definition for day-sharing varies by state implementation",
                "system_response": "include_in_benefit_description",
                "clarifying_question": None
            },
        ],

        "prerequisite_schemes": [],
        "prerequisite_note": (
            "Household must register at local Gram Panchayat for Job Card. "
            "Payment via bank or post office account."
        ),

        "required_documents": [
            "aadhaar_card",
            "government_photo_id",
            "residence_proof",
            "jan_dhan_or_active_bank_account",
        ],

        "application_url": "https://nrega.nic.in",
        "helpline": "1800-111-555",

        "state_variations": {
            "has_variations": True,
            "states_with_variations": ["all_states"],
            "variation_note": (
                "Wage rates are state-specific and notified annually. "
                "Some states extended beyond 100 days in specific years."
            )
        },

        "common_hallucinations": [
            "Only for BPL families — WRONG. No income or BPL criterion.",
            "Only for SC/ST workers — WRONG. Universal rural scheme.",
            "Wage rate is ₹X nationally — WRONG. State-specific, changes annually.",
            "Urban residents can apply — WRONG. Strictly rural only.",
            "Each person gets 100 days — WRONG. 100 days per household, shared.",
            "Requires land ownership — WRONG. Landless laborers are the primary beneficiaries.",
        ],
    },

    # =========================================================================
    # 3. AYUSHMAN BHARAT PM-JAY
    # =========================================================================
    "ab_pmjay": {
        "scheme_id": "ab_pmjay",
        "name": "Ayushman Bharat Pradhan Mantri Jan Arogya Yojana",
        "ministry": "Ministry of Health and Family Welfare / National Health Authority",
        "benefit_description": (
            "Health insurance cover of ₹5 lakh per family per year for "
            "secondary and tertiary hospitalization at empanelled hospitals. "
            "Cashless, paperless treatment."
        ),
        "benefit_amount_inr": 500000,
        "benefit_frequency": "annual_insurance_cover",
        "eligibility_type": "database_membership",

        "database_membership_config": {
            "primary_database": "SECC_2011",
            "database_description": (
                "Socio-Economic Caste Census 2011. Frozen dataset. "
                "Does not update. Families enumerated as deprived in 2011 "
                "are eligible regardless of current income."
            ),
            "lookup_method": "aadhaar_linked_or_ration_card_name_address",
            "verification_url": "https://pmjay.gov.in — 'Am I Eligible' tool",
            "database_frozen_date": "2011-12-31",
            "database_critical_warning": (
                "SECC 2011 is frozen. A family poor in 2023 but not in SECC 2011 "
                "is NOT eligible via the central scheme. A family that was poor "
                "in 2011 but is now affluent IS still listed. "
                "Rule-based income matching is WRONG for this scheme."
            ),
            "state_expansion_note": (
                "Many states have added beneficiaries beyond SECC 2011 "
                "via state-funded top-up schemes. State eligibility may use "
                "income criteria where central eligibility does not."
            )
        },

        "guideline_version": (
            "AB PM-JAY Operational Guidelines 2018; SECC 2011 deprivation criteria"
        ),
        "last_verified_date": "2024-01-01",
        "scheme_launched": "2018-09-23",

        "inclusion_rules": [
            {
                "rule_id": "A1",
                "field": "secc_listed",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": (
                    "Primary eligibility: listed in SECC 2011 as deprived household. "
                    "Cannot be determined from user intake alone. "
                    "Must be verified via NHA beneficiary database."
                )
            },
        ],

        "exclusion_rules": [
            {
                "rule_id": "B1",
                "field": "secc_listed",
                "operator": "equals",
                "value": False,
                "confidence": "HIGH",
                "source_note": (
                    "Not listed in SECC 2011 = not eligible for central AB-PMJAY. "
                    "May still be eligible under state expansion schemes."
                )
            },
        ],

        "ambiguous_rules": [
            {
                "rule_id": "AMB1",
                "description": (
                    "State-level expansion schemes use income/ration card criteria "
                    "and vary by state. Cannot encode without state-specific rules."
                ),
                "why_ambiguous": "50+ different state expansion schemes with different criteria",
                "system_response": "prompt_state_specific_lookup",
                "clarifying_question": (
                    "Your state may have expanded health coverage beyond central "
                    "Ayushman Bharat. Check your state's health scheme portal."
                )
            },
            {
                "rule_id": "AMB2",
                "description": (
                    "Families formed after 2011 may not appear in SECC even if "
                    "parents/original household is listed."
                ),
                "why_ambiguous": "No mechanism to inherit SECC status for new family units",
                "system_response": "flag_for_database_verification",
                "clarifying_question": (
                    "Was your household formed before or after 2011? "
                    "If after 2011, your parents' SECC listing may not cover you."
                )
            },
        ],

        "prerequisite_schemes": [],
        "prerequisite_note": (
            "No separate application for listed families. "
            "Eligibility verified at empanelled hospital using Aadhaar."
        ),

        "required_documents": [
            "aadhaar_card",
            "ration_card",
        ],

        "application_url": "https://pmjay.gov.in",
        "helpline": "14555",

        "state_variations": {
            "has_variations": True,
            "states_with_variations": [
                "gujarat", "rajasthan", "kerala", "maharashtra",
                "tamil_nadu", "andhra_pradesh", "telangana"
            ],
            "variation_note": (
                "Most states have adopted AB-PMJAY with state top-up, "
                "or have separate state health schemes."
            )
        },

        "common_hallucinations": [
            "Income below ₹X lakh makes you eligible — WRONG. No income criterion. SECC-based only.",
            "BPL card holders automatically eligible — WRONG. BPL list ≠ SECC 2011 list.",
            "Any family with income < ₹2 lakh qualifies — WRONG. SECC database, not income.",
            "Covers OPD and all medical expenses — WRONG. Hospitalization only.",
            "Cover is per person per year — WRONG. ₹5 lakh per FAMILY per year.",
            "Can be availed at any hospital — WRONG. Only empanelled hospitals.",
        ],
    },

    # =========================================================================
    # 4. PMAY GRAMIN
    # =========================================================================
    "pmay_gramin": {
        "scheme_id": "pmay_gramin",
        "name": "Pradhan Mantri Awaas Yojana — Gramin",
        "ministry": "Ministry of Rural Development",
        "benefit_description": (
            "Financial assistance for construction of pucca house. "
            "₹1.20 lakh in plain areas, ₹1.30 lakh in hilly/difficult areas. "
            "Additional ₹12,000 for toilet under SBM-G. "
            "90/95 person-days MGNREGA wages for unskilled labour."
        ),
        "benefit_amount_inr": 120000,
        "benefit_amount_hilly_areas_inr": 130000,
        "benefit_frequency": "one_time",
        "eligibility_type": "hybrid",

        "hybrid_config": {
            "description": (
                "PMAY-G uses SECC 2011 data to identify primary target population "
                "and Awaas+ survey 2018 for additional identification. "
                "Final eligibility combines both."
            ),
            "primary_source": "SECC_2011_housing_deprivation_criteria",
            "secondary_source": "Awaas_Plus_survey_2018"
        },

        "guideline_version": "PMAY-G Guidelines 2016, amended 2022; Awaas Plus guidelines 2018",
        "last_verified_date": "2024-01-01",
        "scheme_launched": "2016-11-20",

        "inclusion_rules": [
            {
                "rule_id": "A1",
                "field": "residence_type",
                "operator": "equals",
                "value": "rural",
                "confidence": "HIGH",
                "source_note": "PMAY-G is specifically for rural areas. Urban: see PMAY-U."
            },
            {
                "rule_id": "A2",
                "field": "housing_status",
                "operator": "in",
                "value": ["kutcha", "semi_pucca", "homeless"],
                "confidence": "HIGH",
                "source_note": (
                    "Target beneficiaries are houseless or living in kutcha/semi-pucca houses."
                )
            },
            {
                "rule_id": "A3",
                "field": "has_pucca_house_anywhere_in_india",
                "operator": "equals",
                "value": False,
                "confidence": "HIGH",
                "source_note": (
                    "PMAY-G guidelines: 'should not own a pucca house anywhere in India'."
                ),
                "critical_note": "Anywhere in India — not just current location"
            },
            {
                "rule_id": "A4",
                "field": "secc_listed",
                "operator": "equals",
                "value": True,
                "confidence": "MEDIUM",
                "source_note": (
                    "Primary beneficiary identification through SECC 2011. "
                    "Awaas Plus 2018 survey supplements SECC. "
                    "MEDIUM confidence: Awaas Plus creates a parallel list."
                )
            },
        ],

        "exclusion_rules": [
            {
                "rule_id": "B1",
                "field": "has_pucca_house_anywhere_in_india",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": "Explicitly excluded in PMAY-G operational guidelines"
            },
            {
                "rule_id": "B2",
                "field": "residence_type",
                "operator": "equals",
                "value": "urban",
                "confidence": "HIGH",
                "source_note": "Urban beneficiaries under PMAY-U, not PMAY-G"
            },
            {
                "rule_id": "B3",
                "field": "already_received_govt_housing_benefit",
                "operator": "equals",
                "value": True,
                "confidence": "MEDIUM",
                "source_note": (
                    "Prior IAY/PMAY beneficiaries who received assistance and "
                    "built a house are excluded. MEDIUM confidence — clause needs "
                    "field verification."
                )
            },
        ],

        "ambiguous_rules": [
            {
                "rule_id": "AMB1",
                "description": (
                    "Some eligible households appear in Awaas Plus but not SECC. "
                    "Cannot determine Awaas Plus listing from intake data alone."
                ),
                "why_ambiguous": "Awaas Plus is a separate 2018 field survey — no online lookup",
                "system_response": "flag_for_panchayat_verification",
                "clarifying_question": (
                    "Please contact your Gram Panchayat to verify if your household "
                    "is listed in the PMAY-G beneficiary list or Awaas Plus survey."
                )
            },
        ],

        "prerequisite_schemes": ["pm_jan_dhan_yojana"],
        "prerequisite_note": "Bank account required for installment-based fund transfer.",

        "required_documents": [
            "aadhaar_card",
            "jan_dhan_or_active_bank_account",
            "ration_card",
            "residence_proof",
            "self_declaration_form",
        ],

        "application_url": "https://pmayg.nic.in",
        "helpline": "1800-11-6446",

        "state_variations": {
            "has_variations": True,
            "states_with_variations": [
                "all_northeast_states", "himachal_pradesh",
                "uttarakhand", "jammu_and_kashmir"
            ],
            "variation_note": (
                "Higher unit cost (₹1.30 lakh) in hilly/difficult areas. "
                "Some states add state funds as top-up."
            )
        },

        "common_hallucinations": [
            "Available to all rural poor — WRONG. SECC/Awaas Plus list-based.",
            "BPL card is sufficient — WRONG. SECC listing required.",
            "Income limit of ₹X lakh — WRONG. No income criterion. Housing condition-based.",
            "Benefit is ₹2.5 lakh — WRONG. ₹1.20L plain, ₹1.30L hilly areas.",
            "Landless cannot apply — WRONG. Land ownership not required for PMAY-G.",
        ],
    },

    # =========================================================================
    # 5. PMAY URBAN
    # =========================================================================
    "pmay_urban": {
        "scheme_id": "pmay_urban",
        "name": "Pradhan Mantri Awaas Yojana — Urban",
        "ministry": "Ministry of Housing and Urban Affairs",
        "benefit_description": (
            "Housing assistance in 4 verticals: "
            "(1) BLC: Beneficiary-Led Construction — up to ₹1.5 lakh; "
            "(2) CLSS: Credit Linked Subsidy — DISCONTINUED as of March 2022; "
            "(3) AHP: Affordable Housing in Partnership — ₹1.5 lakh central assistance; "
            "(4) ISSR: In-Situ Slum Redevelopment. "
            "CLSS DISCONTINUED — do not present as active."
        ),
        "benefit_amount_inr": 150000,
        "benefit_amount_note": (
            "Amount varies by vertical. BLC/AHP: up to ₹1.5 lakh. "
            "CLSS was interest subsidy (discontinued March 2022)."
        ),
        "benefit_frequency": "one_time",
        "eligibility_type": "rule_based",
        "guideline_version": (
            "PMAY-U Guidelines 2015, amended 2022. "
            "CLSS discontinued March 31, 2022. "
            "PMAY-U 2.0 announced 2024 — rules under formulation."
        ),
        "last_verified_date": "2024-01-01",
        "scheme_launched": "2015-06-25",

        "income_categories": {
            "EWS": {
                "description": "Economically Weaker Section",
                "annual_income_ceiling_inr": 300000,
                "confidence": "MEDIUM",
                "source_note": "₹3 lakh ceiling for EWS. Subject to periodic revision."
            },
            "LIG": {
                "description": "Low Income Group",
                "annual_income_ceiling_inr": 600000,
                "confidence": "MEDIUM",
                "source_note": "₹3L–₹6L annual household income for LIG."
            },
            "MIG_I": {
                "description": "Middle Income Group I",
                "annual_income_ceiling_inr": 1200000,
                "confidence": "LOW",
                "source_note": (
                    "₹6L–₹12L for MIG-I. LOW confidence: CLSS discontinued, "
                    "PMAY-U 2.0 MIG structure under revision."
                )
            },
            "MIG_II": {
                "description": "Middle Income Group II",
                "annual_income_ceiling_inr": 1800000,
                "confidence": "LOW",
                "source_note": (
                    "₹12L–₹18L for MIG-II. CLSS discontinued. "
                    "LOW confidence — verify PMAY-U 2.0."
                )
            },
        },

        "inclusion_rules": [
            {
                "rule_id": "A1",
                "field": "residence_type",
                "operator": "equals",
                "value": "urban",
                "confidence": "HIGH",
                "source_note": "PMAY-U for urban areas only. Rural: see PMAY-G."
            },
            {
                "rule_id": "A2",
                "field": "has_pucca_house_anywhere_in_india",
                "operator": "equals",
                "value": False,
                "confidence": "HIGH",
                "source_note": (
                    "Beneficiary household should not own a pucca house anywhere in India."
                ),
                "critical_note": "Anywhere in India — not just the urban area"
            },
            {
                "rule_id": "A3",
                "field": "annual_household_income_inr",
                "operator": "less_than_or_equal",
                "value": 1800000,
                "confidence": "MEDIUM",
                "source_note": (
                    "Maximum income for any PMAY-U vertical is ₹18 lakh. "
                    "MEDIUM confidence — MIG categories under revision with PMAY-U 2.0."
                )
            },
        ],

        "exclusion_rules": [
            {
                "rule_id": "B1",
                "field": "has_pucca_house_anywhere_in_india",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": "Owns pucca house anywhere in India — explicitly excluded"
            },
            {
                "rule_id": "B2",
                "field": "previously_received_central_housing_subsidy",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": (
                    "Prior PMAY-U, PMAY-G, IAY beneficiaries cannot receive benefit twice."
                )
            },
            {
                "rule_id": "B3",
                "field": "residence_type",
                "operator": "equals",
                "value": "rural",
                "confidence": "HIGH",
                "source_note": "Rural residents must apply under PMAY-G"
            },
        ],

        "ambiguous_rules": [
            {
                "rule_id": "AMB1",
                "description": (
                    "PMAY-U 2.0 announced in Union Budget 2024. "
                    "New rules under formulation. Current scheme period ended March 2022."
                ),
                "why_ambiguous": "Active policy transition — rules not finalized",
                "system_response": "flag_scheme_as_in_transition",
                "clarifying_question": None
            },
        ],

        "prerequisite_schemes": ["pm_jan_dhan_yojana"],

        "required_documents": [
            "aadhaar_card",
            "income_certificate_from_tahsildar",
            "residence_proof",
            "bank_account_linked_to_aadhaar",
            "self_declaration_form",
        ],

        "application_url": "https://pmaymis.gov.in",
        "helpline": "1800-11-3377",

        "state_variations": {
            "has_variations": True,
            "states_with_variations": ["all_states"],
            "variation_note": (
                "State governments add funds and may have different income criteria. "
                "Urban Local Bodies are implementing agencies."
            )
        },

        "common_hallucinations": [
            "CLSS interest subsidy is available — WRONG. Discontinued March 2022.",
            "Income limit is ₹6 lakh for all — WRONG. Multiple income categories exist.",
            "Only for slum dwellers — WRONG. Multiple verticals including BLC.",
            "Available in rural areas — WRONG. Urban only.",
            "One-time payment of ₹2.67 lakh — WRONG. Amount varies by vertical.",
        ],
    },

    # =========================================================================
    # 6. PM UJJWALA YOJANA
    # =========================================================================
    "pmuy": {
        "scheme_id": "pmuy",
        "name": "Pradhan Mantri Ujjwala Yojana",
        "ministry": "Ministry of Petroleum and Natural Gas",
        "benefit_description": (
            "Free LPG connection (security deposit waiver, regulator, and one refill) "
            "to adult women from BPL/qualifying households. "
            "PMUY 2.0 (2021) expanded to migrants and additional categories."
        ),
        "benefit_amount_inr": None,
        "benefit_amount_note": (
            "Free connection (value approx ₹1,600–2,000). "
            "Subsequent refills at market price."
        ),
        "benefit_frequency": "one_time_connection",
        "eligibility_type": "rule_based",
        "guideline_version": "PMUY 1.0 May 2016; PMUY 2.0 August 2021",
        "last_verified_date": "2024-01-01",
        "scheme_launched": "2016-05-01",

        "inclusion_rules": [
            {
                "rule_id": "A1",
                "field": "gender",
                "operator": "equals",
                "value": "female",
                "confidence": "HIGH",
                "source_note": (
                    "Connection must be in the name of an adult woman of the household."
                )
            },
            {
                "rule_id": "A2",
                "field": "age",
                "operator": "greater_than_or_equal",
                "value": 18,
                "confidence": "HIGH",
                "source_note": "Adult woman — 18 years or above"
            },
            {
                "rule_id": "A3",
                "field": "is_bpl_listed_or_qualifying_category",
                "operator": "equals",
                "value": True,
                "confidence": "MEDIUM",
                "source_note": (
                    "PMUY 2.0 expanded eligibility to: SC/ST households, "
                    "PMAY-G beneficiaries, AAY beneficiaries, tea garden families, "
                    "forest dwellers, SECC-listed households. "
                    "MEDIUM confidence: full category list spans multiple notifications."
                )
            },
        ],

        "exclusion_rules": [
            {
                "rule_id": "B1",
                "field": "household_already_has_lpg_connection",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": (
                    "Households with existing LPG connection are not eligible. "
                    "Verified via LPG distributor database during application."
                )
            },
            {
                "rule_id": "B2",
                "field": "gender",
                "operator": "equals",
                "value": "male",
                "confidence": "HIGH",
                "source_note": "Connection cannot be issued in a male name under PMUY"
            },
        ],

        "ambiguous_rules": [
            {
                "rule_id": "AMB1",
                "description": (
                    "PMUY 2.0 allows migrants to apply with self-declaration of residence. "
                    "Exact format varies by oil marketing company (IOC, BPCL, HPCL)."
                ),
                "why_ambiguous": "OMC-level implementation differences",
                "system_response": "note_in_output",
                "clarifying_question": None
            },
        ],

        "prerequisite_schemes": ["pm_jan_dhan_yojana"],
        "prerequisite_note": (
            "Bank account required for subsidy transfer via DBTL. "
            "Aadhaar must be linked to bank account."
        ),

        "required_documents": [
            "aadhaar_card",
            "bank_account_linked_to_aadhaar",
            "ration_card",
            "bpl_card_or_certificate",
        ],

        "application_url": "https://www.pmuy.gov.in",
        "helpline": "1906",

        "state_variations": {
            "has_variations": True,
            "states_with_variations": ["all_states"],
            "variation_note": (
                "Some states provide additional refill subsidies. "
                "Assam/WB have special provisions for tea garden workers."
            )
        },

        "common_hallucinations": [
            "Available to any poor woman — WRONG. Must be from qualifying categories.",
            "Male household members can apply — WRONG. Must be in woman's name.",
            "Provides free cooking gas indefinitely — WRONG. Only first connection free.",
            "Income limit is ₹X — WRONG. Category-based, not direct income test.",
            "Requires BPL card only — PARTIALLY WRONG. PMUY 2.0 expanded beyond BPL.",
        ],
    },

    # =========================================================================
    # 7. PM MATRU VANDANA YOJANA
    # =========================================================================
    "pmmvy": {
        "scheme_id": "pmmvy",
        "name": "Pradhan Mantri Matru Vandana Yojana",
        "ministry": "Ministry of Women and Child Development",
        "benefit_description": (
            "Maternity benefit of ₹5,000 for first living child. "
            "₹6,000 for second child if girl (under PMMVY 2.0, from Nov 2022). "
            "Transferred directly to beneficiary's bank account."
        ),
        "benefit_amount_inr": 5000,
        "benefit_amount_note": (
            "PMMVY 1.0: ₹5,000 for first child in 3 installments. "
            "PMMVY 2.0 (Nov 2022): ₹5,000 first child; ₹6,000 second child if girl. "
            "Second son does NOT get the ₹6,000 benefit."
        ),
        "benefit_frequency": "one_time_per_eligible_child",
        "eligibility_type": "rule_based",
        "guideline_version": "PMMVY Guidelines 2017; PMMVY 2.0 November 2022",
        "last_verified_date": "2024-01-01",
        "scheme_launched": "2017-01-01",

        "inclusion_rules": [
            {
                "rule_id": "A1",
                "field": "gender",
                "operator": "equals",
                "value": "female",
                "confidence": "HIGH",
                "source_note": "Scheme is for pregnant and lactating mothers — women only"
            },
            {
                "rule_id": "A2",
                "field": "is_pregnant_or_recently_delivered",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": (
                    "Applies to pregnant women and recently delivered mothers. "
                    "Registration must happen during pregnancy for installment payment."
                )
            },
            {
                "rule_id": "A3",
                "field": "is_first_or_qualifying_child",
                "operator": "equals",
                "value": True,
                "confidence": "MEDIUM",
                "source_note": (
                    "PMMVY 1.0: First living child only. "
                    "PMMVY 2.0: First child OR second child if girl. "
                    "MEDIUM confidence: PMMVY 2.0 state implementation not uniform."
                )
            },
            {
                "rule_id": "A4",
                "field": "is_registered_at_anganwadi_or_health_facility",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": (
                    "Registration with Anganwadi Centre or approved health facility required."
                )
            },
        ],

        "exclusion_rules": [
            {
                "rule_id": "B1",
                "field": "is_govt_employee_already_receiving_maternity_benefit",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": (
                    "Women receiving maternity benefits under any other law "
                    "(e.g., Maternity Benefit Act for formal sector) not eligible."
                )
            },
            {
                "rule_id": "B2",
                "field": "child_number",
                "operator": "greater_than",
                "value": 2,
                "confidence": "MEDIUM",
                "source_note": (
                    "Third or subsequent children do not qualify. "
                    "MEDIUM confidence on exact PMMVY 2.0 cutoff."
                )
            },
        ],

        "ambiguous_rules": [
            {
                "rule_id": "AMB1",
                "description": (
                    "PMMVY 2.0 integration with Poshan Tracker: "
                    "Benefits now routed through Poshan Tracker. "
                    "States not yet integrated may use old process."
                ),
                "why_ambiguous": "State-level system integration status varies",
                "system_response": "note_in_output",
                "clarifying_question": (
                    "Contact your local Anganwadi Centre for the "
                    "current application process in your state."
                )
            },
        ],

        "prerequisite_schemes": ["pm_jan_dhan_yojana"],
        "prerequisite_note": (
            "Bank account in the woman's own name required for direct transfer."
        ),

        "required_documents": [
            "aadhaar_card",
            "bank_account_linked_to_aadhaar",
            "pregnancy_registration_certificate_from_anganwadi_or_phc",
            "mother_child_protection_card",
        ],

        "application_url": "https://pmmvy.wcd.gov.in",
        "helpline": "7998799804",

        "state_variations": {
            "has_variations": True,
            "states_with_variations": ["all_states"],
            "variation_note": (
                "Some states (Odisha, Tamil Nadu) have additional maternity schemes. "
                "PMMVY applies centrally but delivery is state-managed."
            )
        },

        "common_hallucinations": [
            "Available for all pregnancies — WRONG. First child and second girl only.",
            "₹11,000 total benefit — WRONG. ₹5,000 first child or ₹6,000 second girl.",
            "Applies to all women — WRONG. Not for those covered by Maternity Benefit Act.",
            "No registration required — WRONG. Anganwadi registration mandatory.",
            "Cash in hand — WRONG. Direct bank transfer only.",
        ],
    },

    # =========================================================================
    # 8. SUKANYA SAMRIDDHI YOJANA
    # =========================================================================
    "sukanya_samriddhi": {
        "scheme_id": "sukanya_samriddhi",
        "name": "Sukanya Samriddhi Yojana",
        "ministry": "Ministry of Finance / Department of Posts",
        "benefit_description": (
            "Small savings scheme for girl child. "
            "High interest rate (revised quarterly, ~8.2% p.a. as of Jan 2024). "
            "Tax-exempt (EEE status). Account matures when girl turns 21. "
            "Partial withdrawal at 18 for education or marriage."
        ),
        "benefit_amount_inr": None,
        "benefit_amount_note": (
            "Not a fixed benefit — savings scheme with compound interest. "
            "Minimum ₹250/year, maximum ₹1.5 lakh/year. "
            "Interest rate revised quarterly — do not hardcode."
        ),
        "benefit_frequency": "savings_scheme_with_interest",
        "eligibility_type": "rule_based",
        "guideline_version": "Sukanya Samriddhi Account Rules 2016, amended 2019",
        "last_verified_date": "2024-01-01",
        "scheme_launched": "2015-01-22",

        "inclusion_rules": [
            {
                "rule_id": "A1",
                "field": "has_girl_child_under_10",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": (
                    "Account can be opened for girl child up to age 10 years."
                )
            },
            {
                "rule_id": "A2",
                "field": "is_parent_or_legal_guardian",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": "Account opened by parent or legal guardian of the girl child."
            },
            {
                "rule_id": "A3",
                "field": "is_indian_citizen",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": (
                    "Girl child must be Indian citizen. "
                    "NRI accounts earn post-office savings rate, not SSY rate."
                )
            },
        ],

        "exclusion_rules": [
            {
                "rule_id": "B1",
                "field": "girl_child_age",
                "operator": "greater_than",
                "value": 10,
                "confidence": "HIGH",
                "source_note": "Cannot open SSY account for girl above 10 years."
            },
            {
                "rule_id": "B2",
                "field": "num_ssa_accounts_already_open",
                "operator": "greater_than_or_equal",
                "value": 2,
                "confidence": "HIGH",
                "source_note": (
                    "Maximum 2 SSY accounts per family (one per girl child). "
                    "Exception: twins/triplets may allow 3."
                )
            },
        ],

        "ambiguous_rules": [
            {
                "rule_id": "AMB1",
                "description": (
                    "Interest rate is revised quarterly and must not be hardcoded."
                ),
                "why_ambiguous": "Rate changes every quarter",
                "system_response": "direct_to_official_source_for_rate",
                "clarifying_question": None
            },
        ],

        "prerequisite_schemes": [],
        "prerequisite_note": (
            "Account opened at post offices or authorized bank branches. "
            "No prerequisite schemes. No BPL or income criteria."
        ),

        "required_documents": [
            "birth_certificate_of_girl_child",
            "aadhaar_card",
            "government_photo_id",
            "residence_proof",
        ],

        "application_url": "https://www.indiapost.gov.in",
        "helpline": "1800-11-2011",

        "state_variations": {
            "has_variations": False,
            "states_with_variations": [],
            "variation_note": "Central scheme, uniform rules nationally."
        },

        "common_hallucinations": [
            "Only for BPL families — WRONG. Universal scheme, no income criterion.",
            "Interest rate is fixed — WRONG. Revised quarterly.",
            "Account matures at 18 — WRONG. Matures at 21. Partial withdrawal at 18.",
            "For girls up to age 14 — WRONG. Up to age 10 only.",
            "One account per household — WRONG. One per girl, max 2 per family.",
        ],
    },

    # =========================================================================
    # 9. NSAP OLD AGE PENSION (IGNOAPS)
    # =========================================================================
    "nsap_ignoaps": {
        "scheme_id": "nsap_ignoaps",
        "name": "Indira Gandhi National Old Age Pension Scheme (IGNOAPS) under NSAP",
        "ministry": "Ministry of Rural Development",
        "benefit_description": (
            "Monthly pension for destitute elderly. "
            "Central contribution: ₹200/month (age 60–79); ₹500/month (age 80+). "
            "States add top-up — total pension varies (₹400–₹2,000+/month by state)."
        ),
        "benefit_amount_inr": 200,
        "benefit_amount_note": (
            "CENTRAL share only: ₹200/month (60–79), ₹500/month (80+). "
            "Total with state top-up varies widely. "
            "Do not present central amount as total."
        ),
        "benefit_frequency": "monthly",
        "eligibility_type": "rule_based",
        "guideline_version": "NSAP Guidelines 2014; state-specific notifications",
        "last_verified_date": "2024-01-01",
        "scheme_launched": "1995-08-15",

        "inclusion_rules": [
            {
                "rule_id": "A1",
                "field": "age",
                "operator": "greater_than_or_equal",
                "value": 60,
                "confidence": "HIGH",
                "source_note": "Minimum age 60 years. Age 80+ qualifies for higher rate."
            },
            {
                "rule_id": "A2",
                "field": "is_bpl_listed_or_destitute",
                "operator": "equals",
                "value": True,
                "confidence": "MEDIUM",
                "source_note": (
                    "NSAP guidelines: 'destitute' defined as little or no regular means "
                    "of subsistence. Operationally implemented through BPL list inclusion. "
                    "MEDIUM confidence: definition varies by state."
                )
            },
            {
                "rule_id": "A3",
                "field": "is_indian_citizen",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": "NSAP applies to Indian citizens"
            },
        ],

        "exclusion_rules": [
            {
                "rule_id": "B1",
                "field": "age",
                "operator": "less_than",
                "value": 60,
                "confidence": "HIGH",
                "source_note": "Below 60 not eligible for IGNOAPS"
            },
            {
                "rule_id": "B2",
                "field": "is_receiving_other_govt_pension",
                "operator": "equals",
                "value": True,
                "confidence": "MEDIUM",
                "source_note": (
                    "MEDIUM confidence — exclusion of govt service pensioners "
                    "implemented differently across states. Verify at state level."
                )
            },
        ],

        "ambiguous_rules": [
            {
                "rule_id": "AMB1",
                "description": (
                    "State top-up amounts vary from ₹0 to ₹2,500+/month. "
                    "Cannot encode statically — changes with state budgets."
                ),
                "why_ambiguous": "28+ state budget decisions, changes annually",
                "system_response": "present_central_amount_only_with_state_note",
                "clarifying_question": None
            },
        ],

        "prerequisite_schemes": ["pm_jan_dhan_yojana"],

        "required_documents": [
            "aadhaar_card",
            "age_proof_birth_certificate_or_school_leaving",
            "bpl_card_or_certificate",
            "bank_account_linked_to_aadhaar",
            "residence_proof",
        ],

        "application_url": "https://nsap.nic.in",
        "helpline": "1800-11-1363",

        "state_variations": {
            "has_variations": True,
            "states_with_variations": ["all_states"],
            "variation_note": (
                "State top-up mandatory (minimum equal to central share) "
                "but many states give more. Application process varies by state."
            )
        },

        "common_hallucinations": [
            "Pension is ₹200/month total — WRONG. ₹200 is CENTRAL share only.",
            "No BPL requirement — WRONG. Must be destitute/BPL listed.",
            "Available from age 55 — WRONG. Minimum age is 60.",
            "Same amount in all states — WRONG. State top-up varies widely.",
            "Automatically given to all elderly — WRONG. Application required.",
        ],
    },

    # =========================================================================
    # 10. ATAL PENSION YOJANA
    # =========================================================================
    "atal_pension_yojana": {
        "scheme_id": "atal_pension_yojana",
        "name": "Atal Pension Yojana",
        "ministry": "Ministry of Finance / PFRDA",
        "benefit_description": (
            "Guaranteed pension of ₹1,000–₹5,000/month after age 60, "
            "based on contribution amount and entry age. "
            "Targets unorganized sector workers without pension coverage."
        ),
        "benefit_amount_inr": None,
        "benefit_amount_note": (
            "Pension ₹1,000–₹5,000/month depending on chosen amount, "
            "entry age, and monthly contribution. "
            "Earlier entry = lower contribution for same pension."
        ),
        "benefit_frequency": "monthly_post_age_60",
        "eligibility_type": "rule_based",
        "guideline_version": "APY Operational Framework 2015; PFRDA guidelines; Oct 2022 amendment",
        "last_verified_date": "2024-01-01",
        "scheme_launched": "2015-06-01",

        "inclusion_rules": [
            {
                "rule_id": "A1",
                "field": "age",
                "operator": "between",
                "value": [18, 40],
                "confidence": "HIGH",
                "source_note": (
                    "Applicant must be between 18 and 40 years. "
                    "Minimum 20 years of contribution required (until age 60)."
                )
            },
            {
                "rule_id": "A2",
                "field": "is_indian_citizen",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": "Indian citizens only. NRIs not eligible."
            },
            {
                "rule_id": "A3",
                "field": "has_savings_bank_account",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": "Savings bank account required for auto-debit of contributions."
            },
        ],

        "exclusion_rules": [
            {
                "rule_id": "B1",
                "field": "is_income_taxpayer",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": (
                    "Income taxpayers NOT eligible for APY. "
                    "Rule added in October 2022. "
                    "Existing accounts opened before this date are not affected."
                ),
                "critical_note": "Taxpayer exclusion added Oct 2022 — frequently absent from older descriptions"
            },
            {
                "rule_id": "B2",
                "field": "is_member_of_epf_esi_or_other_statutory_pension",
                "operator": "equals",
                "value": True,
                "confidence": "MEDIUM",
                "source_note": (
                    "APY targets those WITHOUT existing social security pension. "
                    "EPF/EPS members may technically open APY but scheme targets "
                    "unorganized sector. MEDIUM confidence on hard exclusion status."
                )
            },
            {
                "rule_id": "B3",
                "field": "age",
                "operator": "greater_than",
                "value": 40,
                "confidence": "HIGH",
                "source_note": "Cannot enroll above age 40"
            },
        ],

        "ambiguous_rules": [
            {
                "rule_id": "AMB1",
                "description": (
                    "Government co-contribution: 50% or ₹1,000/year (whichever lower) "
                    "was available for accounts opened June 2015–March 2016. "
                    "This co-contribution period has ended for all new subscribers."
                ),
                "why_ambiguous": "Many scheme descriptions still mention govt co-contribution incorrectly",
                "system_response": "clarify_co_contribution_is_ended",
                "clarifying_question": None
            },
        ],

        "prerequisite_schemes": [],
        "prerequisite_note": "Savings bank account required. No other scheme prerequisite.",

        "required_documents": [
            "aadhaar_card",
            "mobile_number_for_otp",
            "jan_dhan_or_active_bank_account",
        ],

        "application_url": "https://www.npscra.nsdl.co.in/scheme-apy.php",
        "helpline": "1800-110-069",

        "state_variations": {
            "has_variations": False,
            "states_with_variations": [],
            "variation_note": "Central scheme, uniform nationally."
        },

        "common_hallucinations": [
            "Available to all age groups — WRONG. Entry age 18–40 only.",
            "Government contributes to all new accounts — WRONG. Co-contribution period ended.",
            "Available to income taxpayers — WRONG. Taxpayers excluded since Oct 2022.",
            "Pension of ₹5,000/month regardless of contribution — WRONG. Amount depends on contribution.",
            "NRIs can enroll — WRONG. Indian citizens only.",
        ],
    },

    # =========================================================================
    # 11. PM JEEVAN JYOTI BIMA YOJANA
    # =========================================================================
    "pmjjby": {
        "scheme_id": "pmjjby",
        "name": "Pradhan Mantri Jeevan Jyoti Bima Yojana",
        "ministry": "Ministry of Finance / Department of Financial Services",
        "benefit_description": (
            "Life insurance cover of ₹2 lakh on death (any cause). "
            "Annual premium of ₹436/year (revised from ₹330 in June 2022). "
            "Auto-debited from bank account annually."
        ),
        "benefit_amount_inr": 200000,
        "premium_amount_inr": 436,
        "premium_note": "Premium revised to ₹436/year from June 2022. Was ₹330 earlier.",
        "benefit_frequency": "annual_renewable_insurance",
        "eligibility_type": "rule_based",
        "guideline_version": "PMJJBY scheme details 2015; premium revision June 2022",
        "last_verified_date": "2024-01-01",
        "scheme_launched": "2015-05-09",

        "inclusion_rules": [
            {
                "rule_id": "A1",
                "field": "age",
                "operator": "between",
                "value": [18, 50],
                "confidence": "HIGH",
                "source_note": (
                    "Age 18 to 50 years for enrollment. "
                    "Cover continues until age 55 if enrolled before 50."
                )
            },
            {
                "rule_id": "A2",
                "field": "has_savings_bank_account",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": "Bank account required for auto-debit of annual premium"
            },
            {
                "rule_id": "A3",
                "field": "is_indian_citizen",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": "Indian citizens only"
            },
        ],

        "exclusion_rules": [
            {
                "rule_id": "B1",
                "field": "age",
                "operator": "greater_than",
                "value": 50,
                "confidence": "HIGH",
                "source_note": "Cannot enroll above age 50"
            },
            {
                "rule_id": "B2",
                "field": "bank_account_has_insufficient_balance",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": (
                    "If auto-debit fails due to insufficient balance, policy lapses. "
                    "Can be reinstated with full premium and good health declaration."
                )
            },
        ],

        "ambiguous_rules": [],

        "prerequisite_schemes": ["pm_jan_dhan_yojana"],
        "prerequisite_note": (
            "Bank account required. Premium auto-debited — "
            "account must have balance on May 31 each year."
        ),

        "required_documents": [
            "aadhaar_card",
            "jan_dhan_or_active_bank_account",
            "mobile_number_for_otp",
        ],

        "application_url": "https://www.jansuraksha.gov.in",
        "helpline": "1800-180-1111",

        "state_variations": {
            "has_variations": False,
            "states_with_variations": [],
            "variation_note": "Central scheme. No state variations in rules."
        },

        "common_hallucinations": [
            "Premium is ₹330/year — WRONG. Revised to ₹436/year from June 2022.",
            "Cover for accidental death only — WRONG. Any cause of death covered.",
            "Available up to age 60 — WRONG. Enrollment only up to age 50.",
            "Free for BPL families — WRONG. Premium applies to all.",
            "Cover amount is ₹1 lakh — WRONG. ₹2 lakh life cover.",
        ],
    },

    # =========================================================================
    # 12. PM SURAKSHA BIMA YOJANA
    # =========================================================================
    "pmsby": {
        "scheme_id": "pmsby",
        "name": "Pradhan Mantri Suraksha Bima Yojana",
        "ministry": "Ministry of Finance / Department of Financial Services",
        "benefit_description": (
            "Accidental death and disability insurance. "
            "₹2 lakh for accidental death or full disability. "
            "₹1 lakh for partial disability. "
            "Annual premium of ₹20/year."
        ),
        "benefit_amount_inr": 200000,
        "benefit_partial_disability_inr": 100000,
        "premium_amount_inr": 20,
        "benefit_frequency": "annual_renewable_insurance",
        "eligibility_type": "rule_based",
        "guideline_version": "PMSBY scheme details 2015",
        "last_verified_date": "2024-01-01",
        "scheme_launched": "2015-05-09",

        "inclusion_rules": [
            {
                "rule_id": "A1",
                "field": "age",
                "operator": "between",
                "value": [18, 70],
                "confidence": "HIGH",
                "source_note": "Age 18 to 70 years. Broader range than PMJJBY."
            },
            {
                "rule_id": "A2",
                "field": "has_savings_bank_account",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": "Bank account required for auto-debit"
            },
            {
                "rule_id": "A3",
                "field": "is_indian_citizen",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": "Indian citizens only"
            },
        ],

        "exclusion_rules": [
            {
                "rule_id": "B1",
                "field": "age",
                "operator": "greater_than",
                "value": 70,
                "confidence": "HIGH",
                "source_note": "Above 70: not eligible"
            },
        ],

        "ambiguous_rules": [
            {
                "rule_id": "AMB1",
                "description": (
                    "'Partial disability' requires medical certification of loss of "
                    "use of both eyes, both hands, both feet, or one eye and one hand/foot."
                ),
                "why_ambiguous": "Medical determination at claim time — not intake level",
                "system_response": "note_in_benefit_description",
                "clarifying_question": None
            },
        ],

        "prerequisite_schemes": ["pm_jan_dhan_yojana"],

        "required_documents": [
            "aadhaar_card",
            "jan_dhan_or_active_bank_account",
        ],

        "application_url": "https://www.jansuraksha.gov.in",
        "helpline": "1800-180-1111",

        "state_variations": {
            "has_variations": False,
            "states_with_variations": [],
            "variation_note": "Central scheme. No state variations."
        },

        "common_hallucinations": [
            "Covers natural death — WRONG. Accidental death/disability only.",
            "Premium is ₹330 or ₹436 — WRONG. Only ₹20/year.",
            "Maximum age 55 — WRONG. Up to age 70.",
            "Benefit is ₹5 lakh — WRONG. ₹2 lakh death/full disability, ₹1 lakh partial.",
        ],
    },

    # =========================================================================
    # 13. NATIONAL FAMILY BENEFIT SCHEME (NFBS)
    # =========================================================================
    "nfbs": {
        "scheme_id": "nfbs",
        "name": "National Family Benefit Scheme (NFBS) under NSAP",
        "ministry": "Ministry of Rural Development",
        "benefit_description": (
            "One-time lump sum of ₹20,000 to BPL households on death "
            "of primary breadwinner aged 18–59 years."
        ),
        "benefit_amount_inr": 20000,
        "benefit_frequency": "one_time_on_death_of_breadwinner",
        "eligibility_type": "rule_based",
        "guideline_version": "NSAP NFBS Guidelines 2014",
        "last_verified_date": "2024-01-01",
        "scheme_launched": "1995-08-15",

        "inclusion_rules": [
            {
                "rule_id": "A1",
                "field": "is_bpl_household",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": "BPL household as per state BPL list. NSAP NFBS guidelines."
            },
            {
                "rule_id": "A2",
                "field": "primary_breadwinner_died",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": (
                    "The deceased must have been the primary breadwinner. "
                    "Age of deceased must have been 18–59 at time of death."
                )
            },
            {
                "rule_id": "A3",
                "field": "deceased_age_at_death",
                "operator": "between",
                "value": [18, 59],
                "confidence": "HIGH",
                "source_note": "Breadwinner must have died between ages 18 and 59."
            },
            {
                "rule_id": "A4",
                "field": "is_surviving_household_member",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": "Benefit paid to surviving member, not the deceased"
            },
        ],

        "exclusion_rules": [
            {
                "rule_id": "B1",
                "field": "is_bpl_household",
                "operator": "equals",
                "value": False,
                "confidence": "HIGH",
                "source_note": "Non-BPL households not eligible"
            },
            {
                "rule_id": "B2",
                "field": "deceased_age_at_death",
                "operator": "not_between",
                "value": [18, 59],
                "confidence": "HIGH",
                "source_note": "Death outside 18–59 age range does not qualify"
            },
        ],

        "ambiguous_rules": [
            {
                "rule_id": "AMB1",
                "description": (
                    "'Primary breadwinner' not precisely defined in NSAP guidelines. "
                    "Operationally determined by district welfare officers."
                ),
                "why_ambiguous": "Definitional ambiguity in guidelines — state discretion applies",
                "system_response": "flag_for_clarification_at_application",
                "clarifying_question": (
                    "Was the person who passed away the main income earner of your household?"
                )
            },
        ],

        "prerequisite_schemes": ["pm_jan_dhan_yojana"],

        "required_documents": [
            "aadhaar_card",
            "bpl_card_or_certificate",
            "bank_account_linked_to_aadhaar",
            "age_proof_birth_certificate_or_school_leaving",
            "death_certificate_of_breadwinner",
            "proof_of_relationship_to_deceased",
        ],

        "application_url": "https://nsap.nic.in",
        "helpline": "1800-11-1363",

        "state_variations": {
            "has_variations": True,
            "states_with_variations": ["all_states"],
            "variation_note": (
                "Central scheme, state implementation varies. "
                "Some states have enhanced state-funded top-up."
            )
        },

        "common_hallucinations": [
            "Available for death of any family member — WRONG. Primary breadwinner only.",
            "No age restriction on deceased — WRONG. Age 18–59 at time of death.",
            "Available to all — WRONG. BPL households only.",
            "Monthly benefit — WRONG. One-time lump sum payment.",
            "₹40,000 benefit — WRONG. ₹20,000 central contribution.",
        ],
    },

    # =========================================================================
    # 14. PM SVANidhi
    # =========================================================================
    "pm_svanidhi": {
        "scheme_id": "pm_svanidhi",
        "name": "PM Street Vendor's AtmaNirbhar Nidhi (PM SVANidhi)",
        "ministry": "Ministry of Housing and Urban Affairs",
        "benefit_description": (
            "Collateral-free working capital loans for urban street vendors. "
            "Tier 1: ₹10,000 | Tier 2: ₹20,000 (on timely repayment) | "
            "Tier 3: ₹50,000 (on timely repayment of Tier 2). "
            "7% interest subsidy on timely repayment. "
            "Digital transaction incentive: up to ₹100/month cashback."
        ),
        "benefit_amount_inr": 10000,
        "benefit_amount_note": "Progressive loan: ₹10K → ₹20K → ₹50K. Loan, not grant.",
        "benefit_frequency": "loan_with_subsidy_on_repayment",
        "eligibility_type": "rule_based",
        "guideline_version": "PM SVANidhi Guidelines 2020; revised 2022",
        "last_verified_date": "2024-01-01",
        "scheme_launched": "2020-06-01",

        "inclusion_rules": [
            {
                "rule_id": "A1",
                "field": "is_street_vendor",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": (
                    "Must be a street vendor per Street Vendors Act 2014 definition: "
                    "vending in urban areas, stationary or mobile (hawkers)."
                )
            },
            {
                "rule_id": "A2",
                "field": "was_vending_before_march_24_2020",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": (
                    "Must have been vending on or before March 24, 2020 "
                    "(pre-COVID lockdown date)."
                )
            },
            {
                "rule_id": "A3",
                "field": "has_vending_certificate_or_identity_card",
                "operator": "equals",
                "value": True,
                "confidence": "MEDIUM",
                "source_note": (
                    "Must have: Certificate of Vending OR Identity Card from ULB "
                    "OR Letter of Recommendation (LoR) from ULB/TVC. "
                    "MEDIUM confidence: LoR route broadens access beyond formal docs."
                )
            },
            {
                "rule_id": "A4",
                "field": "residence_type",
                "operator": "equals",
                "value": "urban",
                "confidence": "HIGH",
                "source_note": "PM SVANidhi is for URBAN street vendors only."
            },
        ],

        "exclusion_rules": [
            {
                "rule_id": "B1",
                "field": "residence_type",
                "operator": "equals",
                "value": "rural",
                "confidence": "HIGH",
                "source_note": "Rural areas not covered"
            },
        ],

        "ambiguous_rules": [
            {
                "rule_id": "AMB1",
                "description": (
                    "Peri-urban vendors operating just outside city limits "
                    "may or may not qualify depending on ULB jurisdiction."
                ),
                "why_ambiguous": "ULB boundary definitions vary",
                "system_response": "prompt_ulb_verification",
                "clarifying_question": (
                    "Do you vend within the limits of a Municipality, "
                    "Municipal Corporation, or Town Panchayat?"
                )
            },
        ],

        "prerequisite_schemes": ["pm_jan_dhan_yojana"],
        "prerequisite_note": (
            "Bank account required. ULB registration/TVC letter is "
            "a process prerequisite within the scheme."
        ),

        "required_documents": [
            "aadhaar_card",
            "jan_dhan_or_active_bank_account",
            "mobile_number_for_otp",
            "vending_certificate_or_ulb_identity_card_or_lor",
        ],

        "application_url": "https://pmsvanidhi.mohua.gov.in",
        "helpline": "1800-11-1979",

        "state_variations": {
            "has_variations": True,
            "states_with_variations": ["all_states"],
            "variation_note": (
                "ULBs implement the scheme. Speed of LoR issuance and "
                "Town Vending Committee functioning varies significantly by city."
            )
        },

        "common_hallucinations": [
            "Available to rural vendors — WRONG. Urban only.",
            "It is a grant — WRONG. It is a loan with interest subsidy on repayment.",
            "₹10,000 is the maximum — WRONG. Progressive up to ₹50,000.",
            "Requires formal business registration — WRONG. LoR route available.",
            "No pre-COVID vending requirement — WRONG. Must have been vending before March 24, 2020.",
        ],
    },

    # =========================================================================
    # 15. JANANI SURAKSHA YOJANA
    # =========================================================================
    "janani_suraksha_yojana": {
        "scheme_id": "janani_suraksha_yojana",
        "name": "Janani Suraksha Yojana (JSY)",
        "ministry": "Ministry of Health and Family Welfare",
        "benefit_description": (
            "Cash assistance for institutional delivery. "
            "LPS rural: ₹1,400 | LPS urban: ₹1,000 | "
            "HPS rural: ₹700 | HPS urban: ₹600. "
            "ASHA worker receives additional incentive."
        ),
        "benefit_amount_inr": None,
        "benefit_amount_note": (
            "LPS rural ₹1,400 | LPS urban ₹1,000 | HPS rural ₹700 | HPS urban ₹600. "
            "LPS = Low Performing States (typically BIMARU + NE states). "
            "HPS = High Performing States (southern/western states)."
        ),
        "benefit_frequency": "one_time_per_delivery",
        "eligibility_type": "rule_based",
        "guideline_version": "JSY Operational Guidelines 2005; subsequent MoHFW circulars",
        "last_verified_date": "2024-01-01",
        "scheme_launched": "2005-04-12",

        "inclusion_rules": [
            {
                "rule_id": "A1",
                "field": "gender",
                "operator": "equals",
                "value": "female",
                "confidence": "HIGH",
                "source_note": "Pregnant women only"
            },
            {
                "rule_id": "A2",
                "field": "is_pregnant_or_recently_delivered",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": "Must be pregnant woman registered at health facility"
            },
            {
                "rule_id": "A3",
                "field": "delivery_at_govt_or_accredited_facility",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": (
                    "Cash assistance conditional on INSTITUTIONAL DELIVERY. "
                    "Home deliveries do not qualify for the main cash benefit."
                )
            },
            {
                "rule_id": "A4",
                "field": "is_bpl_or_sc_st",
                "operator": "equals",
                "value": True,
                "confidence": "MEDIUM",
                "source_note": (
                    "In High Performing States (HPS): restricted to BPL and SC/ST women. "
                    "In Low Performing States (LPS): ALL pregnant women eligible. "
                    "MEDIUM confidence: state classification may have been revised."
                )
            },
            {
                "rule_id": "A5",
                "field": "age",
                "operator": "greater_than_or_equal",
                "value": 19,
                "confidence": "MEDIUM",
                "source_note": (
                    "JSY guidelines specify benefit for mothers aged 19+. "
                    "MEDIUM confidence: implementation varies by state."
                )
            },
        ],

        "exclusion_rules": [
            {
                "rule_id": "B1",
                "field": "delivery_at_home",
                "operator": "equals",
                "value": True,
                "confidence": "HIGH",
                "source_note": (
                    "Home deliveries: no JSY cash benefit. "
                    "Scheme designed to incentivize institutional delivery."
                )
            },
            {
                "rule_id": "B2",
                "field": "birth_order",
                "operator": "greater_than",
                "value": 2,
                "confidence": "LOW",
                "source_note": (
                    "LOW CONFIDENCE — Original JSY guidelines restricted benefit "
                    "to first 2 live births in HPS. May have been removed. "
                    "DO NOT apply without verifying current state policy."
                ),
                "critical_note": (
                    "LOW CONFIDENCE RULE — Verify before applying. "
                    "Birth order restriction status is unclear."
                )
            },
        ],

        "ambiguous_rules": [
            {
                "rule_id": "AMB1",
                "description": (
                    "LPS/HPS state classification established 2005, may have been revised. "
                    "Affects both eligibility scope and benefit amount."
                ),
                "why_ambiguous": "State classification may have been revised by MoHFW",
                "system_response": "use_state_field_to_classify_then_flag",
                "clarifying_question": None,
                "lps_states_approximate": [
                    "uttar_pradesh", "madhya_pradesh", "rajasthan", "bihar",
                    "jharkhand", "odisha", "uttarakhand", "chhattisgarh",
                    "assam", "jammu_and_kashmir", "meghalaya", "nagaland",
                    "manipur", "mizoram", "arunachal_pradesh", "sikkim", "tripura"
                ],
                "confidence_on_lps_list": "MEDIUM"
            },
        ],

        "prerequisite_schemes": ["pm_jan_dhan_yojana"],
        "prerequisite_note": (
            "Bank account for cash transfer. "
            "ANC registration at health facility strongly recommended."
        ),

        "required_documents": [
            "aadhaar_card",
            "bank_account_linked_to_aadhaar",
            "pregnancy_registration_certificate_from_anganwadi_or_phc",
            "bpl_card_or_certificate",
            "residence_proof",
        ],

        "application_url": "https://nhm.gov.in/index1.php?lang=1&level=3&sublinkid=841&lid=309",
        "helpline": "104",

        "state_variations": {
            "has_variations": True,
            "states_with_variations": ["all_states"],
            "variation_note": (
                "LPS vs HPS classification determines eligibility scope and amount. "
                "States may have additional maternity schemes alongside JSY."
            )
        },

        "common_hallucinations": [
            "Available regardless of delivery location — WRONG. Institutional delivery required.",
            "₹1,400 benefit in all states — WRONG. LPS/HPS distinction applies.",
            "No income or category restriction — WRONG for HPS. BPL/SC/ST only in HPS.",
            "Monthly payment during pregnancy — WRONG. One-time after delivery.",
            "Same as PMMVY — WRONG. JSY is delivery incentive; PMMVY is maternity benefit.",
        ],
    },

}  # END OF SCHEMES DICTIONARY


# =============================================================================
# CONFIDENCE AUDIT
# =============================================================================

CONFIDENCE_AUDIT = {
    "audit_date": "2024-01-01",
    "audited_by": "PENDING — HUMAN REVIEW REQUIRED",
    "methodology": (
        "Every LOW and MEDIUM confidence field in SCHEMES is documented below. "
        "LOW = do not use without independent verification. "
        "MEDIUM = use with caution, verify against source document."
    ),

    "low_confidence_fields": [
        {
            "scheme_id": "pmay_urban",
            "rule_id": "income_categories.MIG_I",
            "field": "annual_income_ceiling_inr",
            "value_used": 1200000,
            "reason": (
                "PMAY-U 2.0 announced in Budget 2024. MIG income categories "
                "and benefits are under revision. The ₹12 lakh ceiling for MIG-I "
                "was accurate for PMAY-U 1.0 CLSS but CLSS is discontinued. "
                "The applicable benefit structure for MIG under PMAY-U 2.0 "
                "is not finalized as of this file's creation."
            ),
            "verification_action": "Check MoHUA PMAY-U 2.0 guidelines when released"
        },
        {
            "scheme_id": "pmay_urban",
            "rule_id": "income_categories.MIG_II",
            "field": "annual_income_ceiling_inr",
            "value_used": 1800000,
            "reason": "Same as MIG_I above. PMAY-U 2.0 revision pending.",
            "verification_action": "Check MoHUA PMAY-U 2.0 guidelines when released"
        },
        {
            "scheme_id": "janani_suraksha_yojana",
            "rule_id": "B2",
            "field": "birth_order_restriction",
            "value_used": "greater_than_2_excluded",
            "reason": (
                "Original JSY guidelines had birth order restriction in HPS. "
                "This has been implemented inconsistently and may have been "
                "formally removed in subsequent MoHFW circulars."
            ),
            "verification_action": (
                "Verify against most recent JSY operational guidelines from MoHFW. "
                "Check state-level JSY guidelines for HPS states specifically."
            )
        },
        {
            "scheme_id": "atal_pension_yojana",
            "rule_id": "B2",
            "field": "epf_member_exclusion",
            "value_used": "medium_confidence_targeting_not_hard_exclusion",
            "reason": (
                "PFRDA guidelines target APY at unorganized sector (non-EPF). "
                "EPF members are not legally barred but the scheme intent excludes them. "
                "Whether this is a soft or hard exclusion is unclear."
            ),
            "verification_action": "Check latest PFRDA APY master circular"
        },
    ],

    "medium_confidence_fields": [
        {
            "scheme_id": "pm_kisan",
            "rule_id": "A5",
            "field": "land_is_cultivable",
            "reason": (
                "PM-KISAN guidelines use 'farmer family' implying cultivable land, "
                "but 'cultivable' is not legally defined in the scheme document."
            ),
            "verification_action": "Review PM-KISAN FAQ and MoA clarification circulars"
        },
        {
            "scheme_id": "pmay_gramin",
            "rule_id": "A4",
            "field": "secc_listed_as_inclusion_criterion",
            "reason": (
                "PMAY-G uses both SECC 2011 and Awaas Plus 2018 survey. "
                "The relative weight is complex. Simplified here."
            ),
            "verification_action": "Review PMAY-G Awaas Plus integration guidelines"
        },
        {
            "scheme_id": "pmuy",
            "rule_id": "A3",
            "field": "is_bpl_listed_or_qualifying_category",
            "reason": (
                "PMUY 2.0 expanded categories significantly across multiple notifications. "
                "Encoding here covers major categories but may miss sub-categories."
            ),
            "verification_action": "Review all PMUY 2.0 MoPNG notifications and circulars"
        },
        {
            "scheme_id": "pmmvy",
            "rule_id": "A3",
            "field": "pmmvy_2_implementation_status",
            "reason": (
                "PMMVY 2.0 second girl child benefit announced Nov 2022. "
                "State-level implementation is not uniform."
            ),
            "verification_action": "Check WCD ministry portal for state implementation status"
        },
        {
            "scheme_id": "nsap_ignoaps",
            "rule_id": "B2",
            "field": "govt_pensioner_exclusion",
            "reason": (
                "NSAP guidelines discourage duplicate pension but exclusion of "
                "government service pensioners is implemented differently by states."
            ),
            "verification_action": "Check state-specific NSAP IGNOAPS implementation orders"
        },
        {
            "scheme_id": "janani_suraksha_yojana",
            "rule_id": "A4_LPS",
            "field": "lps_state_classification",
            "reason": (
                "LPS/HPS classification was established in 2005. "
                "State reclassification may have occurred."
            ),
            "verification_action": "Verify current LPS/HPS list from MoHFW NHM division"
        },
        {
            "scheme_id": "janani_suraksha_yojana",
            "rule_id": "A5",
            "field": "minimum_age_19",
            "reason": (
                "The age 19 threshold appears in some state implementations "
                "but is not uniformly enforced."
            ),
            "verification_action": "Review state-specific JSY operational guidelines"
        },
        {
            "scheme_id": "pmay_urban",
            "rule_id": "A3",
            "field": "income_ceiling_1800000",
            "reason": "MIG income ceiling under PMAY-U 2.0 is under revision.",
            "verification_action": "Check PMAY-U 2.0 guidelines on pmaymis.gov.in"
        },
        {
            "scheme_id": "pm_svanidhi",
            "rule_id": "A3",
            "field": "lor_alternative_to_vending_certificate",
            "reason": (
                "LoR processing and acceptance varies by ULB. "
                "Boolean encoding oversimplifies the practical access barrier."
            ),
            "verification_action": "Review ULB-level implementation and TVC functioning"
        },
    ],

    "known_staleness_risks": [
        {
            "scheme_id": "pmjjby",
            "field": "premium_amount_inr",
            "note": "Premium revised June 2022. May be revised again.",
            "check_frequency": "annual"
        },
        {
            "scheme_id": "sukanya_samriddhi",
            "field": "interest_rate",
            "note": "Interest rate revised quarterly. DO NOT HARDCODE.",
            "check_frequency": "quarterly"
        },
        {
            "scheme_id": "mgnrega",
            "field": "wage_rates",
            "note": "State-specific wage rates notified annually by MoRD.",
            "check_frequency": "annual"
        },
        {
            "scheme_id": "pmay_urban",
            "field": "all_rules",
            "note": "PMAY-U 2.0 announced. Entire scheme structure may change.",
            "check_frequency": "immediate_on_guideline_release"
        },
        {
            "scheme_id": "nsap_ignoaps",
            "field": "state_top_up_amounts",
            "note": "State pension top-ups revised in state budgets annually.",
            "check_frequency": "annual_post_state_budgets"
        },
    ],

    "schemes_requiring_immediate_human_review_before_deploy": [
        {
            "scheme_id": "pmay_urban",
            "reason": "PMAY-U 2.0 rules not finalized. Using outdated structure."
        },
        {
            "scheme_id": "janani_suraksha_yojana",
            "reason": "B2 birth order rule is LOW confidence. LPS/HPS list needs verification."
        },
        {
            "scheme_id": "ab_pmjay",
            "reason": (
                "State expansion scheme rules not encoded. "
                "Only central SECC-based eligibility modeled."
            )
        },
    ],

    "hallucinations_this_file_may_itself_contain": [
        (
            "Income thresholds for PMAY-U MIG categories may be stale "
            "given PMAY-U 2.0 announcement. Marked LOW confidence."
        ),
        (
            "JSY birth order restriction (B2) is flagged LOW confidence. "
            "Do not apply without verification."
        ),
        (
            "PMMVY 2.0 second-girl-child benefit encoding is MEDIUM confidence "
            "because state implementation is not uniform."
        ),
        (
            "APY EPF member exclusion is MEDIUM confidence — may be targeting "
            "guidance rather than hard legal exclusion."
        ),
        (
            "NSAP IGNOAPS government pensioner exclusion varies by state. "
            "The rule as encoded (B2) is an approximation of common practice."
        ),
    ],
}

# =============================================================================
# DATABASE VALIDITY FLAG
# Set by the validation block below when run as __main__.
# Checked by matching_engine.py at import time.
# =============================================================================
DATABASE_VALID = True  # Optimistic default; __main__ block will override if errors found


# =============================================================================
# TASK 2 — VALIDATION BLOCK
# =============================================================================

if __name__ == "__main__":
    import sys

    errors_found = 0
    warnings_found = 0

    print(f"Loaded {len(SCHEMES)} schemes")
    print()

    VALID_ELIGIBILITY_TYPES = {"rule_based", "database_membership", "hybrid"}
    VALID_CONFIDENCE_LEVELS = {"HIGH", "MEDIUM", "LOW"}
    VALID_OPERATORS = {
        "equals", "not_equals", "greater_than", "less_than",
        "greater_than_or_equal", "less_than_or_equal",
        "in", "not_in", "is_true", "is_false", "exists",
        "between", "not_between",
    }

    for scheme_id, scheme in SCHEMES.items():
        if scheme_id.startswith("_"):
            continue

        scheme_errors = []
        scheme_warnings = []

        # --- Required top-level fields ---
        required_fields = [
            "inclusion_rules", "exclusion_rules", "eligibility_type",
            "name", "ministry", "benefit_description", "required_documents",
            "application_url", "state_variations", "common_hallucinations",
            "guideline_version", "last_verified_date", "prerequisite_schemes",
        ]
        for field in required_fields:
            if field not in scheme:
                scheme_errors.append(f"Missing required field: '{field}'")

        # --- scheme_id consistency ---
        if scheme.get("scheme_id") != scheme_id:
            scheme_errors.append(
                f"scheme_id field '{scheme.get('scheme_id')}' "
                f"doesn't match dictionary key '{scheme_id}'"
            )

        # --- eligibility_type ---
        etype = scheme.get("eligibility_type")
        if etype not in VALID_ELIGIBILITY_TYPES:
            scheme_errors.append(f"Invalid eligibility_type: '{etype}'")

        # --- inclusion_rules ---
        for rule in scheme.get("inclusion_rules", []):
            if "rule_id" not in rule:
                scheme_errors.append(f"Inclusion rule missing 'rule_id': {rule}")
            if "confidence" not in rule:
                scheme_errors.append(
                    f"Inclusion rule {rule.get('rule_id', '?')} missing 'confidence'"
                )
            if rule.get("confidence") not in VALID_CONFIDENCE_LEVELS:
                scheme_errors.append(
                    f"Inclusion rule {rule.get('rule_id', '?')} has invalid "
                    f"confidence: '{rule.get('confidence')}'"
                )
            if "field" not in rule:
                scheme_errors.append(
                    f"Inclusion rule {rule.get('rule_id', '?')} missing 'field'"
                )
            if "operator" not in rule:
                scheme_errors.append(
                    f"Inclusion rule {rule.get('rule_id', '?')} missing 'operator'"
                )
            elif rule.get("operator") not in VALID_OPERATORS:
                scheme_warnings.append(
                    f"Inclusion rule {rule.get('rule_id', '?')} uses "
                    f"unrecognized operator: '{rule.get('operator')}'"
                )
            if "source_note" not in rule or not rule["source_note"]:
                scheme_warnings.append(
                    f"Inclusion rule {rule.get('rule_id', '?')} missing source_note"
                )

        # --- exclusion_rules ---
        for rule in scheme.get("exclusion_rules", []):
            if "rule_id" not in rule:
                scheme_errors.append(f"Exclusion rule missing 'rule_id': {rule}")
            if "confidence" not in rule:
                scheme_errors.append(
                    f"Exclusion rule {rule.get('rule_id', '?')} missing 'confidence'"
                )
            if rule.get("confidence") not in VALID_CONFIDENCE_LEVELS:
                scheme_errors.append(
                    f"Exclusion rule {rule.get('rule_id', '?')} has invalid "
                    f"confidence: '{rule.get('confidence')}'"
                )
            if "source_note" not in rule or not rule["source_note"]:
                scheme_warnings.append(
                    f"Exclusion rule {rule.get('rule_id', '?')} missing source_note"
                )

        # --- required_documents must all be plain strings ---
        for doc in scheme.get("required_documents", []):
            if not isinstance(doc, str):
                scheme_errors.append(
                    f"required_documents contains non-string value: {doc!r} "
                    f"(type: {type(doc).__name__})"
                )

        # --- prerequisite_schemes must all be plain strings ---
        for prereq in scheme.get("prerequisite_schemes", []):
            if not isinstance(prereq, str):
                scheme_errors.append(
                    f"prerequisite_schemes contains non-string value: {prereq!r}"
                )

        # --- common_hallucinations should be non-empty for rule_based ---
        if (scheme.get("eligibility_type") == "rule_based"
                and not scheme.get("common_hallucinations")):
            scheme_warnings.append("common_hallucinations list is empty for rule_based scheme")

        # --- hybrid schemes should have hybrid_config ---
        if etype == "hybrid" and "hybrid_config" not in scheme:
            scheme_warnings.append("hybrid scheme missing 'hybrid_config'")

        # --- database_membership schemes should have database_membership_config ---
        if etype == "database_membership" and "database_membership_config" not in scheme:
            scheme_errors.append("database_membership scheme missing 'database_membership_config'")

        # --- Print results for this scheme ---
        inclusion_count = len(scheme.get("inclusion_rules", []))
        exclusion_count = len(scheme.get("exclusion_rules", []))

        if scheme_errors:
            print(f"  ✗ {scheme_id} — {inclusion_count} inclusion rules, "
                  f"{exclusion_count} exclusion rules")
            for err in scheme_errors:
                print(f"      ERROR: {err}")
                errors_found += 1
        elif scheme_warnings:
            print(f"  ⚠ {scheme_id} — {inclusion_count} inclusion rules, "
                  f"{exclusion_count} exclusion rules")
            for warn in scheme_warnings:
                print(f"      WARN:  {warn}")
                warnings_found += 1
        else:
            print(f"  ✓ {scheme_id} — {inclusion_count} inclusion rules, "
                  f"{exclusion_count} exclusion rules")

    print()
    if errors_found == 0:
        print(f"All schemes validated successfully. "
              f"({warnings_found} warnings — review before production)")
        DATABASE_VALID = True
    else:
        print(f"VALIDATION FAILED: {errors_found} error(s), {warnings_found} warning(s).")
        print("Do not deploy until all errors are resolved.")
        DATABASE_VALID = False
        sys.exit(1)