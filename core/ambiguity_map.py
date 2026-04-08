"""
KALAM — Welfare Scheme Matching Engine
Ambiguity Map

PURPOSE:
--------
This file is a REQUIRED SUBMISSION DELIVERABLE.
It documents every known ambiguity across all 15 schemes in four categories:

    1. Internal contradictions — rules within a single scheme that conflict
    2. Cross-scheme overlaps   — inter-scheme interactions a naive system handles wrong
    3. Definitional ambiguities — terms with no computable operational definition
    4. Stale data risks         — rules that reference time-sensitive data

SEVERITY LEVELS:
    HIGH   — Could cause a wrong eligibility decision (false positive or false negative)
    MEDIUM — Causes confidence reduction; match result is uncertain but not wrong
    LOW    — Informational; does not affect match output but should be disclosed

HOW THIS FILE IS USED:
    1. matching_engine.py imports get_high_severity_ambiguities() and surfaces
       HIGH severity items in every match output that involves the affected scheme.
    2. The submission checklist requires this file as a standalone artifact.
    3. Human auditors use this as their review checklist before deployment.

Dependencies: none (standalone file, does not import schemes_database)
"""

from __future__ import annotations
from typing import Any


# =============================================================================
# CATEGORY 1 — INTERNAL CONTRADICTIONS
# Rules within a single scheme that conflict or create unevaluable logic.
# =============================================================================

