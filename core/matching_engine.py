# =============================================================================
# KALAM — Welfare Scheme Matching Engine
# matching_engine.py
#
# Install dependencies:
#   pip install colorama
#
# Usage:
#   python matching_engine.py          # runs built-in test profiles
#   import matching_engine as kalam    # use match_schemes() in your app
#
# Architecture decisions encoded here:
#   1. Rule evaluator never assumes defaults for missing fields — fails loudly
#   2. Exclusions are evaluated FIRST and short-circuit inclusion evaluation
#   3. Confidence is a ceiling system — lowest rule caps the score
#   4. database_membership schemes are never given yes/no — always "verify"
#   5. Document gaps are reported separately from eligibility gaps
#   6. Application sequence is topologically sorted on prerequisites
#
# This file depends on: schemes_database.py (SCHEMES, CONFIDENCE_AUDIT)
# =============================================================================

from __future__ import annotations

import sys
import traceback
from typing import Any

# ---------------------------------------------------------------------------
# Colorama — graceful fallback if not installed
# ---------------------------------------------------------------------------
try:
    from colorama import init as _colorama_init, Fore, Style
    _colorama_init(autoreset=True)
    _COLOR_AVAILABLE = True
except ImportError:
    # Define no-op color stubs so the rest of the code runs identically
    # without colorama installed. Every Fore.X and Style.X becomes "".
    class _NoColor:
        def __getattr__(self, _: str) -> str:
            return ""
    Fore = _NoColor()
    Style = _NoColor()
    _COLOR_AVAILABLE = False
    print(
        "WARNING: colorama not installed. Output will be uncolored.\n"
        "         Install with: pip install colorama",
        file=sys.stderr,
    )

# ---------------------------------------------------------------------------
# Import scheme database
# ---------------------------------------------------------------------------
try:
    from schemes_database import SCHEMES, CONFIDENCE_AUDIT, DATABASE_VALID
except ImportError as exc:
    print(
        f"FATAL: Cannot import schemes_database.py — {exc}\n"
        "       Ensure schemes_database.py is in the same directory.",
        file=sys.stderr,
    )
    sys.exit(1)

if not DATABASE_VALID:
    print(
        "WARNING: schemes_database.py failed its internal validation.\n"
        "         Results may be unreliable. Review CONFIDENCE_AUDIT before use.",
        file=sys.stderr,
    )

# ---------------------------------------------------------------------------
# Build a fast lookup of scheme_ids that contain LOW confidence rules.
# Used by calculate_confidence_score() to apply scheme-level caps.
# We derive this from CONFIDENCE_AUDIT rather than re-scanning SCHEMES,
# because CONFIDENCE_AUDIT is the human-verified record of what we know
# is uncertain — that's the authoritative source.
# ---------------------------------------------------------------------------
_LOW_CONFIDENCE_SCHEME_IDS: set[str] = {
    entry["scheme_id"]
    for entry in CONFIDENCE_AUDIT.get("low_confidence_fields", [])
}

# Similarly collect schemes flagged as needing immediate human review
_NEEDS_REVIEW_SCHEME_IDS: set[str] = {
    entry["scheme_id"]
    for entry in CONFIDENCE_AUDIT.get(
        "schemes_requiring_immediate_human_review_before_deploy", []
    )
}

# ---------------------------------------------------------------------------
# Operator implementations
# Keeping these as a dispatch table rather than a long if/elif chain makes
# adding new operators trivial and keeps evaluate_rule() readable.
# ---------------------------------------------------------------------------

def _op_equals(field_val: Any, rule_val: Any) -> bool:
    return field_val == rule_val

def _op_not_equals(field_val: Any, rule_val: Any) -> bool:
    return field_val != rule_val

def _op_gt(field_val: Any, rule_val: Any) -> bool:
    return field_val > rule_val

def _op_lt(field_val: Any, rule_val: Any) -> bool:
    return field_val < rule_val

def _op_gte(field_val: Any, rule_val: Any) -> bool:
    return field_val >= rule_val

def _op_lte(field_val: Any, rule_val: Any) -> bool:
    return field_val <= rule_val

def _op_in(field_val: Any, rule_val: Any) -> bool:
    return field_val in rule_val

def _op_not_in(field_val: Any, rule_val: Any) -> bool:
    return field_val not in rule_val

def _op_is_true(field_val: Any, _: Any) -> bool:
    return field_val is True

def _op_is_false(field_val: Any, _: Any) -> bool:
    return field_val is False

def _op_exists(field_val: Any, _: Any) -> bool:
    return field_val is not None

def _op_between(field_val: Any, rule_val: Any) -> bool:
    """
    rule_val must be a 2-element list [low, high] (both inclusive).
    e.g. age between [18, 40] means 18 <= age <= 40.
    """
    if not isinstance(rule_val, (list, tuple)) or len(rule_val) != 2:
        raise ValueError(
            f"Operator 'between' requires a 2-element list, got: {rule_val!r}"
        )
    return rule_val[0] <= field_val <= rule_val[1]

def _op_not_between(field_val: Any, rule_val: Any) -> bool:
    return not _op_between(field_val, rule_val)


_OPERATOR_DISPATCH: dict[str, Any] = {
    "equals":                 _op_equals,
    "not_equals":             _op_not_equals,
    "greater_than":           _op_gt,
    "less_than":              _op_lt,
    "greater_than_or_equal":  _op_gte,
    "less_than_or_equal":     _op_lte,
    "in":                     _op_in,
    "not_in":                 _op_not_in,
    "is_true":                _op_is_true,
    "is_false":               _op_is_false,
    "exists":                 _op_exists,
    "between":                _op_between,
    "not_between":            _op_not_between,
}


# =============================================================================
# SECTION 1 — THE RULE EVALUATOR
# =============================================================================