_INTERNAL_CONTRADICTIONS: list[dict[str, Any]] = [

    {
        "ambiguity_id": "INT_001",
        "type": "internal_contradiction",
        "severity": "HIGH",
        "scheme_id": "pm_kisan",
        "description": (
            "The Group D / MTS pension carve-out (AMB1) is structurally unevaluable. "
            "Rule B8 excludes serving government employees and B9 excludes retired "
            "government employees with pension ≥ ₹10,000/month. The scheme guidelines "
            "carve out an exception for Multi-Tasking Staff (MTS) and Group D employees. "
            "However, the intake schema asks only 'is_serving_or_retired_govt_employee' "
            "and 'monthly_pension_if_retired_govt' — it does not ask employment grade. "
            "This makes the carve-out unevaluable: a Group D retiree with ₹11,000/month "
            "pension will be incorrectly excluded by B9 because the engine has no grade data."
        ),
        "affected_rules": ["B8", "B9", "AMB1"],
        "affected_fields": [
            "is_serving_or_retired_govt_employee",
            "monthly_pension_if_retired_govt",
        ],
        "missing_field_needed": "govt_employee_grade_category",
        "real_world_impact": (
            "A retired Group D government peon receiving ₹11,000/month pension "
            "who also owns 1 acre of farmland will be flagged as ineligible for "
            "PM Kisan. He is actually eligible. False negative with real financial harm: "
            "₹6,000/year missed."
        ),
        "resolution_status": "unresolved_flagged_for_clarification",
        "recommended_fix": (
            "Add 'govt_employee_grade_category' field to intake schema with options: "
            "['group_a', 'group_b', 'group_c', 'group_d_mts', 'unknown']. "
            "If 'group_d_mts': bypass B8 and B9 exclusions. "
            "If 'unknown': set confidence to LOW and flag for clarification."
        ),
        "clarifying_question": (
            "Kya aap Group D / Multi-Tasking Staff (MTS) category mein retire hue hain? "
            "(Were you retired from a Group D or MTS government post?)"
        ),
    },

    {
        "ambiguity_id": "INT_002",
        "type": "internal_contradiction",
        "severity": "HIGH",
        "scheme_id": "pm_kisan",
        "description": (
            "Asymmetric exclusion for local body elected representatives creates "
            "an inconsistency that is hard to collect correctly. "
            "Rule B5/B6 excludes BOTH current AND former MPs/MLAs/MLCs. "
            "Rule B7 excludes ONLY CURRENT Zila Panchayat Presidents and Mayors — "
            "former holders of these offices are NOT excluded. "
            "This asymmetry is real and deliberate but creates a data collection problem: "
            "the intake form field 'is_or_was_elected_representative' (boolean) collapses "
            "both categories into one, making it impossible to distinguish a former MLA "
            "(excluded) from a former Zila Panchayat President (not excluded)."
        ),
        "affected_rules": ["B5", "B6", "B7"],
        "affected_fields": ["is_or_was_elected_representative"],
        "missing_field_needed": "elected_representative_type_and_current_status",
        "real_world_impact": (
            "A former Zila Panchayat Adhyaksha who owned farmland before and after "
            "their term will be incorrectly excluded if the system treats all former "
            "elected representatives the same. "
            "Conversely, a former MLA who claims not to be a 'former elected rep' "
            "could slip through if the question is phrased ambiguously."
        ),
        "resolution_status": "unresolved_requires_schema_change",
        "recommended_fix": (
            "Replace single boolean 'is_or_was_elected_representative' with structured fields: "
            "'elected_rep_type': ['mp', 'mla', 'mlc', 'zila_panchayat_president', "
            "'municipal_mayor', 'other', 'never'] AND 'is_currently_holding_position': bool. "
            "Apply B5/B6 if type in [mp, mla, mlc] regardless of current status. "
            "Apply B7 only if type in [zila_panchayat_president, municipal_mayor] AND currently holding."
        ),
        "clarifying_question": (
            "Have you ever held an elected position? If yes: "
            "(a) MP/MLA/MLC — ever held? (b) Zila Panchayat President or Mayor — currently holding?"
        ),
    },

    {
        "ambiguity_id": "INT_003",
        "type": "internal_contradiction",
        "severity": "MEDIUM",
        "scheme_id": "pm_kisan",
        "description": (
            "The income tax exclusion (B10) uses the field 'filed_income_tax_last_assessment_year' "
            "but the profile schema also contains 'filed_income_tax' (shorter name). "
            "These are different field names for the same concept. "
            "If intake collects 'filed_income_tax', rule B10 will always fire as data_missing "
            "and route PM Kisan to partially_eligible instead of fully_eligible. "
            "This was flagged in the integration check (MISMATCH 4) but represents an "
            "internal field-naming contradiction between the intake schema and the rules schema."
        ),
        "affected_rules": ["B10"],
        "affected_fields": ["filed_income_tax_last_assessment_year", "filed_income_tax"],
        "real_world_impact": (
            "PM Kisan will never be fully_eligible — always partially_eligible — "
            "for users whose profiles use 'filed_income_tax' instead of "
            "'filed_income_tax_last_assessment_year'. Confidence score permanently capped "
            "at 0.60 due to data_missing flag. False partial eligibility."
        ),
        "resolution_status": "unresolved_schema_normalization_required",
        "recommended_fix": (
            "Standardize field name to 'filed_income_tax_last_assessment_year' throughout. "
            "Update all intake forms, API documentation, and test profiles to use this name. "
            "Add field alias resolution in matching_engine.py as interim fix: "
            "user_profile['filed_income_tax_last_assessment_year'] = "
            "user_profile.get('filed_income_tax_last_assessment_year') "
            "or user_profile.get('filed_income_tax')."
        ),
        "clarifying_question": None,
    },

    {
        "ambiguity_id": "INT_004",
        "type": "internal_contradiction",
        "severity": "HIGH",
        "scheme_id": "ab_pmjay",
        "description": (
            "AB-PMJAY is classified as database_membership, but its single inclusion rule "
            "checks 'secc_listed == True' and its single exclusion rule checks "
            "'secc_listed == False'. These two rules are logical complements — one will "
            "always be True and the other False. The rule structure implies we can evaluate "
            "eligibility from intake data, but we explicitly cannot: 'secc_listed' is not "
            "an intake field — it requires a database lookup. "
            "The rule structure is thus internally inconsistent with the eligibility_type "
            "classification: a database_membership scheme should have zero evaluable rules "
            "in the standard rule engine."
        ),
        "affected_rules": ["A1", "B1"],
        "affected_fields": ["secc_listed"],
        "real_world_impact": (
            "If 'secc_listed' somehow appears in the user profile (e.g., user says "
            "'Yes I am SECC listed'), the engine might evaluate it as rule_based and "
            "give a confident yes/no instead of routing to verify_manually. "
            "This would be a false positive or false negative depending on the value, "
            "bypassing the critical safeguard that SECC verification requires a database lookup."
        ),
        "resolution_status": "unresolved_design_tension",
        "recommended_fix": (
            "The matching_engine.py correctly short-circuits on eligibility_type == "
            "'database_membership' BEFORE evaluating any rules. This prevents the rules "
            "from ever being evaluated. However, the rules should still exist for "
            "documentation purposes. Add a comment in schemes_database.py: "
            "'These rules are DOCUMENTATION ONLY — the engine never evaluates them. "
            "SECC verification requires database lookup at pmjay.gov.in.'"
        ),
        "clarifying_question": None,
    },

    {
        "ambiguity_id": "INT_005",
        "type": "internal_contradiction",
        "severity": "HIGH",
        "scheme_id": "pmay_gramin",
        "description": (
            "PMAY-G is classified as 'hybrid' but its inclusion rule A4 checks 'secc_listed', "
            "which has the same database-lookup problem as AB-PMJAY. "
            "The hybrid classification means the engine WILL evaluate rule A4 against the "
            "user profile. If 'secc_listed' is absent (which it usually will be at intake), "
            "A4 fires as data_missing and routes PMAY-G to partially_eligible with a data gap. "
            "This is the correct behavior — but the system never surfaces the deeper truth: "
            "even if the user says 'secc_listed = True', that self-report cannot be "
            "trusted without database verification. "
            "The hybrid_config documents this but the rule engine doesn't enforce it."
        ),
        "affected_rules": ["A4"],
        "affected_fields": ["secc_listed"],
        "real_world_impact": (
            "A user who wrongly believes they are SECC-listed and fills in 'secc_listed = True' "
            "will be shown as fully_eligible for PMAY-G housing assistance. "
            "They will apply, be rejected, and lose trust in the system. "
            "False positive with significant downstream harm."
        ),
        "resolution_status": "partially_mitigated",
        "recommended_fix": (
            "Add a special field flag in the engine: 'requires_database_verification: True' "
            "for any field that is a database lookup rather than a true user attribute. "
            "If a 'requires_database_verification' field is present in user_profile, "
            "add a warning to the output regardless of its value: "
            "'secc_listed status self-reported — must be verified at pmayg.nic.in before applying.'"
        ),
        "clarifying_question": (
            "Has your household been listed in the PMAY-G beneficiary list "
            "at your Gram Panchayat? (This must be verified at your local Panchayat office.)"
        ),
    },

    {
        "ambiguity_id": "INT_006",
        "type": "internal_contradiction",
        "severity": "MEDIUM",
        "scheme_id": "pmmvy",
        "description": (
            "PMMVY has an exclusion rule B2 that checks child_number > 2, "
            "but the scheme was amended in November 2022 to allow second child "
            "if the child is a girl. This means the exclusion logic is: "
            "NOT (child_number == 1) AND NOT (child_number == 2 AND expected_child_gender == 'female'). "
            "The current B2 implementation (child_number > 2 → excluded) is a simplification "
            "that misses the conditional: a woman pregnant with her second child who expects "
            "a boy should be excluded, but a woman pregnant with her second child who expects "
            "a girl should be included. The rule as written admits both incorrectly."
        ),
        "affected_rules": ["A3", "B2"],
        "affected_fields": ["child_number", "is_first_or_qualifying_child"],
        "missing_field_needed": "expected_child_gender_if_second_pregnancy",
        "real_world_impact": (
            "A woman pregnant with her second boy child will be shown as partially_eligible "
            "for PMMVY (since child_number=2 passes B2 which only triggers at >2). "
            "She will apply for ₹6,000, be rejected, and waste an application. "
            "False positive caused by incomplete rule encoding of the 2022 amendment."
        ),
        "resolution_status": "unresolved_requires_amendment_clarification",
        "recommended_fix": (
            "Add field 'expected_child_gender' with options ['male', 'female', 'unknown']. "
            "Modify B2 to: exclude if (child_number > 2) OR (child_number == 2 AND "
            "expected_child_gender == 'male'). "
            "Flag as MEDIUM confidence pending PMMVY 2.0 full implementation verification."
        ),
        "clarifying_question": (
            "Is this your first or second pregnancy? "
            "If second: do you know the expected gender of the child? "
            "(PMMVY 2022 amendment provides ₹6,000 for second child only if girl.)"
        ),
    },

    {
        "ambiguity_id": "INT_007",
        "type": "internal_contradiction",
        "severity": "MEDIUM",
        "scheme_id": "nsap_ignoaps",
        "description": (
            "The IGNOAPS exclusion B2 ('is_receiving_other_govt_pension') conflicts with "
            "the inclusion rule A2 ('is_bpl_listed_or_destitute'). "
            "A retired government employee with a small pension (e.g., ₹3,000/month) "
            "could theoretically be BPL-listed (A2 passes) but also be receiving a "
            "government pension (B2 triggers). The scheme's intent is that destitute "
            "elderly without other income receive IGNOAPS — but the BPL inclusion and "
            "pension exclusion use different measurement systems (BPL listing vs pension receipt) "
            "that can contradict each other in edge cases. "
            "Additionally, B2 confidence is MEDIUM, meaning we're not certain "
            "this exclusion is uniformly applied."
        ),
        "affected_rules": ["A2", "B2"],
        "affected_fields": ["is_bpl_listed_or_destitute", "is_receiving_other_govt_pension"],
        "real_world_impact": (
            "A 68-year-old widower who was BPL-listed in 2011 and receives ₹2,500/month "
            "widow pension from state government will: "
            "Pass A2 (BPL listed) but trigger B2 (receiving govt pension). "
            "Result: excluded from IGNOAPS. This may or may not be the correct outcome "
            "depending on the state's implementation — some states allow this combination."
        ),
        "resolution_status": "state_dependent_unresolvable_without_state_data",
        "recommended_fix": (
            "Add 'pension_amount_if_receiving' field. "
            "Implement B2 as: exclude if pension_amount >= state-defined threshold. "
            "Most states allow IGNOAPS alongside very small pensions. "
            "Without state-specific thresholds, flag as ambiguous and route to "
            "partially_eligible with clarifying question."
        ),
        "clarifying_question": (
            "Are you currently receiving any government pension? "
            "If yes, how much per month? (Some states allow IGNOAPS alongside small pensions.)"
        ),
    },

    {
        "ambiguity_id": "INT_008",
        "type": "internal_contradiction",
        "severity": "LOW",
        "scheme_id": "sukanya_samriddhi",
        "description": (
            "SSY inclusion rule A1 checks 'has_girl_child_under_10' (boolean) and "
            "exclusion rule B1 checks 'girl_child_age > 10'. "
            "These two fields are not the same: 'has_girl_child_under_10' is a household-level "
            "boolean while 'girl_child_age' is an individual-level integer. "
            "A household with two girl children — one aged 7 and one aged 12 — would pass "
            "A1 (has a girl under 10) but whether B1 triggers depends on which girl's age "
            "is stored in 'girl_child_age'. "
            "If the user enters the 12-year-old's age, B1 triggers and the household is "
            "incorrectly excluded, when actually it qualifies for an account for the 7-year-old."
        ),
        "affected_rules": ["A1", "B1"],
        "affected_fields": ["has_girl_child_under_10", "girl_child_age"],
        "real_world_impact": (
            "Household with one eligible (age 7) and one ineligible (age 12) girl child "
            "may be told it doesn't qualify for SSY if the 12-year-old's age is entered. "
            "Missing: up to ₹1.5 lakh/year in tax-free savings opportunity."
        ),
        "resolution_status": "unresolved_requires_list_field",
        "recommended_fix": (
            "Change 'girl_child_age' to 'girl_children_ages' (list of integers). "
            "B1 should trigger only if ALL girl children are above 10. "
            "If any girl child is 10 or under, the scheme is eligible for that child."
        ),
        "clarifying_question": (
            "How many girl children do you have, and what are their ages? "
            "(SSY account can be opened for each girl child up to age 10.)"
        ),
    },

]


# =============================================================================
# CATEGORY 2 — CROSS-SCHEME OVERLAPS
# Inter-scheme interactions that naive systems handle incorrectly.
# =============================================================================

_CROSS_SCHEME_OVERLAPS: list[dict[str, Any]] = [

    {
        "ambiguity_id": "CSO_001",
        "type": "cross_scheme_overlap",
        "severity": "HIGH",
        "scheme_ids": ["pmay_gramin", "pmay_urban"],
        "description": (
            "PMAY-G and PMAY-U are mutually exclusive by design: a person is either "
            "a rural resident (PMAY-G) or an urban resident (PMAY-U). "
            "The engine correctly uses 'residence_type' to route between them. "
            "However, 'residence_type' in the intake is SELF-REPORTED. "
            "India has approximately 8,000 census towns that are classified as urban "
            "by the Census but whose residents often self-identify as 'rural'. "
            "Additionally, migrants (rural origin, urban current address) genuinely "
            "don't know which category they belong to for PMAY purposes. "
            "A person who self-reports 'rural' but lives in a census town will be "
            "shown PMAY-G options when they should be shown PMAY-U options. "
            "PMAY-G application will be rejected because the local body is urban."
        ),
        "naive_system_error": (
            "Routes entirely based on self-reported residence_type without "
            "flagging that Census classification (not self-report) determines "
            "which PMAY applies. Shows confident eligibility for wrong PMAY variant."
        ),
        "correct_behavior": (
            "Accept self-reported residence_type but add flag: "
            "'PMAY eligibility (rural vs urban) is determined by Census classification "
            "of your village/town, not self-report. Verify your settlement's classification "
            "before applying. If classified as Census Town: apply under PMAY-U.'"
        ),
        "real_world_impact": (
            "Wasted application, rejected at urban local body level, "
            "delay of 6–12 months in housing assistance."
        ),
        "resolution_status": "partially_mitigated_requires_census_api",
        "recommended_fix": (
            "Integrate Census 2011/2021 village/town classification API. "
            "If user's village appears in Census Town list → override to 'urban'. "
            "If API unavailable: flag the self-reported value as unverified "
            "and show both PMAY-G and PMAY-U with a clarification note."
        ),
        "can_claim_both": False,
        "mutual_exclusion_enforced_by": "residence_type field",
        "mutual_exclusion_reliable": False,
    },

    {
        "ambiguity_id": "CSO_002",
        "type": "cross_scheme_overlap",
        "severity": "MEDIUM",
        "scheme_ids": ["pmmvy", "janani_suraksha_yojana"],
        "description": (
            "PMMVY and JSY both target pregnant women but with different windows "
            "and different purposes. A pregnant woman can and SHOULD claim both. "
            "PMMVY: maternity cash benefit for first/second (girl) child — "
            "must register during pregnancy, paid in installments. "
            "JSY: delivery incentive — paid after institutional delivery. "
            "A naive system might incorrectly flag one as redundant with the other, "
            "or might show both as 'fully eligible' without noting that JSY requires "
            "institutional delivery (a condition PMMVY does not impose). "
            "The schemes have different eligibility conditions and both should be pursued "
            "simultaneously — not sequentially."
        ),
        "naive_system_error": (
            "Either: (a) flags JSY as duplicate of PMMVY and suppresses it, or "
            "(b) correctly shows both but fails to note that JSY has an additional "
            "condition (institutional delivery) that PMMVY does not. "
            "User may think claiming one forecloses the other."
        ),
        "correct_behavior": (
            "Show both as eligible simultaneously. "
            "Add note: 'These schemes complement each other — claim both. "
            "PMMVY: register now during pregnancy. JSY: claim after delivery at "
            "government facility. Both can be claimed for the same pregnancy.'"
        ),
        "real_world_impact": (
            "If user thinks they can only claim one, they may forgo JSY (₹700–₹1,400) "
            "or fail to register for PMMVY during pregnancy (missing the installment window)."
        ),
        "resolution_status": "unresolved_requires_complementary_flag",
        "can_claim_both": True,
        "mutual_exclusion_enforced_by": None,
        "recommended_fix": (
            "Add 'complementary_schemes' field to scheme definitions. "
            "pmmvy.complementary_schemes = ['janani_suraksha_yojana']. "
            "Engine should show a 'Claim Together' section for complementary scheme pairs."
        ),
    },

    {
        "ambiguity_id": "CSO_003",
        "type": "cross_scheme_overlap",
        "severity": "HIGH",
        "scheme_ids": ["atal_pension_yojana", "pmjjby"],
        "description": (
            "APY has enrollment age limit 'between 18 and 40 years'. "
            "PMJJBY has enrollment age limit 'between 18 and 50 years'. "
            "At exactly age 40: "
            "APY uses operator 'between' with value [18, 40] — inclusive. "
            "This means age 40 IS eligible for APY by our engine's implementation. "
            "However, the APY guidelines say 'any citizen in the age group of 18-40 years' — "
            "which is ambiguous: does '40 years' mean 'has not yet turned 41' or "
            "'is exactly in the 40th year of life' (i.e., 39 completed years)? "
            "If the guidelines mean 'below 40' (exclusive upper bound), our 'between' "
            "operator with inclusive bounds gives a wrong answer for someone who is "
            "exactly 40 years old. "
            "Additionally, at age 40, a person is simultaneously eligible for APY "
            "(if our inclusive reading is correct) and PMJJBY. The system must not "
            "treat these as mutually exclusive — they are independent schemes."
        ),
        "naive_system_error": (
            "Either: (a) wrong operator (less_than vs less_than_or_equal) means "
            "age-40 person is incorrectly excluded from APY, or "
            "(b) shows both APY and PMJJBY but marks them as conflicting."
        ),
        "correct_behavior": (
            "Show both APY and PMJJBY for age-40 person. "
            "Add flag: 'APY eligibility at exactly age 40 is ambiguous in guidelines. "
            "Verify with your bank/PFRDA before applying.'"
        ),
        "real_world_impact": (
            "A 40-year-old who is incorrectly excluded from APY misses the last "
            "opportunity to enroll in a guaranteed pension scheme. Cannot enroll at 41."
        ),
        "resolution_status": "unresolved_requires_pfrda_clarification",
        "can_claim_both": True,
        "mutual_exclusion_enforced_by": None,
        "boundary_case": "age == 40",
        "recommended_fix": (
            "Contact PFRDA to clarify whether '18-40 years' means age < 40 or age <= 40. "
            "Until clarified: use inclusive bound (age <= 40) but add LOW confidence flag "
            "for all evaluations where age == 40."
        ),
    },

    {
        "ambiguity_id": "CSO_004",
        "type": "cross_scheme_overlap",
        "severity": "LOW",
        "scheme_ids": ["mgnrega", "pm_kisan"],
        "description": (
            "A rural landowning farmer family can simultaneously claim both MGNREGA wages "
            "and PM Kisan cash transfers. These schemes do not exclude each other. "
            "MGNREGA: any rural adult who wants unskilled work. "
            "PM Kisan: landowning farmer families. "
            "A small farmer who owns 0.5 hectares can work on MGNREGA projects during "
            "the off-season and receive PM Kisan installments. "
            "A naive system might flag this as a conflict ('already receiving agricultural "
            "support') or suppress one. There is no conflict — both should be shown."
        ),
        "naive_system_error": (
            "Suppresses MGNREGA for a user who is eligible for PM Kisan "
            "(treating agricultural support as a category-level exclusion) or "
            "vice versa. No such mutual exclusion exists in either scheme's guidelines."
        ),
        "correct_behavior": (
            "Show both as eligible with no conflict note. "
            "This is a known valid combination for small and marginal farmers."
        ),
        "real_world_impact": (
            "Suppressing MGNREGA for a PM Kisan farmer costs the household "
            "up to 100 days × ₹200-350/day = ₹20,000–₹35,000/year in missed wages."
        ),
        "resolution_status": "confirmed_no_conflict",
        "can_claim_both": True,
        "mutual_exclusion_enforced_by": None,
        "recommended_fix": "No fix needed. Confirm engine does not suppress either scheme.",
    },

    {
        "ambiguity_id": "CSO_005",
        "type": "cross_scheme_overlap",
        "severity": "MEDIUM",
        "scheme_ids": ["pmjjby", "pmsby"],
        "description": (
            "PMJJBY (life insurance, any cause of death) and PMSBY (accidental death/disability) "
            "are complementary and frequently confused. A person in age group 18-50 is eligible "
            "for BOTH simultaneously. Combined premium: ₹436 + ₹20 = ₹456/year for "
            "₹2L (accidental) + ₹2L (life) = ₹4L total cover. "
            "A naive system might: "
            "(a) show only one because they seem similar, or "
            "(b) show both but not explain they have DIFFERENT trigger conditions "
            "(accidental only vs any cause). "
            "The distinction matters: a person age 51-70 is eligible for PMSBY but NOT PMJJBY."
        ),
        "naive_system_error": (
            "Shows only one scheme, or conflates them as the same product, "
            "or fails to show PMSBY for ages 51-70 because it only searches "
            "for 'insurance schemes' and PMJJBY was already matched."
        ),
        "correct_behavior": (
            "Show both for ages 18-50. Show only PMSBY for ages 51-70. "
            "Add note: 'These are different products: PMJJBY covers any death (₹436/yr); "
            "PMSBY covers accidental death/disability only (₹20/yr). Both recommended.'"
        ),
        "real_world_impact": (
            "A 55-year-old shown only PMJJBY (for which they're ineligible) and not PMSBY "
            "gets zero insurance coverage instead of ₹2 lakh accident cover for ₹20/year."
        ),
        "resolution_status": "partially_mitigated",
        "can_claim_both": True,
        "mutual_exclusion_enforced_by": None,
        "recommended_fix": (
            "Add 'complementary_schemes' field. "
            "Add output note for users eligible for both: "
            "'Taking both PMJJBY + PMSBY provides ₹4L combined cover for ₹456/year total.'"
        ),
    },

    {
        "ambiguity_id": "CSO_006",
        "type": "cross_scheme_overlap",
        "severity": "HIGH",
        "scheme_ids": ["nfbs", "nsap_ignoaps"],
        "description": (
            "NFBS provides a one-time benefit when the PRIMARY BREADWINNER dies, aged 18-59. "
            "If the breadwinner was elderly (60+), they would have been IGNOAPS-eligible, not NFBS-eligible. "
            "The schemes are designed to be mutually exclusive by age of the deceased: "
            "NFBS: breadwinner dies at age 18-59. "
            "IGNOAPS: elderly person (60+) themselves receives pension. "
            "However, a household can receive BOTH over time: "
            "First, NFBS when the breadwinner (age 50) dies, then "
            "later, IGNOAPS for the surviving elderly spouse (now 65). "
            "A naive system might flag IGNOAPS as 'already received death benefit from this household' "
            "and suppress it. This would be wrong — IGNOAPS is for the surviving elder, not the deceased."
        ),
        "naive_system_error": (
            "After NFBS is marked in 'currently_enrolled_schemes', suppresses IGNOAPS "
            "for surviving elderly family member because household already received "
            "a death-related benefit. Wrong — different beneficiary, different scheme."
        ),
        "correct_behavior": (
            "NFBS and IGNOAPS are for different beneficiaries. Never suppress one based on the other. "
            "Check IGNOAPS eligibility for the surviving elderly person independently."
        ),
        "real_world_impact": (
            "Elderly widow, 67, whose husband died and family received NFBS, "
            "is incorrectly told she cannot receive IGNOAPS. "
            "Misses ₹200-2,000+/month pension for remainder of life."
        ),
        "resolution_status": "confirmed_no_conflict_requires_documentation",
        "can_claim_both": True,
        "mutual_exclusion_enforced_by": None,
        "recommended_fix": (
            "Ensure 'currently_enrolled_schemes' check in engine (if implemented) "
            "does NOT suppress IGNOAPS when NFBS is present. "
            "Document this explicitly in scheme metadata."
        ),
    },

    {
        "ambiguity_id": "CSO_007",
        "type": "cross_scheme_overlap",
        "severity": "MEDIUM",
        "scheme_ids": ["pmuy", "pmmvy", "janani_suraksha_yojana"],
        "description": (
            "All three schemes target women from low-income households. "
            "A pregnant woman who qualifies for PMUY (needs LPG connection) also "
            "qualifies for PMMVY and JSY simultaneously. "
            "These are not mutually exclusive — all three should be claimed. "
            "However, the prerequisite structure creates a sequencing trap: "
            "PMUY requires a bank account (PREREQ: Jan Dhan). "
            "PMMVY requires a bank account (PREREQ: Jan Dhan). "
            "JSY requires a bank account (PREREQ: Jan Dhan). "
            "If a pregnant woman has no bank account, ALL THREE are in prerequisite-blocked status "
            "simultaneously. The application sequence builder must handle this: "
            "'First: Jan Dhan account. Then simultaneously: PMUY + PMMVY registration + JSY ANC registration.'"
        ),
        "naive_system_error": (
            "Shows Jan Dhan → PMUY → PMMVY → JSY as a LINEAR sequence, "
            "suggesting the user must complete each before starting the next. "
            "In reality, PMMVY registration and JSY ANC registration should happen "
            "IMMEDIATELY during pregnancy — if the user waits until PMUY is completed "
            "before starting PMMVY registration, they may miss the LMP+150 days window "
            "for the first PMMVY installment."
        ),
        "correct_behavior": (
            "After Jan Dhan: PMUY, PMMVY, and JSY ANC registration should all be "
            "initiated simultaneously. The application sequence should show them as "
            "PARALLEL tasks, not sequential. "
            "PMMVY registration is time-sensitive (pregnancy window)."
        ),
        "real_world_impact": (
            "Missing the LMP+150 days PMMVY window means forfeiting the first "
            "installment of ₹1,000, even if later installments are claimed. "
            "This is a process failure caused by wrong sequencing, not wrong eligibility."
        ),
        "resolution_status": "unresolved_requires_parallel_sequencing",
        "can_claim_both": True,
        "mutual_exclusion_enforced_by": None,
        "recommended_fix": (
            "Add 'time_sensitive: True' and 'time_sensitivity_note' fields to scheme metadata. "
            "build_application_sequence() should flag time-sensitive schemes as URGENT "
            "and show them as parallel with prerequisites, not after them."
        ),
    },

]