def evaluate_rule(rule: dict, user_profile: dict) -> dict:
    """
    Evaluate a single inclusion or exclusion rule against the user profile.

    Design decisions:
    -----------------
    1. NEVER assume a default value for a missing field.
       Missing data is information — it tells us the match is uncertain.
       Silently defaulting to False for 'owns_land' would wrongly exclude
       someone who simply didn't answer that question yet.

    2. Operator errors (e.g., 'between' given a non-list) are caught and
       returned as data_missing=True with a descriptive reason rather than
       crashing. The engine must never stop processing other schemes because
       one rule has a malformed spec.

    3. The returned dict is intentionally verbose. Downstream consumers
       (the confidence calculator, the output formatter, the audit log)
       all need different slices of this information. Returning everything
       once is cheaper than re-evaluating.

    Parameters
    ----------
    rule : dict
        A single rule object from scheme's inclusion_rules or exclusion_rules.
        Required keys: rule_id, field, operator, value, confidence, source_note
    user_profile : dict
        Flat dictionary of user attributes collected at intake.

    Returns
    -------
    dict with keys:
        rule_id        : str   — from the rule definition
        passed         : bool  — True if the rule condition is satisfied
        confidence     : str   — HIGH / MEDIUM / LOW (from rule definition,
                                 degraded to LOW if data is missing)
        reason         : str   — human-readable explanation of the outcome
        data_missing   : bool  — True if the required field was absent
        field_checked  : str   — name of the profile field evaluated
        value_found    : any   — what was in the user profile (None if missing)
        value_required : any   — what the rule expected
        source_note    : str   — citation from scheme guidelines
    """
    rule_id        = rule.get("rule_id", "UNKNOWN")
    field          = rule.get("field", "")
    operator       = rule.get("operator", "")
    required_val   = rule.get("value")          # None is a valid rule value for 'exists'
    confidence     = rule.get("confidence", "MEDIUM")
    source_note    = rule.get("source_note", "No source cited")
    critical_note  = rule.get("critical_note", "")

    # ------------------------------------------------------------------
    # Step 1: Check if the field exists in the user profile.
    # We explicitly distinguish "field absent" from "field is None" —
    # both result in data_missing=True but for different reasons.
    # ------------------------------------------------------------------
    field_present = field in user_profile
    field_val     = user_profile.get(field)  # Returns None if absent

    if not field_present or field_val is None and operator != "exists":
        # Special case: 'exists' operator is explicitly checking for None,
        # so a None value is valid input for it. All other operators
        # require a real value.
        if not field_present:
            missing_reason = (
                f"Field '{field}' was not provided in the user profile — "
                f"cannot evaluate rule {rule_id}. "
                f"Collect this field to improve match accuracy."
            )
        else:
            # Field key exists but value is None
            missing_reason = (
                f"Field '{field}' is present but has no value (None) — "
                f"rule {rule_id} cannot be evaluated. "
                f"Prompt user to answer this question."
            )

        return {
            "rule_id":        rule_id,
            "passed":         False,
            "confidence":     "LOW",   # always downgrade to LOW when data missing
            "reason":         missing_reason,
            "data_missing":   True,
            "field_checked":  field,
            "value_found":    field_val,
            "value_required": required_val,
            "source_note":    source_note,
            "critical_note":  critical_note,
        }

    # ------------------------------------------------------------------
    # Step 2: Dispatch to the operator function.
    # ------------------------------------------------------------------
    op_fn = _OPERATOR_DISPATCH.get(operator)

    if op_fn is None:
        # Unknown operator in the scheme database — schema error, not user error.
        return {
            "rule_id":        rule_id,
            "passed":         False,
            "confidence":     "LOW",
            "reason":         (
                f"SCHEMA ERROR: Unknown operator '{operator}' in rule {rule_id}. "
                f"This is a bug in schemes_database.py — report to maintainer."
            ),
            "data_missing":   True,   # treat as missing because we can't evaluate
            "field_checked":  field,
            "value_found":    field_val,
            "value_required": required_val,
            "source_note":    source_note,
            "critical_note":  critical_note,
        }

    # ------------------------------------------------------------------
    # Step 3: Execute the operator. Catch type errors gracefully.
    # e.g., comparing a string field with an int threshold.
    # ------------------------------------------------------------------
    try:
        passed = op_fn(field_val, required_val)
    except (TypeError, ValueError) as exc:
        return {
            "rule_id":        rule_id,
            "passed":         False,
            "confidence":     "LOW",
            "reason":         (
                f"TYPE ERROR evaluating rule {rule_id}: "
                f"cannot apply '{operator}' to value {field_val!r} "
                f"(expected something comparable to {required_val!r}). "
                f"Error: {exc}"
            ),
            "data_missing":   True,
            "field_checked":  field,
            "value_found":    field_val,
            "value_required": required_val,
            "source_note":    source_note,
            "critical_note":  critical_note,
        }

    # ------------------------------------------------------------------
    # Step 4: Build a human-readable reason string.
    # The reason should be useful to a caseworker, not just a developer.
    # ------------------------------------------------------------------
    if passed:
        reason = (
            f"✓ {field} = {field_val!r} satisfies '{operator}' {required_val!r}. "
            f"[{source_note}]"
        )
        if critical_note:
            reason += f" NOTE: {critical_note}"
    else:
        reason = (
            f"✗ {field} = {field_val!r} does NOT satisfy '{operator}' {required_val!r}. "
            f"[{source_note}]"
        )
        if critical_note:
            reason += f" CRITICAL: {critical_note}"

    return {
        "rule_id":        rule_id,
        "passed":         passed,
        "confidence":     confidence,
        "reason":         reason,
        "data_missing":   False,
        "field_checked":  field,
        "value_found":    field_val,
        "value_required": required_val,
        "source_note":    source_note,
        "critical_note":  critical_note,
    }


# =============================================================================
# SECTION 2 — CONFIDENCE CALCULATOR
# =============================================================================

def calculate_confidence_score(
    inclusion_results: list[dict],
    exclusion_results: list[dict],
    scheme: dict,
) -> tuple[float, list[str]]:
    """
    Compute a 0.0–1.0 confidence score and explain every cap applied.

    Design rationale:
    -----------------
    Confidence is a CEILING system, not an averaging system.
    The weakest link in the chain determines the ceiling.
    This mirrors how welfare eligibility actually works: one bad piece
    of data or one unverified rule contaminates the entire determination.

    We do NOT average confidence across rules because that would allow
    ten HIGH-confidence rules to 'dilute' one LOW-confidence rule that
    is actually critical (e.g., the income tax exclusion in PM-KISAN).

    Cap hierarchy (most restrictive wins):
        Exclusion triggered          → 0.0   (hard disqualification)
        LOW confidence rule          → 0.5   (ceiling, rule is unreliable)
        Data missing in any rule     → 0.6   (ceiling, incomplete information)
        MEDIUM confidence rule       → 0.75  (ceiling, rule needs verification)
        Scheme in _LOW_CONFIDENCE    → 0.65  (ceiling, scheme-level audit flag)
        Scheme in _NEEDS_REVIEW      → 0.5   (ceiling, requires human review)
        All clear                    → 1.0

    When multiple caps apply, the minimum is used.
    All applied caps are reported so users know exactly why confidence is low.

    Parameters
    ----------
    inclusion_results : list of rule evaluation dicts from evaluate_rule()
    exclusion_results : list of rule evaluation dicts from evaluate_rule()
    scheme            : the full scheme dict from SCHEMES

    Returns
    -------
    tuple of (score: float, caps_applied: list[str])
    """
    scheme_id   = scheme.get("scheme_id", "unknown")
    caps        : list[str] = []
    ceiling     : float = 1.0

    def _apply_cap(new_cap: float, reason: str) -> None:
        """Apply a ceiling cap, keeping track of all reasons."""
        nonlocal ceiling
        if new_cap < ceiling:
            ceiling = new_cap
            caps.append(f"Cap {new_cap:.2f}: {reason}")
        elif new_cap == ceiling and reason not in caps:
            # Same ceiling level but additional reason — record it
            caps.append(f"Cap {new_cap:.2f}: {reason}")

    # ------------------------------------------------------------------
    # Rule 1: Any exclusion triggered → immediate 0.0
    # We check exclusion_results for rules that PASSED (meaning the
    # exclusion condition is TRUE — the user IS excluded).
    # ------------------------------------------------------------------
    triggered_exclusions = [r for r in exclusion_results if r["passed"]]
    if triggered_exclusions:
        triggered_ids = [r["rule_id"] for r in triggered_exclusions]
        _apply_cap(
            0.0,
            f"Exclusion rule(s) triggered: {', '.join(triggered_ids)}. "
            f"User is disqualified regardless of inclusions."
        )
        # Short-circuit — nothing else matters
        return 0.0, caps

    # ------------------------------------------------------------------
    # Rule 2: Check inclusion results for quality issues
    # ------------------------------------------------------------------
    for result in inclusion_results:
        rule_confidence = result.get("confidence", "MEDIUM")
        is_missing      = result.get("data_missing", False)

        if is_missing:
            _apply_cap(
                0.60,
                f"Rule {result['rule_id']}: field '{result['field_checked']}' "
                f"was not provided. Match is uncertain."
            )
        elif rule_confidence == "LOW":
            _apply_cap(
                0.50,
                f"Rule {result['rule_id']}: LOW confidence — "
                f"rule may not reflect current scheme guidelines. "
                f"Source: {result.get('source_note', 'no citation')}"
            )
        elif rule_confidence == "MEDIUM":
            _apply_cap(
                0.75,
                f"Rule {result['rule_id']}: MEDIUM confidence — "
                f"rule derived from scheme description but not pinned to "
                f"exact guideline clause. Independent verification recommended."
            )
        # HIGH confidence rules with data present: no cap applied

    # ------------------------------------------------------------------
    # Rule 3: Scheme-level audit flags from CONFIDENCE_AUDIT
    # These are applied after rule-level caps because they represent
    # known issues with the entire scheme's rules in this database,
    # not just individual rule quality.
    # ------------------------------------------------------------------
    if scheme_id in _NEEDS_REVIEW_SCHEME_IDS:
        review_entries = [
            e for e in CONFIDENCE_AUDIT.get(
                "schemes_requiring_immediate_human_review_before_deploy", []
            )
            if e["scheme_id"] == scheme_id
        ]
        reason_text = (
            review_entries[0].get("reason", "Flagged for human review")
            if review_entries else "Flagged for human review before deployment"
        )
        _apply_cap(
            0.50,
            f"Scheme '{scheme_id}' is flagged for mandatory human review "
            f"in CONFIDENCE_AUDIT: {reason_text}"
        )
    elif scheme_id in _LOW_CONFIDENCE_SCHEME_IDS:
        _apply_cap(
            0.65,
            f"Scheme '{scheme_id}' has LOW confidence fields documented "
            f"in CONFIDENCE_AUDIT. Results should be verified against "
            f"current official guidelines."
        )

    # ------------------------------------------------------------------
    # Rule 4: If no inclusions passed at all (all failed for non-missing
    # reasons), score should be 0.0 — the person doesn't qualify.
    # This handles the case where no exclusion was triggered but the
    # person also doesn't meet inclusion criteria.
    # ------------------------------------------------------------------
    # Inclusions that failed due to actual rule failure (not missing data)
    hard_failed_inclusions = [
        r for r in inclusion_results
        if not r["passed"] and not r["data_missing"]
    ]
    all_inclusions_either_passed_or_missing = all(
        r["passed"] or r["data_missing"]
        for r in inclusion_results
    )

    if hard_failed_inclusions:
        # At least one inclusion failed definitively — not eligible
        failed_ids = [r["rule_id"] for r in hard_failed_inclusions]
        _apply_cap(
            0.0,
            f"Inclusion rule(s) definitively failed: {', '.join(failed_ids)}. "
            f"User does not meet required conditions."
        )
        return 0.0, caps

    # ------------------------------------------------------------------
    # Final score = current ceiling (all caps applied)
    # ------------------------------------------------------------------
    return ceiling, caps


# =============================================================================
# SECTION 3 — THE MAIN MATCHING FUNCTION
# =============================================================================