# =============================================================================
# CATEGORY 3 — DEFINITIONAL AMBIGUITIES
# Terms used in guidelines that have no computable operational definition.
# =============================================================================

_DEFINITIONAL_AMBIGUITIES: list[dict[str, Any]] = [

    {
        "ambiguity_id": "DEF_001",
        "type": "definitional_ambiguity",
        "severity": "HIGH",
        "scheme_ids": ["pm_kisan"],
        "term": "cultivable land",
        "description": (
            "PM Kisan targets 'landholder farmer families' implying cultivable agricultural land. "
            "The operational guidelines do not define 'cultivable'. "
            "Disputed edge cases: "
            "(1) Fallow land: land that was cultivated but is currently resting. Cultivable or not? "
            "(2) Orchard/plantation land: technically agricultural but not 'cropped'. "
            "(3) Land under litigation: owned on paper, not cultivated due to dispute. "
            "(4) Land in tribal areas under various tenure systems: may not have formal records. "
            "(5) Waterlogged or degraded land: agriculturally classified but physically incultivable. "
            "The intake asks 'land_is_cultivable' as a boolean — the user self-reports this. "
            "There is no objective verification mechanism in the intake schema."
        ),
        "why_uncomputable": (
            "No objective definition in scheme guidelines. "
            "Self-reported boolean cannot distinguish fallow from permanently unproductive land. "
            "Revenue department records use different classification systems across states."
        ),
        "schemes_affected_count": 1,
        "real_world_impact": (
            "An orchard owner who calls their land 'cultivable' (it is, by any reasonable definition) "
            "may or may not qualify — the scheme FAQ does not address this. "
            "Similarly, a fallow-land owner who reports 'land_is_cultivable = False' "
            "because they're not currently farming would be wrongly excluded."
        ),
        "resolution_status": "unresolvable_without_official_clarification",
        "recommended_fix": (
            "Replace boolean 'land_is_cultivable' with: "
            "'land_use_type': ['kharif_crop', 'rabi_crop', 'orchard_plantation', "
            "'fallow', 'degraded_wasteland', 'under_litigation', 'other']. "
            "Treat all except 'degraded_wasteland' and 'under_litigation' as cultivable. "
            "Seek MoA clarification on orchards and fallow land."
        ),
    },

    {
        "ambiguity_id": "DEF_002",
        "type": "definitional_ambiguity",
        "severity": "HIGH",
        "scheme_ids": ["nfbs"],
        "term": "primary breadwinner",
        "description": (
            "NFBS requires the deceased to have been the 'primary breadwinner' of the household. "
            "The NSAP guidelines do not define this term. "
            "Edge cases: "
            "(1) Household where both husband (age 45) and wife (age 40) earn income. "
            "    Husband dies. Is he the primary breadwinner if wife earned more? "
            "(2) Joint family where the grandfather (age 62) owned land and the son (age 35) "
            "    did daily wage work. Son dies. Is the son the primary breadwinner? "
            "(3) Household where the primary earner was an informal daily wage laborer "
            "    with no proof of income. How is 'primary' determined? "
            "(4) Female-headed households where the woman was the primary earner — "
            "    historically under-recognized as 'breadwinners' in practice."
        ),
        "why_uncomputable": (
            "No legal definition in NSAP guidelines. "
            "Determination left to district/block welfare officers (discretionary). "
            "Income proof may not exist for informal workers. "
            "The intake field 'primary_breadwinner_died' is a boolean self-report "
            "that cannot be independently verified."
        ),
        "schemes_affected_count": 1,
        "real_world_impact": (
            "A family where both parents worked may have their NFBS claim rejected "
            "because the officer determines the surviving spouse was 'also an earner'. "
            "The system will show NFBS as eligible but the application may be rejected "
            "at the district level on definitional grounds."
        ),
        "resolution_status": "unresolvable_definitional_gap_in_scheme",
        "recommended_fix": (
            "Add 'primary_breadwinner_note' to scheme output: "
            "'NFBS requires the deceased to have been the primary breadwinner. "
            "This is determined by the district welfare officer. "
            "Bring income proof, employment records, or sworn affidavit if possible.'"
        ),
    },

    {
        "ambiguity_id": "DEF_003",
        "type": "definitional_ambiguity",
        "severity": "MEDIUM",
        "scheme_ids": ["pm_svanidhi"],
        "term": "street vendor",
        "description": (
            "PM SVANidhi uses the Street Vendors Act 2014 definition: "
            "'a person who sells goods or offers services in a public place from a "
            "temporary built-up structure or by moving from place to place.' "
            "Disputed edge cases: "
            "(1) Home-based sellers who sell from their doorstep onto the street — "
            "    technically stationary vending but from private property. "
            "(2) E-commerce enabled street vendors who also sell online — hybrid model. "
            "(3) Seasonal vendors (e.g., sell only during festival season, 2-3 months/year). "
            "(4) Vendors in weekly haats (rural markets) — are these 'public places'? "
            "    Haat vendors are technically rural, covered by different rules. "
            "(5) Auto-rickshaw drivers who also sell goods from their vehicle — "
            "    vending or transport business?"
        ),
        "why_uncomputable": (
            "The definition requires physical observation of vending activity. "
            "The intake boolean 'is_street_vendor' is self-reported. "
            "The was_vending_before_march_24_2020 field requires memory and "
            "cannot be verified from intake data. "
            "ULBs have discretion in issuing vending certificates — "
            "the presence/absence of a certificate proxies but doesn't define vendor status."
        ),
        "schemes_affected_count": 1,
        "real_world_impact": (
            "A home-based seller (window seller) who thinks they qualify may be "
            "rejected at ULB level. A seasonal vendor who operated pre-2020 may "
            "not know they qualify. The system shows eligible but application fails."
        ),
        "resolution_status": "partially_mitigated_by_lor_provision",
        "recommended_fix": (
            "Add clarifying question flow: "
            "'Do you sell goods or services in a public place (market, roadside, etc.)? "
            "Were you doing this before March 24, 2020? "
            "Do you have a vending certificate? If not, your local ULB can issue a "
            "Letter of Recommendation — contact them at [helpline].'"
        ),
    },

    {
        "ambiguity_id": "DEF_004",
        "type": "definitional_ambiguity",
        "severity": "HIGH",
        "scheme_ids": [
            "nsap_ignoaps", "pmay_gramin", "pmuy", "nfbs",
            "janani_suraksha_yojana", "ab_pmjay"
        ],
        "term": "BPL household / Below Poverty Line",
        "description": (
            "Six of our 15 schemes use 'BPL' as an eligibility criterion. "
            "There are at least FOUR different BPL lists in operation simultaneously: "
            "(1) BPL Census 1997 — the original list, still used in some contexts. "
            "(2) BPL Census 2002 — updated list, used for most scheme targeting until ~2011. "
            "(3) SECC 2011 — the most recent national socioeconomic survey, "
            "    used for PMAY-G and AB-PMJAY. Not called 'BPL' but functionally similar. "
            "(4) State-issued BPL cards — states create and maintain their own BPL lists "
            "    using their own criteria. A family may be on the state BPL list but not "
            "    SECC 2011, or vice versa. "
            "When a scheme says 'BPL household', which list does it mean? "
            "This is not specified consistently across scheme guidelines. "
            "The intake collects 'has_bpl_card' and 'is_bpl_household' — "
            "these refer to the state-issued BPL card, not SECC 2011."
        ),
        "why_uncomputable": (
            "Four different lists, no national mapping between them. "
            "A family on State BPL list is not guaranteed to be on SECC 2011. "
            "A family on SECC 2011 may not have a State BPL card. "
            "The intake field 'is_bpl_household' cannot distinguish which list the user is on."
        ),
        "schemes_affected_count": 6,
        "real_world_impact": (
            "A family with a State BPL card but not on SECC 2011: "
            "Eligible for NSAP IGNOAPS (state BPL list used) "
            "NOT eligible for AB-PMJAY (SECC 2011 used) "
            "NOT eligible for PMAY-G (SECC/Awaas Plus used). "
            "The engine treats all BPL criteria as equivalent — false positives for PMAY-G."
        ),
        "resolution_status": "fundamental_data_infrastructure_gap",
        "recommended_fix": (
            "Separate BPL concepts in intake schema: "
            "'has_state_bpl_card': bool — physical card issued by state. "
            "'secc_listed': bool — SECC 2011 database (requires lookup). "
            "Map each scheme to the correct BPL source: "
            "NSAP → has_state_bpl_card. "
            "PMAY-G → secc_listed (database lookup). "
            "AB-PMJAY → secc_listed (database lookup). "
            "JSY-HPS → has_state_bpl_card OR caste_category in [sc, st]."
        ),
    },

    {
        "ambiguity_id": "DEF_005",
        "type": "definitional_ambiguity",
        "severity": "HIGH",
        "scheme_ids": ["pm_kisan", "nsap_ignoaps", "nfbs"],
        "term": "family / household",
        "description": (
            "Different schemes define the family/household unit differently. "
            "PM Kisan: 'a family comprising of husband, wife and minor children' "
            "— meaning a joint family has multiple eligible PM Kisan units. "
            "NSAP IGNOAPS: individual elderly person — scheme is individual, not household. "
            "NFBS: 'household' — but the definition of household for NSAP is not specified. "
            "The intake schema collects one profile per 'user' and assumes "
            "one household = one profile. This fails for PM Kisan where a 3-generation "
            "joint family should be evaluated as 2-3 separate PM Kisan eligible units "
            "if land is partitioned across members."
        ),
        "why_uncomputable": (
            "The system cannot determine household structure from a flat profile dict. "
            "It cannot know whether land is jointly registered or partitioned. "
            "It cannot identify whether multiple family units share one kitchen "
            "(joint family) vs separate kitchens (nuclear units within a property)."
        ),
        "schemes_affected_count": 3,
        "real_world_impact": (
            "A joint family where grandfather, father, and uncle each own separate land plots "
            "may think they can submit only one PM Kisan application. "
            "In fact, each nuclear unit (husband+wife+minor children) is a separate eligible entity. "
            "The family is leaving 2× ₹6,000 = ₹12,000/year on the table."
        ),
        "resolution_status": "architectural_limitation_requires_multi_profile",
        "recommended_fix": (
            "Add to PM Kisan output note: "
            "'If your household has multiple married couples with separate land holdings, "
            "each couple-unit may be eligible separately. "
            "Check with your Gram Panchayat for guidance on separate registration.' "
            "Long-term: support multi-member household profiles."
        ),
    },

    {
        "ambiguity_id": "DEF_006",
        "type": "definitional_ambiguity",
        "severity": "LOW",
        "scheme_ids": ["mgnrega"],
        "term": "unskilled manual work willingness",
        "description": (
            "MGNREGA requires that adult household members seek 'unskilled manual work'. "
            "The intake captures this as 'is_willing_to_do_unskilled_manual_work: bool'. "
            "In practice, MGNREGA has evolved to include semi-skilled work "
            "(construction supervision, data entry for scheme monitoring, etc.). "
            "Additionally, persons with disabilities may not be able to do standard "
            "unskilled manual work but are entitled to accommodation and alternative "
            "work assignments under MGNREGA provisions. "
            "The boolean field does not capture: "
            "(a) Type of unskilled work the person can do. "
            "(b) Disability accommodation provisions."
        ),
        "why_uncomputable": (
            "MGNREGA work types vary by state and project. "
            "Disability accommodations are not captured in intake. "
            "Boolean oversimplifies a situational assessment."
        ),
        "schemes_affected_count": 1,
        "real_world_impact": (
            "A person with locomotor disability may say 'False' to unskilled manual work "
            "(cannot do heavy construction) but would be eligible for MGNREGA's "
            "disability-accommodated work assignments. System incorrectly excludes them."
        ),
        "resolution_status": "low_priority_improvement",
        "recommended_fix": (
            "Add 'disability_work_accommodation_needed' flag. "
            "If disability_status != 'none' AND disability_percentage >= 40: "
            "show MGNREGA with note about disability accommodation provisions."
        ),
    },

]