def match_schemes(user_profile: dict) -> dict:
    """
    Core matching engine: evaluate all schemes against a user profile.

    Design decisions:
    -----------------
    1. We process ALL schemes, even those that will clearly not match,
       so that the not_eligible list is populated and the user understands
       why they don't qualify for each one. Transparency over brevity.

    2. database_membership schemes are NEVER given a yes/no. They are
       always routed to verify_manually with instructions. This prevents
       the SECC-2011 false positive problem identified in our architecture
       analysis (AB-PMJAY).

    3. The output is structured for multiple consumers:
       - A mobile UI (fully_eligible with confidence)
       - A caseworker dashboard (partial with gap_analysis)
       - An audit log (all rule results in confidence_breakdown)

    4. Partial eligibility = passed some but not all inclusions,
       where the failures are due to missing data (not hard failures).
       Hard failures → not_eligible. Missing data → partially_eligible.
       This distinction matters: partial tells the user "provide this
       info"; not_eligible tells them "you don't qualify."

    Parameters
    ----------
    user_profile : dict
        Flat dictionary of user attributes. Missing keys are handled
        gracefully — they reduce confidence but don't crash the engine.

    Returns
    -------
    dict with keys: fully_eligible, partially_eligible, not_eligible,
                    verify_manually, data_gaps_summary, ambiguous_flags,
                    application_sequence
    """
    fully_eligible   : list[dict] = []
    partially_eligible: list[dict] = []
    not_eligible     : list[dict] = []
    verify_manually  : list[dict] = []
    ambiguous_flags  : list[str]  = []

    # Track which fields were missing across ALL schemes so we can
    # surface a consolidated data_gaps_summary at the end.
    # Maps field_name → list of scheme_ids that needed it.
    _data_gaps: dict[str, list[str]] = {}

    for scheme_id, scheme in SCHEMES.items():

        # Skip internal validation sentinel if present
        if scheme_id.startswith("_"):
            continue

        scheme_name = scheme.get("name", scheme_id)

        # ------------------------------------------------------------------
        # Handle database_membership schemes — we CANNOT evaluate rules
        # against user data because eligibility depends on a frozen 2011
        # government database. Presenting rule-based logic for these schemes
        # would be actively misleading.
        # ------------------------------------------------------------------
        if scheme.get("eligibility_type") == "database_membership":
            db_config = scheme.get("database_membership_config", {})
            verify_manually.append({
                "scheme_id":        scheme_id,
                "scheme_name":      scheme_name,
                "eligibility_type": "database_membership",
                "reason":           (
                    f"Eligibility is based on the "
                    f"{db_config.get('primary_database', 'government database')}, "
                    f"not on income or current asset rules. "
                    f"A rule-based match cannot give a reliable answer for this scheme."
                ),
                "how_to_verify":    db_config.get(
                    "verification_url",
                    "Check the official scheme portal for eligibility verification."
                ),
                "verification_url": scheme.get("application_url", ""),
                "database_warning": db_config.get("database_critical_warning", ""),
                "state_expansion_note": db_config.get("state_expansion_note", ""),
            })
            continue

        # ------------------------------------------------------------------
        # Hybrid schemes: evaluate rules BUT also flag database lookup.
        # The rule-based result is a necessary-but-not-sufficient condition.
        # ------------------------------------------------------------------
        is_hybrid = scheme.get("eligibility_type") == "hybrid"

        # ------------------------------------------------------------------
        # Collect ambiguous rules for this scheme into the global flag list.
        # We do this before rule evaluation so even schemes that ultimately
        # fail eligibility still surface their ambiguity warnings.
        # ------------------------------------------------------------------
        for amb in scheme.get("ambiguous_rules", []):
            flag_text = (
                f"[{scheme_id}] Rule {amb.get('rule_id', '?')}: "
                f"{amb.get('description', 'Ambiguous condition')} "
                f"— System response: {amb.get('system_response', 'unknown')}"
            )
            if flag_text not in ambiguous_flags:
                ambiguous_flags.append(flag_text)

        # ------------------------------------------------------------------
        # STEP A: Evaluate EXCLUSION rules first.
        # Any single exclusion passing = disqualified.
        # We still evaluate ALL exclusions (not short-circuit at first)
        # so the output shows the full list of reasons.
        # ------------------------------------------------------------------
        exclusion_results: list[dict] = []
        for rule in scheme.get("exclusion_rules", []):
            result = evaluate_rule(rule, user_profile)
            exclusion_results.append(result)

            # Track missing fields
            if result["data_missing"]:
                field = result["field_checked"]
                _data_gaps.setdefault(field, []).append(scheme_id)

        # Exclusions that PASSED mean the user IS excluded
        triggered_exclusions = [r for r in exclusion_results if r["passed"]]

        if triggered_exclusions:
            # Build a clear English explanation of WHY they're excluded
            exclusion_reasons = "; ".join(
                r["reason"] for r in triggered_exclusions
            )
            not_eligible.append({
                "scheme_id":   scheme_id,
                "scheme_name": scheme_name,
                "reason":      f"EXCLUDED: {exclusion_reasons}",
                "rule_type":   "exclusion",
            })
            continue  # No need to check inclusions

        # ------------------------------------------------------------------
        # STEP B: Evaluate INCLUSION rules.
        # ALL inclusions must pass for full eligibility.
        # ------------------------------------------------------------------
        inclusion_results: list[dict] = []
        for rule in scheme.get("inclusion_rules", []):
            result = evaluate_rule(rule, user_profile)
            inclusion_results.append(result)

            # Track missing fields
            if result["data_missing"]:
                field = result["field_checked"]
                _data_gaps.setdefault(field, []).append(scheme_id)

        # Categorize inclusion results
        hard_failures = [
            r for r in inclusion_results
            if not r["passed"] and not r["data_missing"]
        ]
        missing_data_failures = [
            r for r in inclusion_results
            if not r["passed"] and r["data_missing"]
        ]
        passed_inclusions = [
            r for r in inclusion_results
            if r["passed"]
        ]

        # ------------------------------------------------------------------
        # STEP C: Determine eligibility category
        # ------------------------------------------------------------------

        # --- Not eligible: at least one inclusion definitively failed ---
        if hard_failures:
            failure_reasons = "; ".join(r["reason"] for r in hard_failures)
            not_eligible.append({
                "scheme_id":   scheme_id,
                "scheme_name": scheme_name,
                "reason":      f"INCLUSION FAILED: {failure_reasons}",
                "rule_type":   "inclusion",
            })
            continue

        # --- Calculate confidence score ---
        score, caps_applied = calculate_confidence_score(
            inclusion_results,
            exclusion_results,
            scheme,
        )

        # If score came back 0.0 from calculate_confidence_score for
        # an unexpected reason (schema error etc.), move to not_eligible
        if score == 0.0 and not triggered_exclusions and not hard_failures:
            not_eligible.append({
                "scheme_id":   scheme_id,
                "scheme_name": scheme_name,
                "reason":      (
                    f"Score computed as 0.0 due to: "
                    f"{caps_applied[0] if caps_applied else 'unknown reason'}. "
                    f"Check CONFIDENCE_AUDIT."
                ),
                "rule_type":   "confidence",
            })
            continue

        # --- Build document check ---
        required_docs    = scheme.get("required_documents", [])
        missing_docs     = _check_document_gaps(required_docs, user_profile)
        prereq_schemes   = scheme.get("prerequisite_schemes", [])

        # --- Build core result record ---
        core_result = {
            "scheme_id":   scheme_id,
            "scheme_name": scheme_name,
            "confidence_score": round(score, 2),
            "confidence_breakdown": {
                "inclusions_passed":   [
                    {"rule_id": r["rule_id"], "reason": r["reason"]}
                    for r in passed_inclusions
                ],
                "exclusions_checked":  [
                    {"rule_id": r["rule_id"], "passed": r["passed"]}
                    for r in exclusion_results
                ],
                "data_gaps": [
                    {
                        "rule_id":     r["rule_id"],
                        "field":       r["field_checked"],
                        "reason":      r["reason"],
                    }
                    for r in missing_data_failures
                ],
                "confidence_caps_applied": caps_applied,
            },
            "benefit":          scheme.get("benefit_description", ""),
            "benefit_amount":   scheme.get("benefit_amount_inr"),
            "documents_needed": required_docs,
            "missing_documents": missing_docs,
            "apply_after":      prereq_schemes,
            "application_url":  scheme.get("application_url", ""),
            "helpline":         scheme.get("helpline", ""),
            "is_hybrid":        is_hybrid,
            "hybrid_note":      (
                scheme.get("hybrid_config", {}).get("description", "")
                if is_hybrid else ""
            ),
            "guideline_version": scheme.get("guideline_version", ""),
            "state_variations":  scheme.get("state_variations", {}),
        }

        # --- Partially eligible: passed all available checks but
        #     some fields were missing ---
        if missing_data_failures:
            missing_fields = [r["field_checked"] for r in missing_data_failures]
            missing_rules  = [r["rule_id"] for r in missing_data_failures]

            # Build actionable gap analysis
            gap_lines = []
            for r in missing_data_failures:
                amb = _find_ambiguous_rule_for_field(scheme, r["rule_id"])
                if amb and amb.get("clarifying_question"):
                    gap_lines.append(
                        f"• Missing: '{r['field_checked']}' "
                        f"— Ask: \"{amb['clarifying_question']}\""
                    )
                else:
                    gap_lines.append(
                        f"• Missing: '{r['field_checked']}' "
                        f"(needed for rule {r['rule_id']})"
                    )

            what_to_do = _build_what_to_do(
                scheme, missing_fields, missing_docs, prereq_schemes
            )

            partial_result = {
                **core_result,
                "gap_analysis": (
                    f"Passed {len(passed_inclusions)} of "
                    f"{len(inclusion_results)} inclusion checks. "
                    f"Missing data for {len(missing_data_failures)} rule(s):\n"
                    + "\n".join(gap_lines)
                ),
                "missing_fields_for_rules": missing_rules,
                "what_to_do": what_to_do,
            }
            partially_eligible.append(partial_result)

        # --- Fully eligible (possibly with document gaps) ---
        else:
            fully_eligible.append(core_result)

    # ------------------------------------------------------------------
    # Build data_gaps_summary — fields missing across multiple schemes
    # surfaced as a single actionable list for the user.
    # ------------------------------------------------------------------
    data_gaps_summary = _build_data_gaps_summary(_data_gaps)

    # ------------------------------------------------------------------
    # Build application sequence for all eligible schemes
    # ------------------------------------------------------------------
    eligible_ids = [s["scheme_id"] for s in fully_eligible]
    partial_ids  = [s["scheme_id"] for s in partially_eligible]
    all_relevant_ids = eligible_ids + partial_ids

    application_sequence = build_application_sequence(all_relevant_ids)

    return {
        "fully_eligible":    fully_eligible,
        "partially_eligible": partially_eligible,
        "not_eligible":      not_eligible,
        "verify_manually":   verify_manually,
        "data_gaps_summary": data_gaps_summary,
        "ambiguous_flags":   ambiguous_flags,
        "application_sequence": application_sequence,
        "_meta": {
            "schemes_evaluated":  len(SCHEMES),
            "database_valid":     DATABASE_VALID,
            "color_available":    _COLOR_AVAILABLE,
        }
    }