# =============================================================================
# CATEGORY 4 — STALE DATA RISKS
# Rules referencing time-sensitive data that may already be outdated.
# =============================================================================

_STALE_DATA_RISKS: list[dict[str, Any]] = [

    {
        "ambiguity_id": "STALE_001",
        "type": "stale_data_risk",
        "severity": "HIGH",
        "scheme_ids": ["ab_pmjay"],
        "data_element": "SECC 2011 database",
        "description": (
            "The Socio-Economic Caste Census 2011 is the foundational eligibility database "
            "for AB-PMJAY. As of 2024, this data is 13 years old. "
            "Population churn since 2011: "
            "(1) Deaths: people listed in SECC 2011 who have since died remain on the list. "
            "    Their family members try to claim benefits in deceased person's name — fraud risk. "
            "(2) New families: approximately 25-30 million new households formed since 2011 "
            "    (marriages creating new units, joint families splitting) are not in SECC. "
            "(3) Economic mobility: families that were deprived in 2011 and are now "
            "    middle-class are still listed. "
            "(4) New poverty: families that were not deprived in 2011 but are now poor "
            "    (due to illness, disability, loss of employment) are not listed. "
            "No update mechanism exists at the central level. "
            "SECC 2.0 has been discussed but not conducted as of verification date."
        ),
        "staleness_age": "13 years (2011 → 2024)",
        "update_frequency": "Never updated since 2011",
        "estimated_affected_households": "25-30 million new households not covered",
        "real_world_impact": (
            "Families who became poor after 2011 (medical bankruptcy, disability, "
            "natural disaster) cannot access AB-PMJAY's ₹5 lakh health cover. "
            "This is a systemic exclusion, not a data error — but it means our "
            "'verify_manually' output for AB-PMJAY may still result in rejection "
            "for genuinely poor families not in SECC."
        ),
        "resolution_status": "systemic_policy_gap_not_fixable_at_engine_level",
        "recommended_fix": (
            "Add to AB-PMJAY verify_manually output: "
            "'If you are not listed in SECC 2011, check your STATE's AB-PMJAY "
            "expansion scheme — many states have added income-based beneficiaries "
            "beyond the SECC list. [State portal link].'"
        ),
        "last_verified_date": "2024-01-01",
        "next_review_date": "2024-06-01",
    },

    {
        "ambiguity_id": "STALE_002",
        "type": "stale_data_risk",
        "severity": "HIGH",
        "scheme_ids": ["pmjjby"],
        "data_element": "Annual premium amount ₹436",
        "description": (
            "PMJJBY premium was revised from ₹330 to ₹436 per year in June 2022. "
            "This is the most recent known value (as of verification date January 2024). "
            "The premium is set by the government and can be revised in any financial year. "
            "If revised again, our stored value of ₹436 becomes incorrect. "
            "This affects the benefit_description and premium_amount_inr fields. "
            "Risk: user is told the premium is ₹436, auto-debit is set up for ₹436, "
            "but the actual debit is a different amount, causing account discrepancy."
        ),
        "staleness_age": "0–18 months (June 2022 → January 2024)",
        "update_frequency": "Can change annually with government notification",
        "real_world_impact": (
            "User sets aside exactly ₹436 in their bank account on May 31 each year. "
            "If premium changed to ₹500, auto-debit fails, policy lapses, "
            "family has no life insurance. Discovery only at death claim stage."
        ),
        "resolution_status": "actively_managed_requires_annual_check",
        "recommended_fix": (
            "Add to PMJJBY output: 'Premium amount ₹436/year — verify current amount at "
            "jansuraksha.gov.in before enrollment as government may revise annually.' "
            "Add to deployment checklist: verify PMJJBY premium at start of each financial year."
        ),
        "last_verified_date": "2024-01-01",
        "next_review_date": "2024-04-01",
    },

    {
        "ambiguity_id": "STALE_003",
        "type": "stale_data_risk",
        "severity": "MEDIUM",
        "scheme_ids": ["mgnrega"],
        "data_element": "State-specific wage rates",
        "description": (
            "MGNREGA wage rates are notified state-by-state, annually, by the Ministry of Rural "
            "Development. As of financial year 2023-24, rates ranged from approximately "
            "₹221/day (Chhattisgarh/MP at lower end) to ₹374/day (Haryana). "
            "These change every April 1 with the new financial year notification. "
            "Our database does not store specific wage rates — it only says "
            "'₹200–₹350/day approximately'. "
            "If a user wants to know their exact potential earnings (100 days × state rate), "
            "we cannot tell them accurately. "
            "Additionally, drought/disaster special provisions can temporarily extend "
            "the 100-day guarantee in specific years for specific districts."
        ),
        "staleness_age": "Up to 12 months",
        "update_frequency": "Annual (April 1 each year)",
        "real_world_impact": (
            "User underestimates MGNREGA earnings (if our range is below actual) "
            "or overestimates (if our range is above actual). "
            "This affects financial planning decisions, not eligibility. "
            "Severity: MEDIUM (financial estimate wrong, not eligibility wrong)."
        ),
        "resolution_status": "low_risk_acceptable_approximation",
        "recommended_fix": (
            "Store wage rates as a state-keyed lookup table, updated annually. "
            "Or: add to MGNREGA output: 'Current wage rate for [state]: verify at nrega.nic.in. "
            "Rates are revised every April.'"
        ),
        "last_verified_date": "2024-01-01",
        "next_review_date": "2024-04-01",
    },

    {
        "ambiguity_id": "STALE_004",
        "type": "stale_data_risk",
        "severity": "MEDIUM",
        "scheme_ids": ["atal_pension_yojana"],
        "data_element": "Income taxpayer exclusion rule (October 2022 amendment)",
        "description": (
            "The exclusion of income taxpayers from APY was added in October 2022. "
            "This is a relatively recent amendment that many existing scheme descriptions "
            "do not include. Our database correctly captures this (rule B1, HIGH confidence). "
            "However, the risk is in the opposite direction: this rule COULD be reversed "
            "or modified in future amendments. "
            "Additionally, the definition of 'income taxpayer' for APY purposes — "
            "does it mean 'has PAN and has filed a return' or 'has taxable income above threshold' — "
            "is not precisely specified in the PFRDA circular. "
            "A person with PAN who filed a nil return (income below taxable limit) "
            "may not be a 'taxpayer' in the economic sense but technically filed a return."
        ),
        "staleness_age": "15 months (October 2022 → January 2024)",
        "update_frequency": "Can change with PFRDA circular",
        "real_world_impact": (
            "A person with PAN who files a nil return is shown as APY-ineligible. "
            "If 'income taxpayer' means 'pays tax' (not 'files return'), they are actually eligible. "
            "False negative for a small but real population of low-income PAN holders."
        ),
        "resolution_status": "requires_pfrda_clarification",
        "recommended_fix": (
            "Interpret 'income taxpayer' strictly as 'paid income tax in last assessment year' "
            "(consistent with PM Kisan's language). "
            "Add output note: 'If you have PAN but income is below taxable limit and you "
            "paid zero tax, verify APY eligibility directly with your bank or PFRDA helpline.'"
        ),
        "last_verified_date": "2024-01-01",
        "next_review_date": "2024-07-01",
    },

    {
        "ambiguity_id": "STALE_005",
        "type": "stale_data_risk",
        "severity": "MEDIUM",
        "scheme_ids": ["pmay_urban"],
        "data_element": "Entire PMAY-U scheme structure",
        "description": (
            "PMAY-U 1.0 ended (for new applications) with its March 2022 deadline. "
            "PMAY-U 2.0 was announced in Union Budget 2024. "
            "As of our verification date, PMAY-U 2.0 operational guidelines have NOT been "
            "released. Our entire PMAY-U rule set reflects the discontinued PMAY-U 1.0 structure. "
            "The CLSS vertical (Credit Linked Subsidy Scheme) is definitively discontinued. "
            "The BLC (Beneficiary-Led Construction) and AHP verticals may continue under 2.0 "
            "but with revised parameters. "
            "Income categories (EWS, LIG, MIG) and their ceilings may be revised. "
            "Our current income ceiling figures (₹3L, ₹6L, ₹12L, ₹18L) are based on "
            "PMAY-U 1.0 which is no longer accepting new applications."
        ),
        "staleness_age": "Variable (PMAY-U 1.0 closed March 2022; 2.0 not yet released)",
        "update_frequency": "One-time revision when PMAY-U 2.0 guidelines released",
        "real_world_impact": (
            "Showing PMAY-U as 'eligible' for users who apply today is misleading — "
            "new applications under PMAY-U 1.0 are not being accepted. "
            "PMAY-U 2.0 may have different eligibility criteria. "
            "Users shown as eligible may find no active scheme to apply to."
        ),
        "resolution_status": "critical_scheme_in_transition_flag_immediately",
        "recommended_fix": (
            "Add 'scheme_status': 'in_transition' field to pmay_urban. "
            "Always show warning in output: 'PMAY-U 1.0 has concluded. "
            "PMAY-U 2.0 operational guidelines are pending. "
            "Monitor pmaymis.gov.in for updates before applying.'"
        ),
        "last_verified_date": "2024-01-01",
        "next_review_date": "2024-03-01",
    },

    {
        "ambiguity_id": "STALE_006",
        "type": "stale_data_risk",
        "severity": "LOW",
        "scheme_ids": ["pm_kisan"],
        "data_element": "Annual benefit amount ₹6,000",
        "description": (
            "PM Kisan benefit of ₹6,000/year (₹2,000 per installment × 3) has been "
            "unchanged since the scheme's launch in February 2019. "
            "Over five years, this represents significant real-value erosion due to inflation. "
            "There have been repeated political discussions about increasing the amount, "
            "particularly before elections. "
            "Risk: the amount could be revised upward (beneficial for users) or "
            "an 'enhanced PM Kisan' for specific categories could be introduced. "
            "Our database would show the old amount."
        ),
        "staleness_age": "5 years (2019 → 2024) without revision",
        "update_frequency": "Could change with any Union Budget announcement",
        "real_world_impact": (
            "If amount increases, our output understates the benefit — lower severity. "
            "User gets more than expected; positive surprise. "
            "Low severity compared to eligibility errors."
        ),
        "resolution_status": "low_risk_monitor_annually",
        "recommended_fix": (
            "Verify benefit_amount_inr at start of each financial year. "
            "Add to deployment checklist."
        ),
        "last_verified_date": "2024-01-01",
        "next_review_date": "2024-02-01",
    },

    {
        "ambiguity_id": "STALE_007",
        "type": "stale_data_risk",
        "severity": "MEDIUM",
        "scheme_ids": ["pmmvy"],
        "data_element": "PMMVY 2.0 second-child-girl amendment (November 2022)",
        "description": (
            "PMMVY was amended in November 2022 to add ₹6,000 benefit for second child "
            "if the second child is a girl. This amendment is captured in our database "
            "at MEDIUM confidence. "
            "Three specific staleness risks: "
            "(1) The ₹6,000 amount for second girl may be revised. "
            "(2) State implementation of the 2022 amendment is not uniform — "
            "    some states have not operationalized it through Poshan Tracker. "
            "(3) The definition of 'girl child' for this purpose (registered sex at birth "
            "    vs other possibilities) is not specified in the amendment. "
            "Additionally, the 2022 amendment details are based on WCD ministry press release "
            "information, not a verified copy of the amendment notification. "
            "This is explicitly LOW confidence territory."
        ),
        "staleness_age": "14 months (November 2022 → January 2024)",
        "update_frequency": "Could change with further WCD ministry notifications",
        "real_world_impact": (
            "A woman pregnant with her second girl child who applies for ₹6,000 "
            "may find the scheme not implemented in her state's Poshan Tracker, "
            "or may receive ₹5,000 (old amount) instead of ₹6,000 (new amount). "
            "False expectation set by our database."
        ),
        "resolution_status": "requires_immediate_verification",
        "recommended_fix": (
            "Mark PMMVY 2.0 second-child-girl benefit as LOW confidence in output. "
            "Add note: 'The ₹6,000 benefit for second girl child was announced in "
            "November 2022. Verify availability in your state at pmmvy.wcd.gov.in "
            "or your local Anganwadi Centre before relying on this amount.'"
        ),
        "last_verified_date": "2024-01-01",
        "next_review_date": "2024-02-01",
    },

    {
        "ambiguity_id": "STALE_008",
        "type": "stale_data_risk",
        "severity": "LOW",
        "scheme_ids": ["sukanya_samriddhi"],
        "data_element": "Interest rate ~8.2% per annum",
        "description": (
            "SSY interest rate is revised quarterly by the Ministry of Finance. "
            "Our database explicitly does not store a specific rate value and directs "
            "users to the official source. "
            "This is correctly handled — but the benefit_description mentions '~8.2% p.a. "
            "as of Jan 2024' which will become stale within 90 days if the rate is revised. "
            "The tilde (~) and date qualifier help but the specific number is still misleading "
            "if shown to users 6 months after our verification date."
        ),
        "staleness_age": "0–90 days maximum (revised quarterly)",
        "update_frequency": "Quarterly (January, April, July, October)",
        "real_world_impact": (
            "Low — user may expect 8.2% and get 8.0% or 8.4%. "
            "No eligibility impact. Financial planning impact only."
        ),
        "resolution_status": "low_risk_correctly_handled",
        "recommended_fix": (
            "Remove specific rate percentage from benefit_description entirely. "
            "Replace with: 'High interest rate (revised quarterly by MoF — "
            "check current rate at indiapost.gov.in).'"
        ),
        "last_verified_date": "2024-01-01",
        "next_review_date": "2024-04-01",
    },

]


# =============================================================================
# MASTER AMBIGUITY MAP
# =============================================================================

AMBIGUITY_MAP: dict[str, list[dict]] = {
    "internal_contradictions":  _INTERNAL_CONTRADICTIONS,
    "cross_scheme_overlaps":    _CROSS_SCHEME_OVERLAPS,
    "definitional_ambiguities": _DEFINITIONAL_AMBIGUITIES,
    "stale_data_risks":         _STALE_DATA_RISKS,
}


# =============================================================================
# SUMMARY COMPUTATION
# =============================================================================

def _compute_summary() -> dict:
    """
    Compute AMBIGUITY_SUMMARY dynamically from AMBIGUITY_MAP contents.
    Dynamic computation ensures summary stays accurate as ambiguities are added.
    """
    all_items: list[dict] = []
    for category_items in AMBIGUITY_MAP.values():
        all_items.extend(category_items)

    total = len(all_items)
    high   = sum(1 for i in all_items if i.get("severity") == "HIGH")
    medium = sum(1 for i in all_items if i.get("severity") == "MEDIUM")
    low    = sum(1 for i in all_items if i.get("severity") == "LOW")

    # Count ambiguities per scheme_id
    scheme_counts: dict[str, int] = {}
    all_affected_scheme_ids: set[str] = set()

    for item in all_items:
        # scheme_ids can be a list or a single string (scheme_id key)
        affected = item.get("scheme_ids", [])
        if isinstance(affected, str):
            affected = [affected]
        if not affected:
            # Some items use "scheme_id" (singular) — internal contradictions
            sid = item.get("scheme_id")
            if sid:
                affected = [sid]
        for sid in affected:
            scheme_counts[sid] = scheme_counts.get(sid, 0) + 1
            all_affected_scheme_ids.add(sid)

    # All known scheme IDs (hardcoded — matches schemes_database.py)
    all_scheme_ids = {
        "pm_kisan", "mgnrega", "ab_pmjay", "pmay_gramin", "pmay_urban",
        "pmuy", "pmmvy", "sukanya_samriddhi", "nsap_ignoaps",
        "atal_pension_yojana", "pmjjby", "pmsby", "nfbs",
        "pm_svanidhi", "janani_suraksha_yojana",
    }
    schemes_with_zero = sorted(all_scheme_ids - all_affected_scheme_ids)

    most_ambiguous = max(scheme_counts, key=scheme_counts.get) if scheme_counts else "none"
    most_ambiguous_count = scheme_counts.get(most_ambiguous, 0)

    return {
        "total_ambiguities":               total,
        "high_severity":                   high,
        "medium_severity":                 medium,
        "low_severity":                    low,
        "by_category": {
            "internal_contradictions":  len(_INTERNAL_CONTRADICTIONS),
            "cross_scheme_overlaps":    len(_CROSS_SCHEME_OVERLAPS),
            "definitional_ambiguities": len(_DEFINITIONAL_AMBIGUITIES),
            "stale_data_risks":         len(_STALE_DATA_RISKS),
        },
        "schemes_with_zero_ambiguities":   schemes_with_zero,
        "most_ambiguous_scheme":           most_ambiguous,
        "most_ambiguous_scheme_count":     most_ambiguous_count,
        "scheme_ambiguity_counts":         dict(
            sorted(scheme_counts.items(), key=lambda kv: kv[1], reverse=True)
        ),
    }