# =============================================================================
# HELPER FUNCTIONS (used internally by match_schemes)
# =============================================================================

def _check_document_gaps(required_docs: list[str], user_profile: dict) -> list[str]:
    """
    Identify which required documents the user has indicated they don't have.

    Document fields in user_profile follow the convention:
        "has_aadhaar": True/False
        "has_bpl_card": True/False
        etc.

    We map from the document ID (e.g., "aadhaar_card") to the profile field
    (e.g., "has_aadhaar") using a best-effort heuristic. If the profile
    field is absent entirely, we don't flag it as missing — we only flag
    documents the user explicitly said they don't have.

    This avoids conflating "didn't answer" with "doesn't have".
    """
    _DOC_TO_PROFILE_FIELD = {
        "aadhaar_card":                     "has_aadhaar",
        "bank_account_linked_to_aadhaar":   "bank_account_status",
        "jan_dhan_or_active_bank_account":  "bank_account_status",
        "bpl_card_or_certificate":          "has_bpl_card",
        "land_records_khatoni_or_ror_or_patta": "has_land_records",
        "caste_certificate":                "has_caste_certificate",
        "income_certificate_from_tahsildar": "has_income_certificate",
        "disability_certificate_udid":       "has_disability_certificate",
        "ration_card":                       "has_ration_card",
    }

    missing = []
    for doc_id in required_docs:
        profile_field = _DOC_TO_PROFILE_FIELD.get(doc_id)
        if profile_field is None:
            continue  # No mapping — can't check; don't flag
        val = user_profile.get(profile_field)
        if val is False:
            missing.append(doc_id)
        elif val == "none":
            # Covers bank_account_status = "none"
            missing.append(doc_id)
    return missing


def _find_ambiguous_rule_for_field(scheme: dict, rule_id: str) -> dict | None:
    """
    Look up an ambiguous_rules entry that relates to the given rule_id.
    Used to surface clarifying questions in gap analysis.
    """
    for amb in scheme.get("ambiguous_rules", []):
        # ambiguous_rules may reference a single rule or a list
        affects = amb.get("affects_rules", [])
        if isinstance(affects, str):
            affects = [affects]
        if rule_id in affects or amb.get("rule_id") == rule_id:
            return amb
    return None


def _build_what_to_do(
    scheme: dict,
    missing_fields: list[str],
    missing_docs: list[str],
    prereq_schemes: list[str],
) -> str:
    """
    Build a plain-English actionable next step for a partially eligible scheme.

    Priority order:
    1. If prerequisites are missing, do those first.
    2. Then collect missing documents.
    3. Then provide the missing profile information.
    4. Then apply.
    """
    steps = []
    step_num = 1

    if prereq_schemes:
        names = []
        for pid in prereq_schemes:
            pscheme = SCHEMES.get(pid, {})
            names.append(pscheme.get("name", pid))
        steps.append(
            f"Step {step_num}: First complete these prerequisite schemes: "
            f"{', '.join(names)}."
        )
        step_num += 1

    if missing_docs:
        steps.append(
            f"Step {step_num}: Obtain these documents: "
            f"{', '.join(missing_docs)}."
        )
        step_num += 1

    if missing_fields:
        steps.append(
            f"Step {step_num}: Provide the following information to confirm "
            f"eligibility: {', '.join(missing_fields)}."
        )
        step_num += 1

    steps.append(
        f"Step {step_num}: Apply at {scheme.get('application_url', 'official scheme portal')} "
        f"or call helpline {scheme.get('helpline', 'N/A')}."
    )

    return " | ".join(steps)


def _build_data_gaps_summary(
    gaps: dict[str, list[str]]
) -> list[str]:
    """
    Convert the per-field gap tracking dict into a prioritized summary.

    Fields missing across many schemes are surfaced first — they are the
    highest-value fields to collect. A field needed by 8 schemes is more
    important to collect than one needed by 1 scheme.
    """
    if not gaps:
        return []

    # Sort by number of schemes affected, descending
    sorted_gaps = sorted(gaps.items(), key=lambda kv: len(kv[1]), reverse=True)
    summary = []
    for field, scheme_ids in sorted_gaps:
        count = len(scheme_ids)
        if count >= 2:
            summary.append(
                f"'{field}' was missing — affected {count} scheme checks "
                f"({', '.join(scheme_ids[:3])}{'...' if count > 3 else ''}). "
                f"Providing this field would significantly improve match quality."
            )
        else:
            summary.append(
                f"'{field}' was missing — affected scheme: {scheme_ids[0]}."
            )
    return summary


# =============================================================================
# SECTION 4 — APPLICATION SEQUENCE BUILDER
# =============================================================================

def build_application_sequence(eligible_scheme_ids: list[str]) -> list[str]:
    """
    Topological sort of eligible schemes so prerequisites come first.

    Design:
    -------
    We build a directed graph where an edge A → B means "A must be done
    before B". This is Kahn's algorithm for topological sort.

    Circular dependencies are detected and resolved by breaking the cycle
    at the scheme that appears later alphabetically (arbitrary but
    deterministic). A warning is added to the output explaining this.

    We only sort schemes that are in the eligible_scheme_ids list.
    If a prerequisite scheme is NOT in the eligible list (e.g., Jan Dhan
    because the user already has a bank account), it is noted but not
    added to the sequence — we don't tell users to apply for schemes
    they already have or don't qualify for.

    Edge case: if eligible_scheme_ids is empty, return [].
    """
    if not eligible_scheme_ids:
        return []

    eligible_set = set(eligible_scheme_ids)

    # Build adjacency: prereqs_of[scheme_id] = set of prereq_ids
    # that are also in our eligible set
    prereqs_of: dict[str, set[str]] = {sid: set() for sid in eligible_set}
    in_degree  : dict[str, int]      = {sid: 0 for sid in eligible_set}

    for scheme_id in eligible_set:
        scheme = SCHEMES.get(scheme_id, {})
        for prereq_id in scheme.get("prerequisite_schemes", []):
            if prereq_id in eligible_set:
                # prereq_id must come before scheme_id
                prereqs_of[prereq_id]  # ensure key exists
                prereqs_of.setdefault(prereq_id, set())
                # Add edge: prereq_id → scheme_id
                # scheme_id has one more thing depending on it
                # We build: dependents_of[prereq_id] includes scheme_id
                pass  # built below

    # Rebuild cleanly: dependents_of[A] = set of schemes that need A first
    dependents_of: dict[str, set[str]] = {sid: set() for sid in eligible_set}

    for scheme_id in eligible_set:
        scheme = SCHEMES.get(scheme_id, {})
        for prereq_id in scheme.get("prerequisite_schemes", []):
            if prereq_id in eligible_set:
                dependents_of[prereq_id].add(scheme_id)
                in_degree[scheme_id] = in_degree.get(scheme_id, 0) + 1

    # Kahn's BFS topological sort
    from collections import deque
    queue  = deque(sid for sid, deg in in_degree.items() if deg == 0)
    result : list[str] = []
    visited: set[str]  = set()

    while queue:
        # Sort queue contents for deterministic output
        # (multiple zero-in-degree nodes could appear simultaneously)
        current = sorted(queue)[0]
        queue.remove(current)

        if current in visited:
            continue
        visited.add(current)
        result.append(current)

        for dependent in sorted(dependents_of.get(current, [])):
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    # Handle circular dependencies — any nodes not visited are in a cycle
    cycle_nodes = eligible_set - visited
    if cycle_nodes:
        # Append them in sorted order with a warning prefix
        for node in sorted(cycle_nodes):
            result.append(f"[CYCLE_DETECTED:{node}]")

    return result


# =============================================================================
# SECTION 5 — OUTPUT FORMATTER (colored console output)
# =============================================================================

def _divider(char: str = "─", width: int = 72) -> str:
    return char * width

def _color(text: str, fore_color: str) -> str:
    """Apply color only if colorama is available."""
    if _COLOR_AVAILABLE:
        return f"{fore_color}{text}{Style.RESET_ALL}"
    return text

def _confidence_bar(score: float, width: int = 20) -> str:
    """
    Visual confidence bar: ████████░░░░░░░░░░░░  0.40
    Gives a quick visual read without requiring a GUI.
    """
    filled = int(score * width)
    empty  = width - filled
    bar    = "█" * filled + "░" * empty
    pct    = f"{score:.0%}"

    if score >= 0.75:
        color = Fore.GREEN
    elif score >= 0.50:
        color = Fore.YELLOW
    else:
        color = Fore.RED

    if _COLOR_AVAILABLE:
        return f"{color}{bar}{Style.RESET_ALL} {pct}"
    return f"{bar} {pct}"