AMBIGUITY_SUMMARY: dict = _compute_summary()


# =============================================================================
# PUBLIC API FUNCTIONS
# =============================================================================

def get_ambiguities_for_scheme(scheme_id: str) -> list[dict]:
    """
    Return all ambiguity entries that affect a given scheme_id.

    Searches across all four categories. An ambiguity item matches if:
    - Its 'scheme_id' key equals the given scheme_id (internal contradictions), OR
    - Its 'scheme_ids' list contains the given scheme_id (cross-scheme, definitional, stale).

    Parameters
    ----------
    scheme_id : str
        The scheme identifier (e.g., "pm_kisan", "ab_pmjay").

    Returns
    -------
    list of ambiguity dicts, sorted by severity (HIGH first).
    """
    results = []
    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

    for category_items in AMBIGUITY_MAP.values():
        for item in category_items:
            # Check singular scheme_id (used in internal_contradictions)
            if item.get("scheme_id") == scheme_id:
                results.append(item)
                continue
            # Check plural scheme_ids list
            affected = item.get("scheme_ids", [])
            if isinstance(affected, str):
                affected = [affected]
            if scheme_id in affected:
                results.append(item)

    # Sort: HIGH → MEDIUM → LOW, then by ambiguity_id for determinism
    results.sort(
        key=lambda x: (
            severity_order.get(x.get("severity", "LOW"), 2),
            x.get("ambiguity_id", "")
        )
    )
    return results