def print_results(results: dict, profile_label: str = "User") -> None:
    """
    Pretty-print match_schemes() output to stdout.

    Sections printed:
    1. Header with profile label
    2. Fully eligible (GREEN)
    3. Partially eligible (YELLOW) with gap analysis
    4. Verify manually (BLUE)
    5. Not eligible — only the count, not the full list
       (keep output readable; not_eligible can be 10+ schemes)
    6. Data gaps summary
    7. Application sequence
    """
    print()
    print(_divider("═"))
    print(
        _color(f"  KALAM MATCH RESULTS — {profile_label}", Fore.CYAN)
    )
    meta = results.get("_meta", {})
    print(
        f"  Schemes evaluated: {meta.get('schemes_evaluated', '?')} | "
        f"Database valid: {meta.get('database_valid', '?')}"
    )
    print(_divider("═"))

    # ----------------------------------------------------------------
    # Fully eligible
    # ----------------------------------------------------------------
    fully = results.get("fully_eligible", [])
    print()
    print(_color(f"  ✅ FULLY ELIGIBLE ({len(fully)} schemes)", Fore.GREEN))
    print(_divider())

    if not fully:
        print("  None")
    else:
        for s in fully:
            print()
            print(
                _color(f"  ► {s['scheme_name']}", Fore.GREEN)
                + f"  [{s['scheme_id']}]"
            )
            print(f"  Confidence: {_confidence_bar(s['confidence_score'])}")
            print(f"  Benefit:    {s['benefit']}")

            if s.get("missing_documents"):
                print(
                    _color(
                        f"  ⚠ Missing documents: {', '.join(s['missing_documents'])}",
                        Fore.YELLOW,
                    )
                )

            if s.get("is_hybrid"):
                print(
                    _color(
                        f"  ℹ Hybrid scheme — also requires database verification: "
                        f"{s.get('hybrid_note', '')}",
                        Fore.CYAN,
                    )
                )

            if s.get("apply_after"):
                prereq_names = [
                    SCHEMES.get(p, {}).get("name", p)
                    for p in s["apply_after"]
                ]
                print(f"  Apply after: {', '.join(prereq_names)}")

            print(f"  Apply at:   {s['application_url']}")
            if s.get("helpline"):
                print(f"  Helpline:   {s['helpline']}")

            # Show confidence caps if score < 1.0
            caps = s["confidence_breakdown"].get("confidence_caps_applied", [])
            if caps:
                print(f"  Confidence caps:")
                for cap in caps:
                    print(f"    • {cap}")

    # ----------------------------------------------------------------
    # Partially eligible
    # ----------------------------------------------------------------
    partial = results.get("partially_eligible", [])
    print()
    print(_color(f"  🟡 PARTIALLY ELIGIBLE ({len(partial)} schemes)", Fore.YELLOW))
    print(_divider())

    if not partial:
        print("  None")
    else:
        for s in partial:
            print()
            print(
                _color(f"  ► {s['scheme_name']}", Fore.YELLOW)
                + f"  [{s['scheme_id']}]"
            )
            print(f"  Confidence: {_confidence_bar(s['confidence_score'])}")
            print(f"  Gap Analysis:")
            for line in s.get("gap_analysis", "").split("\n"):
                print(f"    {line}")
            print(f"  What to do:")
            for step in s.get("what_to_do", "").split(" | "):
                print(f"    → {step}")

    # ----------------------------------------------------------------
    # Verify manually (database_membership)
    # ----------------------------------------------------------------
    verify = results.get("verify_manually", [])
    print()
    print(_color(f"  🔵 VERIFY MANUALLY ({len(verify)} schemes)", Fore.BLUE))
    print(_divider())

    if not verify:
        print("  None")
    else:
        for s in verify:
            print()
            print(_color(f"  ► {s['scheme_name']}", Fore.BLUE) + f"  [{s['scheme_id']}]")
            print(f"  Reason:  {s['reason']}")
            print(f"  How to verify: {s['how_to_verify']}")
            if s.get("verification_url"):
                print(f"  Portal:  {s['verification_url']}")
            if s.get("database_warning"):
                print(_color(f"  ⚠ {s['database_warning']}", Fore.RED))

    # ----------------------------------------------------------------
    # Not eligible — count and top reasons only
    # ----------------------------------------------------------------
    not_elig = results.get("not_eligible", [])
    print()
    print(_color(f"  ❌ NOT ELIGIBLE ({len(not_elig)} schemes)", Fore.RED))
    print(_divider())
    if not_elig:
        # Show first 5 only; full list available in returned dict
        shown = not_elig[:5]
        for s in shown:
            print(f"  • {s['scheme_name']}: {s['reason'][:120]}...")
        if len(not_elig) > 5:
            print(f"  ... and {len(not_elig) - 5} more (access via results['not_eligible'])")

    # ----------------------------------------------------------------
    # Data gaps summary
    # ----------------------------------------------------------------
    gaps = results.get("data_gaps_summary", [])
    if gaps:
        print()
        print(_color("  📋 DATA GAPS (fields that would improve match quality)", Fore.CYAN))
        print(_divider())
        for gap in gaps[:5]:  # top 5 most impactful
            print(f"  • {gap}")

    # ----------------------------------------------------------------
    # Ambiguous flags
    # ----------------------------------------------------------------
    flags = results.get("ambiguous_flags", [])
    if flags:
        print()
        print(_color("  ⚠ AMBIGUOUS RULES ENCOUNTERED", Fore.YELLOW))
        print(_divider())
        for flag in flags[:3]:  # top 3
            print(f"  • {flag[:120]}...")

    # ----------------------------------------------------------------
    # Application sequence
    # ----------------------------------------------------------------
    seq = results.get("application_sequence", [])
    if seq:
        print()
        print(_color("  📋 RECOMMENDED APPLICATION SEQUENCE", Fore.CYAN))
        print(_divider())
        for i, scheme_id in enumerate(seq, 1):
            if scheme_id.startswith("[CYCLE"):
                print(_color(f"  {i}. {scheme_id} — circular dependency detected", Fore.RED))
            else:
                scheme_name = SCHEMES.get(scheme_id, {}).get("name", scheme_id)
                print(f"  {i}. {scheme_name}  [{scheme_id}]")

    print()
    print(_divider("═"))
    print()


# =============================================================================
# SECTION 5 — TEST RUNNER
# =============================================================================

if __name__ == "__main__":

    # =========================================================================
    # PROFILE 1: Clear rural farmer
    # Expected behavior:
    #   - PM-KISAN: likely fully eligible (all fields provided, no exclusions)
    #   - MGNREGA: fully eligible (rural, 18+)
    #   - PMAY-G: partially eligible (SECC field missing → hybrid)
    #   - SSY: partially eligible (has girl under 10, missing some fields)
    #   - NSAP: not eligible (age 52, not 60+)
    #   - AB-PMJAY: verify_manually (database_membership)
    # =========================================================================
    profile_1 = {
        "age":                              52,
        "gender":                           "male",
        "state":                            "Uttar Pradesh",
        "residence_type":                   "rural",
        "caste_category":                   "obc",
        "is_indian_citizen":                True,
        "owns_agricultural_land":           True,
        "land_ownership_type":              "individual",
        "land_area_hectares":               1.5,
        "land_is_cultivable":               True,
        "annual_household_income_inr":      85000,
        "filed_income_tax":                 False,
        "filed_income_tax_last_assessment_year": False,   # PM-KISAN uses this field name
        "is_or_was_elected_representative": False,
        "is_current_constitutional_post_holder": False,
        "is_former_constitutional_post_holder":  False,
        "is_current_minister":              False,
        "is_former_minister":               False,
        "is_current_mp_or_mla_or_mlc":      False,
        "is_former_mp_or_mla_or_mlc":       False,
        "is_current_zila_panchayat_president_or_mayor": False,
        "is_serving_central_or_state_govt_employee": False,
        "is_serving_or_retired_govt_employee": False,
        "monthly_pension_if_retired_govt":  None,
        "is_registered_professional":       False,
        "has_aadhaar":                      True,
        "bank_account_status":              "active_with_dbt",
        "has_bpl_card":                     True,
        "is_bpl_listed_or_destitute":       True,
        "is_bpl_household":                 True,
        "housing_status":                   "kutcha",
        "has_pucca_house_anywhere_in_india": False,
        "family_size":                      5,
        "num_girls_under_10":               1,
        "has_girl_child_under_10":          True,
        "is_parent_or_legal_guardian":      True,
        "girl_child_age":                   6,
        "num_ssa_accounts_already_open":    0,
        "is_farmer":                        True,
        "is_street_vendor":                 False,
        "is_willing_to_do_unskilled_manual_work": True,
        "currently_enrolled_schemes":       [],
        "has_savings_bank_account":         True,
        "is_income_taxpayer":               False,
        "is_member_of_epf_esi_or_other_statutory_pension": False,
    }

    # =========================================================================
    # PROFILE 2: Urban pregnant woman with partial data
    # Expected behavior:
    #   - PMMVY: partially eligible (pregnant, female, but bank account missing)
    #   - JSY: partially eligible (pregnant, female, but delivery details missing)
    #   - APY: possibly eligible (age 28, < 40) but missing several fields
    #   - PMSBY/PMJJBY: partially eligible (age in range, bank missing)
    #   - PM-KISAN: not eligible (urban, no land data)
    #   - MGNREGA: not eligible (urban)
    #   - Many fields intentionally missing to test gap handling
    # =========================================================================
    profile_2 = {
        "age":                          28,
        "gender":                       "female",
        "state":                        "Maharashtra",
        "residence_type":               "urban",
        "caste_category":               "sc",
        "is_pregnant_or_recently_delivered": True,
        "is_pregnant_or_lactating":     True,
        "has_aadhaar":                  True,
        "bank_account_status":          "none",       # explicitly no account
        "has_savings_bank_account":     False,
        "annual_household_income_inr":  120000,
        "filed_income_tax":             False,
        "filed_income_tax_last_assessment_year": False,
        "is_indian_citizen":            True,
        # Many fields NOT provided — engine must handle gracefully:
        # is_or_was_elected_representative — missing
        # owns_agricultural_land — missing
        # housing_status — missing
        # has_pucca_house_anywhere_in_india — missing
    }

    # =========================================================================
    # PROFILE 3: Edge case — retired govt employee farmer with sub-threshold pension
    # Expected behavior:
    #   - PM-KISAN: pension is ₹8,500 < ₹10,000 threshold → NOT excluded by B9
    #               This is the key edge case — should be ELIGIBLE
    #   - MGNREGA: fully eligible (rural, 64 years old, 18+ check passes)
    #   - NSAP IGNOAPS: partially eligible (age 64 ≥ 60 ✓, need BPL check)
    #   - APY: not eligible (age 64 > 40)
    #   - PMJJBY: not eligible (age 64 > 50, cannot enroll)
    #   - PMSBY: eligible (age 64 ≤ 70)
    # =========================================================================
    profile_3 = {
        "age":                              64,
        "gender":                           "male",
        "state":                            "Punjab",
        "residence_type":                   "rural",
        "caste_category":                   "general",
        "is_indian_citizen":                True,
        "owns_agricultural_land":           True,
        "land_ownership_type":              "individual",
        "land_area_hectares":               3.0,
        "land_is_cultivable":               True,
        "is_serving_or_retired_govt_employee": True,
        "is_serving_central_or_state_govt_employee": False,  # RETIRED not serving
        "monthly_pension_if_retired_govt":  8500,  # KEY: below 10000 threshold
        "filed_income_tax":                 False,
        "filed_income_tax_last_assessment_year": False,
        "is_or_was_elected_representative": False,
        "is_current_constitutional_post_holder":  False,
        "is_former_constitutional_post_holder":   False,
        "is_current_minister":              False,
        "is_former_minister":               False,
        "is_current_mp_or_mla_or_mlc":      False,
        "is_former_mp_or_mla_or_mlc":       False,
        "is_current_zila_panchayat_president_or_mayor": False,
        "is_registered_professional":       False,
        "has_aadhaar":                      True,
        "bank_account_status":              "active_with_dbt",
        "has_savings_bank_account":         True,
        "is_income_taxpayer":               False,
        "is_bpl_listed_or_destitute":       False,  # Not BPL — affects NSAP
        "is_bpl_household":                 False,
        "housing_status":                   "pucca",
        "has_pucca_house_anywhere_in_india": True,
        "is_farmer":                        True,
        "is_street_vendor":                 False,
        "is_willing_to_do_unskilled_manual_work": True,
        "is_member_of_epf_esi_or_other_statutory_pension": True,
        "is_receiving_other_govt_pension":  True,
        "currently_enrolled_schemes":       [],
    }

    # =========================================================================
    # Run all three profiles
    # =========================================================================
    profiles = [
        (profile_1, "PROFILE 1 — Rural OBC Farmer, UP (Age 52)"),
        (profile_2, "PROFILE 2 — Urban SC Pregnant Woman, Maharashtra (Age 28)"),
        (profile_3, "PROFILE 3 — Retired Govt Employee Farmer, Punjab (Age 64)"),
    ]

    for profile_data, label in profiles:
        try:
            results = match_schemes(profile_data)
            print_results(results, label)
        except Exception as exc:
            print(
                _color(f"\n  FATAL ERROR processing {label}:\n  {exc}", Fore.RED)
            )
            traceback.print_exc()
            print()

    # =========================================================================
    # Edge case mini-test: completely empty profile
    # Engine must not crash — must return all as partially_eligible or
    # not_eligible with data_missing=True reasons.
    # =========================================================================
    print()
    print(_color("  EDGE CASE: Empty profile (no fields provided)", Fore.MAGENTA))
    print(_divider())
    empty_results = match_schemes({})
    empty_fully   = len(empty_results["fully_eligible"])
    empty_partial = len(empty_results["partially_eligible"])
    empty_gaps    = len(empty_results["data_gaps_summary"])
    print(
        f"  Fully eligible: {empty_fully} | "
        f"Partially eligible: {empty_partial} | "
        f"Data gaps identified: {empty_gaps}"
    )
    print(
        f"  ✓ Engine handled empty profile without crashing."
        if empty_fully == 0 else
        f"  ⚠ Unexpected fully_eligible results on empty profile — review logic."
    )
    print(_divider("═"))