def get_high_severity_ambiguities() -> list[dict]:
    """
    Return all ambiguity entries with severity == 'HIGH'.

    These must be surfaced in every matching output that involves the
    affected schemes. A match result that ignores HIGH severity ambiguities
    is providing false confidence to the user.

    Design decision: HIGH severity ambiguities are those that could cause
    an incorrect eligibility determination (false positive or false negative)
    — not merely reduce confidence. They represent situations where our
    engine could actively mislead a user into wasting an application.

    Returns
    -------
    list of dicts, sorted by ambiguity_id for determinism.
    """
    all_items: list[dict] = []
    for category_items in AMBIGUITY_MAP.values():
        all_items.extend(category_items)

    high_items = [
        item for item in all_items
        if item.get("severity") == "HIGH"
    ]
    high_items.sort(key=lambda x: x.get("ambiguity_id", ""))
    return high_items


def get_ambiguities_by_category(category: str) -> list[dict]:
    """
    Return all ambiguities in a given category.

    Parameters
    ----------
    category : str
        One of: 'internal_contradictions', 'cross_scheme_overlaps',
                'definitional_ambiguities', 'stale_data_risks'
    """
    return AMBIGUITY_MAP.get(category, [])


def get_all_ambiguities_flat() -> list[dict]:
    """Return all ambiguities as a single flat list, sorted by severity then ID."""
    all_items: list[dict] = []
    for category_items in AMBIGUITY_MAP.values():
        all_items.extend(category_items)
    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    all_items.sort(
        key=lambda x: (
            severity_order.get(x.get("severity", "LOW"), 2),
            x.get("ambiguity_id", "")
        )
    )
    return all_items


# =============================================================================
# __main__ — FORMATTED AMBIGUITY REPORT
# =============================================================================

if __name__ == "__main__":

    try:
        from colorama import init as _cinit, Fore, Style
        _cinit(autoreset=True)
        _HAS_COLOR = True
    except ImportError:
        class _NC:
            def __getattr__(self, _):
                return ""
        Fore = Style = _NC()
        _HAS_COLOR = False

    def _color(text: str, fore: str) -> str:
        return f"{fore}{text}{Style.RESET_ALL}" if _HAS_COLOR else text

    def _sev_color(severity: str) -> str:
        return {
            "HIGH":   Fore.RED,
            "MEDIUM": Fore.YELLOW,
            "LOW":    Fore.CYAN,
        }.get(severity, "")

    DIV  = "─" * 72
    DDIV = "═" * 72

    print()
    print(_color("  KALAM — AMBIGUITY MAP REPORT", Fore.CYAN))
    print(DDIV)

    # Summary
    s = AMBIGUITY_SUMMARY
    print(f"  Total ambiguities documented: {s['total_ambiguities']}")
    print(
        f"  By severity: "
        f"{_color(str(s['high_severity']) + ' HIGH', Fore.RED)}  |  "
        f"{_color(str(s['medium_severity']) + ' MEDIUM', Fore.YELLOW)}  |  "
        f"{_color(str(s['low_severity']) + ' LOW', Fore.CYAN)}"
    )
    print(f"  By category:")
    for cat, count in s["by_category"].items():
        print(f"    {cat:<35} {count}")
    print(f"  Most ambiguous scheme: {s['most_ambiguous_scheme']} "
          f"({s['most_ambiguous_scheme_count']} ambiguities)")
    if s["schemes_with_zero_ambiguities"]:
        print(f"  Schemes with zero ambiguities: "
              f"{', '.join(s['schemes_with_zero_ambiguities'])}")
    else:
        print(_color("  ⚠ All schemes have at least one ambiguity.", Fore.YELLOW))

    # Print each category
    category_headers = {
        "internal_contradictions":  "CATEGORY 1 — INTERNAL CONTRADICTIONS",
        "cross_scheme_overlaps":    "CATEGORY 2 — CROSS-SCHEME OVERLAPS",
        "definitional_ambiguities": "CATEGORY 3 — DEFINITIONAL AMBIGUITIES",
        "stale_data_risks":         "CATEGORY 4 — STALE DATA RISKS",
    }

    for category_key, header in category_headers.items():
        items = AMBIGUITY_MAP[category_key]
        print()
        print(DDIV)
        print(_color(f"  {header}", Fore.CYAN))
        print(DDIV)

        for item in items:
            sev     = item.get("severity", "?")
            amb_id  = item.get("ambiguity_id", "?")
            schemes = item.get("scheme_ids") or ([item["scheme_id"]] if "scheme_id" in item else [])

            print()
            print(
                _color(f"  [{amb_id}] ", Fore.WHITE)
                + _color(f"[{sev}]", _sev_color(sev))
                + f" — Schemes: {', '.join(schemes) if schemes else 'see description'}"
            )
            print(DIV)

            # Print term for definitional ambiguities
            if "term" in item:
                print(f"  Term: '{item['term']}'")

            # Wrap description to 70 chars
            desc = item.get("description", "")
            words = desc.split()
            line = "  "
            for word in words:
                if len(line) + len(word) + 1 > 72:
                    print(line)
                    line = "    " + word + " "
                else:
                    line += word + " "
            if line.strip():
                print(line)

            # Impact
            impact = item.get("real_world_impact", "")
            if impact:
                print(f"  Impact: {impact[:120]}{'...' if len(impact) > 120 else ''}")

            # Status
            status = item.get("resolution_status", "unknown")
            status_color = Fore.GREEN if "resolved" in status else Fore.RED
            print(f"  Status: {_color(status, status_color)}")

    # HIGH severity summary at end
    print()
    print(DDIV)
    print(_color("  HIGH SEVERITY AMBIGUITIES — MUST FLAG IN ALL MATCHING OUTPUTS", Fore.RED))
    print(DDIV)
    for item in get_high_severity_ambiguities():
        amb_id  = item.get("ambiguity_id", "?")
        schemes = item.get("scheme_ids") or ([item.get("scheme_id", "?")])
        print(
            f"  {_color(amb_id, Fore.RED)} — "
            f"{', '.join(str(s) for s in schemes)}: "
            f"{item.get('description', '')[:80]}..."
        )

    print()
    print(DDIV)
    print()