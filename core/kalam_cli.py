# =============================================================================
# KALAM — Conversational Hinglish CLI Interface
# kalam_cli.py
#
# Install dependencies:
#   pip install colorama
#
# Run:
#   python kalam_cli.py
#
# Architecture decisions encoded here:
#   1. Questions are in Hinglish — written as a government helper would speak,
#      not as a translation of English bureaucratic language.
#   2. Parser never crashes on unexpected input — always returns a result
#      with confidence level, never throws an exception to the user.
#   3. Contradictions are surfaced immediately, not at the end.
#   4. 'skip', 'back', 'result', 'help' are always available.
#   5. Partial results are clearly labeled as incomplete.
#   6. The conversation is stateful but the final profile is stateless —
#      no user data is persisted after the session ends.
# =============================================================================

from __future__ import annotations

import re
import sys
from typing import Any

# ---------------------------------------------------------------------------
# Colorama — graceful fallback
# ---------------------------------------------------------------------------
try:
    from colorama import init as _colorama_init, Fore, Style
    _colorama_init(autoreset=True)
    _COLOR = True
except ImportError:
    class _NoColor:
        def __getattr__(self, _: str) -> str:
            return ""
    Fore = _NoColor()
    Style = _NoColor()
    _COLOR = False

# ---------------------------------------------------------------------------
# Import matching engine
# ---------------------------------------------------------------------------
try:
    from matching_engine import match_schemes, print_results
except ImportError as e:
    print(f"FATAL: Cannot import matching_engine.py — {e}", file=sys.stderr)
    sys.exit(1)


# =============================================================================
# SECTION 1 — HINGLISH QUESTION BANK
# =============================================================================
# Design principle: Every question must pass the "government helper test" —
# would a helpful, literate person at a Jan Seva Kendra actually say this?
# Questions avoid jargon, offer examples, and acknowledge that exact numbers
# are often unknown to the user.
#
# Structure per question:
#   text       : the question to display
#   help_text  : shown if user types 'help'
#   field      : the profile field this answer fills
#   input_type : "yes_no", "number", "text", "choice", "income", "area"
#   choices    : for "choice" type — list of valid options shown to user
#   skip_ok    : whether user can skip this question
#   condition  : optional lambda(profile) → bool — skip if returns False
# =============================================================================

QUESTION_BANK = [

    # -------------------------------------------------------------------------
    # BLOCK 1 — Identity
    # -------------------------------------------------------------------------
    {
        "field": "age",
        "block": 1,
        "text": (
            "Sabse pehle — aapki umar kitni hai?\n"
            "  (Sirf number likhiye, jaise: 35)"
        ),
        "help_text": (
            "Umar se pata chalta hai kaun si schemes aapke liye hain.\n"
            "Kuch schemes sirf 18+ ke liye hain, kuch 60+ ke liye."
        ),
        "input_type": "number",
        "skip_ok": False,
        "condition": None,
    },
    {
        "field": "gender",
        "block": 1,
        "text": (
            "Aap mard hain ya aurat?\n"
            "  (Likhiye: mard / aurat / transgender)"
        ),
        "help_text": (
            "Kuch schemes sirf mahilaon ke liye hain — jaise Ujjwala, "
            "Matru Vandana. Isliye poochh rahe hain."
        ),
        "input_type": "text",
        "skip_ok": False,
        "condition": None,
    },
    {
        "field": "state",
        "block": 1,
        "text": (
            "Aap kaunse state mein rehte hain?\n"
            "  (Jaise: UP, Bihar, Maharashtra, Rajasthan...)"
        ),
        "help_text": (
            "State se pata chalta hai kaunsi state schemes apply hoti hain. "
            "Central schemes toh sab jagah hain, lekin state schemes "
            "alag-alag hoti hain."
        ),
        "input_type": "text",
        "skip_ok": False,
        "condition": None,
    },
    {
        "field": "residence_type",
        "block": 1,
        "text": (
            "Aap gaon mein rehte hain ya sheher mein?\n"
            "  → Gaon/Rural: Gram Panchayat area\n"
            "  → Sheher/Urban: Municipality ya Municipal Corporation area\n"
            "  (Likhiye: gaon / sheher)"
        ),
        "help_text": (
            "Yeh bahut important hai. PMAY-Gramin sirf gaon walon ke liye hai, "
            "PMAY-Urban sheher walon ke liye. MGNREGA bhi sirf gaon ke liye hai. "
            "Agar aap sure nahi hain, apne Gram Panchayat ya Ward office se "
            "poochh sakte hain."
        ),
        "input_type": "text",
        "skip_ok": False,
        "condition": None,
    },
    {
        "field": "caste_category",
        "block": 1,
        "text": (
            "Aap kaunsi category mein aate hain?\n"
            "  1. General (Samanya Varg)\n"
            "  2. OBC (Other Backward Class / Pichda Varg)\n"
            "  3. SC (Scheduled Caste / Dalit)\n"
            "  4. ST (Scheduled Tribe / Adivasi)\n"
            "  (Number ya naam likhiye)"
        ),
        "help_text": (
            "Caste certificate hona zaroori hai agar SC/ST/OBC schemes "
            "ke liye apply karna hai. Certificate nahi hai toh bhi batayein — "
            "hum bata denge kaise milega."
        ),
        "input_type": "choice",
        "choices": ["general", "obc", "sc", "st"],
        "skip_ok": True,
        "condition": None,
    },
    {
        "field": "is_indian_citizen",
        "block": 1,
        "text": "Kya aap Indian citizen hain? (haan/nahi)",
        "help_text": "Sabhi government schemes sirf Indian citizens ke liye hain.",
        "input_type": "yes_no",
        "skip_ok": False,
        "condition": None,
    },

    # -------------------------------------------------------------------------
    # BLOCK 2 — Economic Status
    # -------------------------------------------------------------------------
    {
        "field": "annual_household_income_inr",
        "block": 2,
        "text": (
            "Aapke ghar mein ek saal mein kitna paisa aata hai?\n"
            "  Saare log mila ke — naukri, kheti, dukan, kuch bhi.\n"
            "  Rough idea bhi chalega, exact number zaroori nahi.\n"
            "  (Jaise: '5 hazaar mahine', '2 lakh saal ka', '300 roz')"
        ),
        "help_text": (
            "Ghar ki amdani se pata chalta hai kaunsi schemes apply hoti hain. "
            "Agar aap sure nahi hain toh roughly batayein — '1-2 lakh ke beech' "
            "bhi likh sakte hain."
        ),
        "input_type": "income",
        "skip_ok": True,
        "condition": None,
    },
    {
        "field": "has_bpl_card",
        "block": 2,
        "text": (
            "Kya aapke paas BPL card hai?\n"
            "  (Below Poverty Line card — yeh ration card se alag hota hai)\n"
            "  (haan/nahi/pata nahi)"
        ),
        "help_text": (
            "BPL card kai schemes ke liye zaroori hai. Agar aapke paas "
            "purple/pink ration card hai ya 'Antyodaya' card hai, "
            "toh probably BPL mein hain."
        ),
        "input_type": "yes_no",
        "skip_ok": True,
        "condition": None,
    },
    {
        "field": "filed_income_tax_last_assessment_year",
        "block": 2,
        "text": (
            "Kya aapne pichhle saal income tax return bhara tha?\n"
            "  (ITR file kiya tha? Zyada tar gaon walon ko yeh nahi bharna padta)\n"
            "  (haan/nahi)"
        ),
        "help_text": (
            "Income tax filers ko PM Kisan nahi milta. Isliye poochh rahe hain. "
            "Agar aapki income ₹2.5 lakh se kam hai toh ITR ki zaroorat nahi hoti."
        ),
        "input_type": "yes_no",
        "skip_ok": True,
        "condition": None,
    },

    # -------------------------------------------------------------------------
    # BLOCK 3 — Land and Housing
    # -------------------------------------------------------------------------
    {
        "field": "owns_agricultural_land",
        "block": 3,
        "text": (
            "Kya aapke naam pe kheti ki zameen hai?\n"
            "  (KHUD ke naam pe — register honi chahiye)\n"
            "  (haan/nahi)"
        ),
        "help_text": (
            "PM Kisan ke liye zameen OWNERSHIP zaroori hai — sirf kheti karna "
            "kaafi nahi. Agar zameen kisi aur ki hai aur aap sirf farming karte "
            "hain, toh PM Kisan nahi milega. Lekin MGNREGA mil sakta hai."
        ),
        "input_type": "yes_no",
        "skip_ok": True,
        "condition": None,
    },
    {
        "field": "land_ownership_type",
        "block": 3,
        "text": (
            "Zameen kaise registered hai?\n"
            "  1. Sirf aapke naam pe (Individual)\n"
            "  2. Aap aur family milke (Joint)\n"
            "  3. Kisi cooperative/society ke naam pe (Institutional)\n"
            "  (Number ya naam likhiye)"
        ),
        "help_text": (
            "PM Kisan ke liye individual ya joint ownership chahiye. "
            "Agar cooperative/society ke naam pe hai toh PM Kisan nahi milega."
        ),
        "input_type": "choice",
        "choices": ["individual", "joint", "institutional"],
        "skip_ok": True,
        # Only ask if they own land
        "condition": lambda p: p.get("owns_agricultural_land") is True,
    },
    {
        "field": "land_area_hectares",
        "block": 3,
        "text": (
            "Kitni zameen hai? Bigha, acre, ya hectare mein bata sakte hain.\n"
            "  (Jaise: '2 bigha', '1 acre', '0.5 hectare')"
        ),
        "help_text": (
            "Zameen ka size kai state-level schemes mein matter karta hai. "
            "Central PM Kisan mein koi limit nahi — par state schemes mein ho "
            "sakti hai. Rough idea bhi chalega."
        ),
        "input_type": "area",
        "skip_ok": True,
        "condition": lambda p: p.get("owns_agricultural_land") is True,
    },
    {
        "field": "land_is_cultivable",
        "block": 3,
        "text": (
            "Kya yeh zameen kheti ke kaam ki hai?\n"
            "  (Kya uspe fasal ugti hai ya ugsak ti hai?)\n"
            "  (haan/nahi)"
        ),
        "help_text": (
            "Wastelands ya rocky land jo farming ke liye use nahi ho sakti "
            "woh usually count nahi hoti PM Kisan mein."
        ),
        "input_type": "yes_no",
        "skip_ok": True,
        "condition": lambda p: p.get("owns_agricultural_land") is True,
    },
    {
        "field": "housing_status",
        "block": 3,
        "text": (
            "Aapka ghar kaisa hai?\n"
            "  1. Pucca (Cement/brick ka pakka ghar)\n"
            "  2. Semi-pucca (Kuch pakka, kuch kachcha)\n"
            "  3. Kutcha (Mitti/bamboo/plastic ka ghar)\n"
            "  4. Homeless (Koi permanent ghar nahi)\n"
            "  5. Rented (Kiraye ka)\n"
            "  (Number ya naam likhiye)"
        ),
        "help_text": (
            "PMAY — Pradhan Mantri Awaas Yojana — sirf unhe milti hai "
            "jinke paas pucca ghar nahi hai. Isliye poochh rahe hain."
        ),
        "input_type": "choice",
        "choices": ["pucca", "semi_pucca", "kutcha", "homeless", "rented"],
        "skip_ok": True,
        "condition": None,
    },
    {
        "field": "has_pucca_house_anywhere_in_india",
        "block": 3,
        "text": (
            "Kya aapke ya aapke pati/patni ke naam pe KAHIN BHI\n"
            "India mein pakka ghar hai?\n"
            "  (Gaon mein, sheher mein, koi bhi jagah)\n"
            "  (haan/nahi)"
        ),
        "help_text": (
            "PMAY ek baar milti hai. Agar kisi ke paas kisi bhi jagah "
            "pucca house hai — chahe woh rehte wahan nahi hain — "
            "toh PMAY nahi milegi."
        ),
        "input_type": "yes_no",
        "skip_ok": True,
        "condition": None,
    },

    # -------------------------------------------------------------------------
    # BLOCK 4 — Documents
    # -------------------------------------------------------------------------
    {
        "field": "has_aadhaar",
        "block": 4,
        "text": (
            "Kya aapke paas Aadhaar card hai?\n"
            "  (12 digit ka number wala card)\n"
            "  (haan/nahi)"
        ),
        "help_text": (
            "Aadhaar lagbhag sabhi government schemes ke liye zaroori hai. "
            "Agar nahi hai toh sabse pehle nearest Aadhaar centre jaiye. "
            "Hum yeh bhi batayenge."
        ),
        "input_type": "yes_no",
        "skip_ok": False,
        "condition": None,
    },
    {
        "field": "bank_account_status",
        "block": 4,
        "text": (
            "Aapka bank account hai?\n"
            "  1. Haan, aur Aadhaar se linked hai (DBT milta hai)\n"
            "  2. Haan, lekin Aadhaar se linked nahi\n"
            "  3. Haan, Jan Dhan account hai\n"
            "  4. Nahi, koi bank account nahi\n"
            "  (Number likhiye)"
        ),
        "help_text": (
            "Sarkar ka paisa directly bank mein aata hai — DBT ke through. "
            "Agar account nahi hai toh Jan Dhan account kholna padega — "
            "yeh bilkul free hai, zero balance pe chalta hai."
        ),
        "input_type": "choice",
        "choices": [
            "active_with_dbt", "active_no_dbt", "jan_dhan", "none"
        ],
        "skip_ok": False,
        "condition": None,
    },

    # -------------------------------------------------------------------------
    # BLOCK 5 — Family
    # -------------------------------------------------------------------------
    {
        "field": "family_size",
        "block": 5,
        "text": (
            "Aapke ghar mein kitne log hain?\n"
            "  (Aap milake — jo ek hi rasode mein khana khate hain)\n"
            "  (Sirf number likhiye)"
        ),
        "help_text": (
            "Family size se benefits calculate hote hain kuch schemes mein. "
            "MGNREGA mein 100 din per family milte hain."
        ),
        "input_type": "number",
        "skip_ok": True,
        "condition": None,
    },
    {
        "field": "num_girls_under_10",
        "block": 5,
        "text": (
            "Kya aapke ghar mein 10 saal se choti koi beti hai?\n"
            "  (haan/nahi — agar haan: kitni?)"
        ),
        "help_text": (
            "Sukanya Samriddhi Yojana — beti ke liye savings scheme — "
            "10 saal se choti beti ke liye khul sakta hai. "
            "Bahut achha interest milta hai, tax bhi nahi lagta."
        ),
        "input_type": "yes_no",
        "skip_ok": True,
        "condition": None,
    },
    {
        "field": "is_pregnant_or_lactating",
        "block": 5,
        "text": (
            "Kya aap abhi pregnant hain ya 6 mahine se chote\n"
            "bachche ko dudh pila rahi hain?\n"
            "  (haan/nahi)"
        ),
        "help_text": (
            "Pradhan Mantri Matru Vandana Yojana aur Janani Suraksha Yojana "
            "pregnant aur lactating mothers ke liye hain. "
            "₹5,000 tak ka fayda mil sakta hai."
        ),
        "input_type": "yes_no",
        "skip_ok": True,
        # Only ask women
        "condition": lambda p: p.get("gender") == "female",
    },

    # -------------------------------------------------------------------------
    # BLOCK 6 — Occupation
    # -------------------------------------------------------------------------
    {
        "field": "is_farmer",
        "block": 6,
        "text": (
            "Kya aap kheti karte hain? (Apna kaam ya kisi ke liye?)\n"
            "  (haan/nahi)"
        ),
        "help_text": "Farmer ke liye kai schemes hain — PM Kisan, MGNREGA, etc.",
        "input_type": "yes_no",
        "skip_ok": True,
        "condition": None,
    },
    {
        "field": "is_street_vendor",
        "block": 6,
        "text": (
            "Kya aap rehri/patri/pheri wale ka kaam karte hain?\n"
            "  (Sadak pe kuch bechte hain — sabzi, chaai, kapde, kuch bhi?)\n"
            "  (haan/nahi)"
        ),
        "help_text": (
            "PM SVANidhi — street vendors ke liye ₹10,000 tak ka loan "
            "bina guarantee ke milta hai. Sheher mein rehne walon ke liye."
        ),
        "input_type": "yes_no",
        "skip_ok": True,
        "condition": None,
    },
    {
        "field": "is_serving_or_retired_govt_employee",
        "block": 6,
        "text": (
            "Kya aap government job mein hain ya the?\n"
            "  (Central ya State — teacher, police, clerk, kuch bhi)\n"
            "  (haan/nahi)"
        ),
        "help_text": (
            "Current ya retired government employees ko kuch schemes nahi miltin. "
            "Jaise PM Kisan — retired employees jinhe ₹10,000+ pension milti hai "
            "unhe yeh nahi milta."
        ),
        "input_type": "yes_no",
        "skip_ok": True,
        "condition": None,
    },
    {
        "field": "monthly_pension_if_retired_govt",
        "block": 6,
        "text": (
            "Aapko har mahine kitni pension milti hai?\n"
            "  (Sirf number — rupees mein. Jaise: 8500)"
        ),
        "help_text": (
            "₹10,000 se kam pension wale retired employees ko PM Kisan "
            "mil sakta hai. ₹10,000 ya zyada wale nahi le sakte."
        ),
        "input_type": "number",
        "skip_ok": True,
        # Only ask retired govt employees
        "condition": lambda p: p.get("is_serving_or_retired_govt_employee") is True,
    },
    {
        "field": "is_or_was_elected_representative",
        "block": 6,
        "text": (
            "Kya aap kabhi bhi MP, MLA, MLC, ya "
            "Zila Panchayat President/Mayor rahe hain?\n"
            "  (Chahe abhi nahi hain — pehle bhi tha toh bhi bataiye)\n"
            "  (haan/nahi)"
        ),
        "help_text": (
            "Purane aur current elected representatives ko PM Kisan "
            "nahi milta. Yeh rule bahut log nahi jaante."
        ),
        "input_type": "yes_no",
        "skip_ok": True,
        "condition": None,
    },
]

# Derived: field → question dict for O(1) lookup
_FIELD_TO_QUESTION: dict[str, dict] = {q["field"]: q for q in QUESTION_BANK}


# =============================================================================
# SECTION 2 — NATURAL LANGUAGE PARSER
# =============================================================================

# Hindi number words → integer
_HINDI_NUMBERS: dict[str, int] = {
    "ek": 1, "do": 2, "teen": 3, "char": 4, "paanch": 5,
    "chhe": 6, "saat": 7, "aath": 8, "nau": 9, "das": 10,
    "gyarah": 11, "barah": 12, "terah": 13, "chaudah": 14,
    "pandrah": 15, "solah": 16, "satrah": 17, "atharah": 18,
    "unnees": 19, "bees": 20, "tees": 30, "chaalees": 40,
    "pachaas": 50, "saath": 60, "sattar": 70, "assi": 80,
    "nabbe": 90, "sau": 100,
    "pachas": 50, "saathi": 60,  # alternate spellings
}

# Multiplier words for income parsing
_MULTIPLIERS: dict[str, int] = {
    "hazaar": 1_000, "hazar": 1_000, "thousand": 1_000,
    "lakh": 100_000, "lac": 100_000, "lakhs": 100_000,
    "crore": 10_000_000, "cr": 10_000_000,
}

# State name normalization — common inputs → canonical name
_STATE_ALIASES: dict[str, str] = {
    "up": "Uttar Pradesh", "uttar pradesh": "Uttar Pradesh",
    "u.p.": "Uttar Pradesh", "yoogi": "Uttar Pradesh",
    "mp": "Madhya Pradesh", "madhya pradesh": "Madhya Pradesh",
    "m.p.": "Madhya Pradesh",
    "maha": "Maharashtra", "maharashtra": "Maharashtra",
    "mumbai": "Maharashtra",
    "raj": "Rajasthan", "rajasthan": "Rajasthan",
    "bihar": "Bihar", "bih": "Bihar",
    "bengal": "West Bengal", "west bengal": "West Bengal",
    "wb": "West Bengal", "wb ": "West Bengal",
    "punjab": "Punjab", "pb": "Punjab",
    "haryana": "Haryana", "hr": "Haryana",
    "hp": "Himachal Pradesh", "himachal": "Himachal Pradesh",
    "himachal pradesh": "Himachal Pradesh",
    "uk": "Uttarakhand", "uttarakhand": "Uttarakhand",
    "uttaranchal": "Uttarakhand",
    "jharkhand": "Jharkhand", "jh": "Jharkhand",
    "chhattisgarh": "Chhattisgarh", "cg": "Chhattisgarh",
    "odisha": "Odisha", "orissa": "Odisha",
    "gujarat": "Gujarat", "guj": "Gujarat",
    "karnataka": "Karnataka", "ktk": "Karnataka",
    "kerala": "Kerala", "kl": "Kerala",
    "tn": "Tamil Nadu", "tamil nadu": "Tamil Nadu",
    "ap": "Andhra Pradesh", "andhra": "Andhra Pradesh",
    "andhra pradesh": "Andhra Pradesh",
    "telangana": "Telangana", "ts": "Telangana",
    "assam": "Assam", "as": "Assam",
    "manipur": "Manipur", "mn": "Manipur",
    "meghalaya": "Meghalaya", "ml": "Meghalaya",
    "mizoram": "Mizoram", "mz": "Mizoram",
    "nagaland": "Nagaland", "nl": "Nagaland",
    "tripura": "Tripura", "tr": "Tripura",
    "arunachal": "Arunachal Pradesh",
    "arunachal pradesh": "Arunachal Pradesh",
    "sikkim": "Sikkim", "sk": "Sikkim",
    "goa": "Goa",
    "jk": "Jammu and Kashmir", "j&k": "Jammu and Kashmir",
    "jammu": "Jammu and Kashmir",
    "jammu and kashmir": "Jammu and Kashmir",
    "ladakh": "Ladakh",
    "delhi": "Delhi", "ncr": "Delhi", "new delhi": "Delhi",
    "chandigarh": "Chandigarh",
    "puducherry": "Puducherry", "pondicherry": "Puducherry",
    "andaman": "Andaman and Nicobar Islands",
    "lakshadweep": "Lakshadweep",
    "daman": "Dadra and Nagar Haveli and Daman and Diu",
}

# Positive yes patterns
_YES_PATTERNS = re.compile(
    r"\b(haan|ha|yes|bilkul|zaroor|theek|theek hai|sahi|correct|"
    r"right|true|ho|ji|ji haan|ha ji|ok|okay|hahn|han)\b",
    re.IGNORECASE
)

# Negative no patterns
_NO_PATTERNS = re.compile(
    r"\b(nahi|no|nope|nahin|na|false|nai|na ji|nhin|nhii|"
    r"nahi hai|nahi hoga|nahi tha)\b",
    re.IGNORECASE
)


def _extract_number_from_text(text: str) -> float | None:
    """
    Extract a numeric value from messy text.
    Handles: '45', 'pachaas', '45 saal', '2.5'.
    Returns None if no number found.
    """
    text_lower = text.lower().strip()

    # Direct float/int
    match = re.search(r"\b(\d+(?:\.\d+)?)\b", text_lower)
    if match:
        return float(match.group(1))

    # Hindi number words
    for word, val in sorted(_HINDI_NUMBERS.items(), key=lambda x: -len(x[0])):
        if word in text_lower:
            return float(val)

    return None


def _parse_income(text: str) -> dict:
    """
    Parse income from natural language into annual INR.

    Handles:
      '15 hazaar mahine ka'   → 180000
      '2 lakh saal ka'        → 200000
      '300 roz'               → 109500
      'din ka 200'            → 73000
      'do-teen lakh'          → needs clarification
    """
    text_lower = text.lower().strip()

    # Detect range input — needs clarification
    range_patterns = [
        r"(\d+)\s*[-–to]\s*(\d+)",
        r"do.?teen", r"2.?3", r"teen.?char",
        r"lagbhag|roughly|almost|around|approx",
    ]
    for pat in range_patterns[:3]:
        if re.search(pat, text_lower):
            return {
                "parsed_value": None,
                "confidence": "low",
                "raw_input": text,
                "needs_clarification": True,
                "clarification_prompt": (
                    "Aapne range batai — thoda aur specific batayein?\n"
                    "Jaise: '1.5 lakh' ya '50 hazaar' — rough bhi chalega."
                ),
            }

    # Extract base number
    base = _extract_number_from_text(text_lower)
    if base is None:
        return {
            "parsed_value": None,
            "confidence": "low",
            "raw_input": text,
            "needs_clarification": True,
            "clarification_prompt": (
                "Samjha nahi — kya aap dubara bata sakte hain?\n"
                "Jaise: '10 hazaar mahine' ya '1 lakh saal ka'"
            ),
        }

    # Apply multipliers
    for word, mult in _MULTIPLIERS.items():
        if word in text_lower:
            base *= mult
            break

    # Apply time period
    if any(w in text_lower for w in ["mahine", "month", "monthly", "per month", "mah"]):
        base *= 12
    elif any(w in text_lower for w in ["roz", "din", "daily", "per day", "dihadi"]):
        base *= 365
    elif any(w in text_lower for w in ["hafte", "week", "weekly"]):
        base *= 52
    # If 'saal' or 'year' or nothing → keep as annual

    return {
        "parsed_value": int(base),
        "confidence": "medium",
        "raw_input": text,
        "needs_clarification": False,
        "clarification_prompt": None,
    }


def _parse_area(text: str, state: str = "") -> dict:
    """
    Parse land area into hectares.

    Bigha conversion note: bigha varies by state.
      UP/Bihar/Rajasthan: 1 bigha ≈ 0.2529 ha
      Punjab/Haryana: 1 bigha ≈ 0.0529 ha  (much smaller!)
      Bengal: 1 bigha ≈ 0.1338 ha
      We use 0.25 ha as a conservative middle estimate
      and flag the uncertainty explicitly.
    """
    text_lower = text.lower().strip()
    base = _extract_number_from_text(text_lower)

    if base is None:
        return {
            "parsed_value": None,
            "confidence": "low",
            "raw_input": text,
            "needs_clarification": True,
            "clarification_prompt": (
                "Kitni zameen hai — thoda aur clearly batayein?\n"
                "Jaise: '2 bigha', '1 acre', '0.5 hectare'"
            ),
        }

    hectares = base  # default: assume hectares
    unit_note = ""
    confidence = "high"

    if "bigha" in text_lower:
        # Use 0.25 ha per bigha as approximation; flag state dependency
        hectares = base * 0.25
        unit_note = (
            f"⚠ Bigha ka size state se state alag hota hai. "
            f"{base} bigha ≈ {hectares:.2f} hectare use kar rahe hain "
            f"(rough estimate)."
        )
        confidence = "medium"
    elif "acre" in text_lower:
        hectares = base * 0.4047
    elif "gaj" in text_lower or "sq yard" in text_lower:
        hectares = base * 0.000836127
        confidence = "medium"
    elif "hectare" in text_lower or "ha" in text_lower:
        hectares = base

    return {
        "parsed_value": round(hectares, 3),
        "confidence": confidence,
        "raw_input": text,
        "needs_clarification": False,
        "clarification_prompt": None,
        "unit_note": unit_note,
    }


def parse_natural_language(
    user_input: str,
    field_being_asked: str,
    state: str = "",
) -> dict:
    """
    Parse raw user text into a structured value for the given field.

    This function never raises an exception. All failure modes return
    a result with needs_clarification=True so the conversation loop
    can handle them gracefully.

    The function is field-aware — 'haan' means different things
    for 'is_farmer' (True) vs 'age' (nothing useful).

    Parameters
    ----------
    user_input : str
        Raw text from the user.
    field_being_asked : str
        The profile field being collected — drives parsing strategy.
    state : str
        User's state, used for bigha conversion.

    Returns
    -------
    dict with: parsed_value, confidence, raw_input,
               needs_clarification, clarification_prompt
    """
    raw = user_input.strip()
    raw_lower = raw.lower()

    if not raw:
        return {
            "parsed_value": None,
            "confidence": "low",
            "raw_input": raw,
            "needs_clarification": True,
            "clarification_prompt": "Kuch toh bataiye — khaali nahi chhod sakte.",
        }

    # ------------------------------------------------------------------
    # Skip / back / help / result — handled by the conversation loop,
    # but we let them pass through here as well so the loop can intercept.
    # ------------------------------------------------------------------
    if raw_lower in ("skip", "aage", "next", "chodo", "chhodo"):
        return {
            "parsed_value": None,
            "confidence": "skipped",
            "raw_input": raw,
            "needs_clarification": False,
            "clarification_prompt": None,
        }

    # ------------------------------------------------------------------
    # YES/NO fields
    # ------------------------------------------------------------------
    yes_no_fields = {
        "is_indian_citizen", "owns_agricultural_land", "land_is_cultivable",
        "has_pucca_house_anywhere_in_india", "has_aadhaar", "has_bpl_card",
        "filed_income_tax_last_assessment_year", "is_farmer", "is_street_vendor",
        "is_serving_or_retired_govt_employee", "is_or_was_elected_representative",
        "is_pregnant_or_lactating", "num_girls_under_10",
    }

    if field_being_asked in yes_no_fields:
        # Check for number of girls sub-case
        if field_being_asked == "num_girls_under_10":
            num = _extract_number_from_text(raw_lower)
            if num is not None and num > 0:
                return {
                    "parsed_value": int(num),
                    "confidence": "high",
                    "raw_input": raw,
                    "needs_clarification": False,
                    "clarification_prompt": None,
                }

        if _YES_PATTERNS.search(raw_lower):
            return {
                "parsed_value": True,
                "confidence": "high",
                "raw_input": raw,
                "needs_clarification": False,
                "clarification_prompt": None,
            }
        if _NO_PATTERNS.search(raw_lower):
            return {
                "parsed_value": False,
                "confidence": "high",
                "raw_input": raw,
                "needs_clarification": False,
                "clarification_prompt": None,
            }
        # Ambiguous
        return {
            "parsed_value": None,
            "confidence": "low",
            "raw_input": raw,
            "needs_clarification": True,
            "clarification_prompt": (
                "Samjha nahi — 'haan' ya 'nahi' mein bataiye?"
            ),
        }

    # ------------------------------------------------------------------
    # AGE
    # ------------------------------------------------------------------
    if field_being_asked == "age":
        num = _extract_number_from_text(raw_lower)
        if num and 0 < num < 120:
            return {
                "parsed_value": int(num),
                "confidence": "high",
                "raw_input": raw,
                "needs_clarification": False,
                "clarification_prompt": None,
            }
        return {
            "parsed_value": None,
            "confidence": "low",
            "raw_input": raw,
            "needs_clarification": True,
            "clarification_prompt": "Umar number mein likhiye — jaise: 35",
        }

    # ------------------------------------------------------------------
    # INCOME
    # ------------------------------------------------------------------
    if field_being_asked == "annual_household_income_inr":
        # "pata nahi" / "don't know" → skip gracefully
        if any(w in raw_lower for w in ["pata nahi", "don't know", "dont know", "nahi pata"]):
            return {
                "parsed_value": None,
                "confidence": "skipped",
                "raw_input": raw,
                "needs_clarification": False,
                "clarification_prompt": None,
            }
        return _parse_income(raw)

    # ------------------------------------------------------------------
    # LAND AREA
    # ------------------------------------------------------------------
    if field_being_asked == "land_area_hectares":
        return _parse_area(raw, state)

    # ------------------------------------------------------------------
    # MONTHLY PENSION
    # ------------------------------------------------------------------
    if field_being_asked == "monthly_pension_if_retired_govt":
        num = _extract_number_from_text(raw_lower)
        for word, mult in _MULTIPLIERS.items():
            if word in raw_lower:
                num = (num or 1) * mult
                break
        if num is not None:
            return {
                "parsed_value": int(num),
                "confidence": "high",
                "raw_input": raw,
                "needs_clarification": False,
                "clarification_prompt": None,
            }
        return {
            "parsed_value": None,
            "confidence": "low",
            "raw_input": raw,
            "needs_clarification": True,
            "clarification_prompt": "Pension amount number mein likhiye — jaise: 8500",
        }

    # ------------------------------------------------------------------
    # FAMILY SIZE
    # ------------------------------------------------------------------
    if field_being_asked == "family_size":
        num = _extract_number_from_text(raw_lower)
        if num and 1 <= num <= 30:
            return {
                "parsed_value": int(num),
                "confidence": "high",
                "raw_input": raw,
                "needs_clarification": False,
                "clarification_prompt": None,
            }
        return {
            "parsed_value": None,
            "confidence": "low",
            "raw_input": raw,
            "needs_clarification": True,
            "clarification_prompt": "Ghar mein kitne log hain — number likhiye",
        }

    # ------------------------------------------------------------------
    # GENDER
    # ------------------------------------------------------------------
    if field_being_asked == "gender":
        male_words = r"\b(mard|ladka|male|man|purush|gent|m|bhai)\b"
        female_words = r"\b(aurat|mahila|female|woman|stree|lady|f)\b"
        trans_words = r"\b(transgender|kinnar|hijra|third gender)\b"
        if re.search(male_words, raw_lower):
            return {
                "parsed_value": "male",
                "confidence": "high",
                "raw_input": raw,
                "needs_clarification": False,
                "clarification_prompt": None,
            }
        if re.search(female_words, raw_lower):
            return {
                "parsed_value": "female",
                "confidence": "high",
                "raw_input": raw,
                "needs_clarification": False,
                "clarification_prompt": None,
            }
        if re.search(trans_words, raw_lower):
            return {
                "parsed_value": "transgender",
                "confidence": "high",
                "raw_input": raw,
                "needs_clarification": False,
                "clarification_prompt": None,
            }
        return {
            "parsed_value": None,
            "confidence": "low",
            "raw_input": raw,
            "needs_clarification": True,
            "clarification_prompt": "Mard, aurat ya transgender — kaunsa sahi hai?",
        }

    # ------------------------------------------------------------------
    # CASTE CATEGORY
    # ------------------------------------------------------------------
    if field_being_asked == "caste_category":
        if re.search(r"\b(general|open|unreserved|samanya|savarna|1)\b", raw_lower):
            return {"parsed_value": "general", "confidence": "high",
                    "raw_input": raw, "needs_clarification": False,
                    "clarification_prompt": None}
        if re.search(r"\b(obc|pichda|backward|2)\b", raw_lower):
            return {"parsed_value": "obc", "confidence": "high",
                    "raw_input": raw, "needs_clarification": False,
                    "clarification_prompt": None}
        if re.search(r"\b(sc|dalit|scheduled caste|harijan|3)\b", raw_lower):
            return {"parsed_value": "sc", "confidence": "high",
                    "raw_input": raw, "needs_clarification": False,
                    "clarification_prompt": None}
        if re.search(r"\b(st|adivasi|tribal|scheduled tribe|4)\b", raw_lower):
            return {"parsed_value": "st", "confidence": "high",
                    "raw_input": raw, "needs_clarification": False,
                    "clarification_prompt": None}
        return {
            "parsed_value": None,
            "confidence": "low",
            "raw_input": raw,
            "needs_clarification": True,
            "clarification_prompt": (
                "Category number ya naam likhiye:\n"
                "  1. General  2. OBC  3. SC  4. ST"
            ),
        }

    # ------------------------------------------------------------------
    # RESIDENCE TYPE
    # ------------------------------------------------------------------
    if field_being_asked == "residence_type":
        if re.search(r"\b(gaon|rural|village|gram|gramin|dehat)\b", raw_lower):
            return {"parsed_value": "rural", "confidence": "high",
                    "raw_input": raw, "needs_clarification": False,
                    "clarification_prompt": None}
        if re.search(r"\b(sheher|urban|city|town|shahar|nagar)\b", raw_lower):
            return {"parsed_value": "urban", "confidence": "high",
                    "raw_input": raw, "needs_clarification": False,
                    "clarification_prompt": None}
        return {
            "parsed_value": None,
            "confidence": "low",
            "raw_input": raw,
            "needs_clarification": True,
            "clarification_prompt": "Gaon ya sheher — kaunsa sahi hai?",
        }

    # ------------------------------------------------------------------
    # STATE
    # ------------------------------------------------------------------
    if field_being_asked == "state":
        normalized = _STATE_ALIASES.get(raw_lower.strip())
        if normalized:
            return {"parsed_value": normalized, "confidence": "high",
                    "raw_input": raw, "needs_clarification": False,
                    "clarification_prompt": None}
        # Try partial match
        for alias, canonical in _STATE_ALIASES.items():
            if alias in raw_lower:
                return {"parsed_value": canonical, "confidence": "medium",
                        "raw_input": raw, "needs_clarification": False,
                        "clarification_prompt": None}
        # Use raw as-is with title case
        return {
            "parsed_value": raw.strip().title(),
            "confidence": "medium",
            "raw_input": raw,
            "needs_clarification": False,
            "clarification_prompt": None,
        }

    # ------------------------------------------------------------------
    # HOUSING STATUS
    # ------------------------------------------------------------------
    if field_being_asked == "housing_status":
        if re.search(r"\b(pucca|pakka|cement|brick|1)\b", raw_lower):
            return {"parsed_value": "pucca", "confidence": "high",
                    "raw_input": raw, "needs_clarification": False,
                    "clarification_prompt": None}
        if re.search(r"\b(semi|adha|2)\b", raw_lower):
            return {"parsed_value": "semi_pucca", "confidence": "high",
                    "raw_input": raw, "needs_clarification": False,
                    "clarification_prompt": None}
        if re.search(r"\b(kachcha|kutcha|kacha|mitti|bambu|bamboo|3)\b", raw_lower):
            return {"parsed_value": "kutcha", "confidence": "high",
                    "raw_input": raw, "needs_clarification": False,
                    "clarification_prompt": None}
        if re.search(r"\b(homeless|ghar nahi|koi ghar|4)\b", raw_lower):
            return {"parsed_value": "homeless", "confidence": "high",
                    "raw_input": raw, "needs_clarification": False,
                    "clarification_prompt": None}
        if re.search(r"\b(rented|kiraya|5)\b", raw_lower):
            return {"parsed_value": "rented", "confidence": "high",
                    "raw_input": raw, "needs_clarification": False,
                    "clarification_prompt": None}
        return {
            "parsed_value": None,
            "confidence": "low",
            "raw_input": raw,
            "needs_clarification": True,
            "clarification_prompt": "Number likhiye: 1.Pucca 2.Semi 3.Kutcha 4.Homeless 5.Rented",
        }

    # ------------------------------------------------------------------
    # BANK ACCOUNT STATUS
    # ------------------------------------------------------------------
    if field_being_asked == "bank_account_status":
        if re.search(r"\b(1|linked|dbt|aadhar linked)\b", raw_lower):
            return {"parsed_value": "active_with_dbt", "confidence": "high",
                    "raw_input": raw, "needs_clarification": False,
                    "clarification_prompt": None}
        if re.search(r"\b(2|not linked|bina link)\b", raw_lower):
            return {"parsed_value": "active_no_dbt", "confidence": "high",
                    "raw_input": raw, "needs_clarification": False,
                    "clarification_prompt": None}
        if re.search(r"\b(3|jan dhan|jandhan|jandhan)\b", raw_lower):
            return {"parsed_value": "jan_dhan", "confidence": "high",
                    "raw_input": raw, "needs_clarification": False,
                    "clarification_prompt": None}
        if re.search(r"\b(4|nahi|no|none|koi nahi)\b", raw_lower):
            return {"parsed_value": "none", "confidence": "high",
                    "raw_input": raw, "needs_clarification": False,
                    "clarification_prompt": None}
        # haan/nahi fallback
        if _YES_PATTERNS.search(raw_lower):
            return {"parsed_value": "active_no_dbt", "confidence": "medium",
                    "raw_input": raw, "needs_clarification": False,
                    "clarification_prompt": None}
        if _NO_PATTERNS.search(raw_lower):
            return {"parsed_value": "none", "confidence": "high",
                    "raw_input": raw, "needs_clarification": False,
                    "clarification_prompt": None}
        return {
            "parsed_value": None,
            "confidence": "low",
            "raw_input": raw,
            "needs_clarification": True,
            "clarification_prompt": "Number likhiye: 1 / 2 / 3 / 4",
        }

    # ------------------------------------------------------------------
    # LAND OWNERSHIP TYPE
    # ------------------------------------------------------------------
    if field_being_asked == "land_ownership_type":
        if re.search(r"\b(individual|sirf mera|akela|khud|1)\b", raw_lower):
            return {"parsed_value": "individual", "confidence": "high",
                    "raw_input": raw, "needs_clarification": False,
                    "clarification_prompt": None}
        if re.search(r"\b(joint|mila|sanjha|family|2)\b", raw_lower):
            return {"parsed_value": "joint", "confidence": "high",
                    "raw_input": raw, "needs_clarification": False,
                    "clarification_prompt": None}
        if re.search(r"\b(institutional|cooperative|society|3)\b", raw_lower):
            return {"parsed_value": "institutional", "confidence": "high",
                    "raw_input": raw, "needs_clarification": False,
                    "clarification_prompt": None}
        return {
            "parsed_value": None,
            "confidence": "low",
            "raw_input": raw,
            "needs_clarification": True,
            "clarification_prompt": "Number likhiye: 1.Individual  2.Joint  3.Institutional",
        }

    # ------------------------------------------------------------------
    # Fallback — return as-is with medium confidence
    # ------------------------------------------------------------------
    return {
        "parsed_value": raw,
        "confidence": "medium",
        "raw_input": raw,
        "needs_clarification": False,
        "clarification_prompt": None,
    }


# =============================================================================
# SECTION 3 — CONTRADICTION DETECTOR
# =============================================================================

def detect_contradiction(
    profile_so_far: dict,
    new_field: str,
    new_value: Any,
) -> dict:
    """
    Check whether adding new_field=new_value contradicts anything
    already collected in profile_so_far.

    Design: contradictions are surfaced as warnings, not hard blocks.
    The user gets an explanation and a chance to correct either answer.
    We never silently override what the user said.

    Returns
    -------
    dict with:
        has_contradiction : bool
        contradiction_description : str  (shown to user)
        suggested_clarification   : str  (what to ask)
    """
    NO_CONTRADICTION = {
        "has_contradiction": False,
        "contradiction_description": "",
        "suggested_clarification": "",
    }

    age = profile_so_far.get("age") or (
        new_value if new_field == "age" else None
    )
    income = profile_so_far.get("annual_household_income_inr") or (
        new_value if new_field == "annual_household_income_inr" else None
    )

    # 1. Age < 18 AND married / pregnant
    if new_field in ("is_pregnant_or_lactating",) and new_value is True:
        if age is not None and age < 18:
            return {
                "has_contradiction": True,
                "contradiction_description": (
                    f"Aapki umar {age} saal hai — kya aap sach mein "
                    f"pregnant hain? Hum sahi information chahte hain."
                ),
                "suggested_clarification": (
                    "Kya aapki umar sahi di thi? Ya pregnancy ki "
                    "information dobara confirm karein."
                ),
            }

    # 2. Rural + street vendor
    if new_field == "is_street_vendor" and new_value is True:
        if profile_so_far.get("residence_type") == "rural":
            return {
                "has_contradiction": True,
                "contradiction_description": (
                    "PM SVANidhi sirf urban (sheher ke) vendors ke liye hai. "
                    "Aapne pehle bola ki aap gaon mein rehte hain."
                ),
                "suggested_clarification": (
                    "Kya aap gaon mein rehte hain ya sheher mein? "
                    "Agar sheher mein hain toh residence dobara batayein."
                ),
            }

    # 3. Farmer + no land ownership
    if new_field == "owns_agricultural_land" and new_value is False:
        if profile_so_far.get("is_farmer") is True:
            return {
                "has_contradiction": True,
                "contradiction_description": (
                    "Aapne bola aap farmer hain, lekin zameen aapke naam "
                    "pe nahi hai. Yeh ho sakta hai — kai log leased zameen "
                    "pe kheti karte hain."
                ),
                "suggested_clarification": (
                    "Kya aap kisi aur ki zameen pe kheti karte hain "
                    "(leased/batai)? PM Kisan ke liye KHUD ki zameen "
                    "zaroori hai — lekin MGNREGA mil sakta hai."
                ),
            }

    # 4. Filed income tax + income < 2.5L
    if new_field == "filed_income_tax_last_assessment_year" and new_value is True:
        if income is not None and income < 250_000:
            return {
                "has_contradiction": True,
                "contradiction_description": (
                    f"Aapne bola income ₹{income:,.0f}/saal hai, "
                    f"lekin income tax bhi bharte hain. "
                    f"₹2.5 lakh se kam income pe tax nahi lagta."
                ),
                "suggested_clarification": (
                    "Kya income tax wali baat sahi hai? "
                    "Ya income amount mein koi galti hui?"
                ),
            }

    # 5. Age > 59 AND serving govt employee
    if new_field == "is_serving_or_retired_govt_employee" and new_value is True:
        if age is not None and age > 59:
            return {
                "has_contradiction": True,
                "contradiction_description": (
                    f"Aapki umar {age} saal hai — kya aap abhi bhi "
                    f"government job mein kaam kar rahe hain, "
                    f"ya retire ho gaye hain?"
                ),
                "suggested_clarification": (
                    "Agar retire ho gaye hain toh pension amount "
                    "zaroor batayein — PM Kisan eligibility ke liye important hai."
                ),
            }

    # 6. Has pucca house + applying for housing scheme
    if new_field == "has_pucca_house_anywhere_in_india" and new_value is True:
        if profile_so_far.get("housing_status") in ("kutcha", "semi_pucca"):
            return {
                "has_contradiction": True,
                "contradiction_description": (
                    "Aapne bola ghar kutcha/semi-pucca hai, lekin "
                    "kahin aur pucca ghar bhi hai. Dono sach ho sakte hain."
                ),
                "suggested_clarification": (
                    "PMAY ke liye: agar KAHIN BHI pucca ghar hai — "
                    "chahe gaon mein, chahe sheher mein — toh PMAY "
                    "nahi milega. Yeh confirm karo."
                ),
            }

    # 7. No Aadhaar — warn that many schemes blocked
    if new_field == "has_aadhaar" and new_value is False:
        return {
            "has_contradiction": True,  # not a contradiction but a critical warning
            "contradiction_description": (
                "⚠ Aadhaar nahi hai — zyaadatar government schemes "
                "ke liye Aadhaar ZAROORI hai."
            ),
            "suggested_clarification": (
                "Sabse pehle nearest Aadhaar Seva Kendra jaiye. "
                "Free mein banta hai. Baad mein baki schemes apply kar sakte hain. "
                "Hum abhi bhi match kar ke batate hain — kuch schemes "
                "Aadhaar ke bina bhi apply ho sakti hain."
            ),
        }

    return NO_CONTRADICTION


# =============================================================================
# SECTION 4 — MAIN CONVERSATION LOOP
# =============================================================================

def _c(text: str, color: str) -> str:
    """Apply color if available."""
    return f"{color}{text}{Style.RESET_ALL}" if _COLOR else text


def _print_section(title: str) -> None:
    print()
    print(_c(f"  {'─' * 60}", Fore.CYAN))
    print(_c(f"  {title}", Fore.CYAN))
    print(_c(f"  {'─' * 60}", Fore.CYAN))


def _print_warning(text: str) -> None:
    print(_c(f"\n  ⚠ {text}", Fore.YELLOW))


def _print_error(text: str) -> None:
    print(_c(f"\n  ✗ {text}", Fore.RED))


def _print_success(text: str) -> None:
    print(_c(f"\n  ✓ {text}", Fore.GREEN))


def _prompt(question_text: str) -> str:
    """Display question and get user input. Never crashes."""
    print()
    print(_c("  " + question_text.replace("\n", "\n  "), Fore.WHITE))
    try:
        raw = input(_c("  ❯ ", Fore.CYAN)).strip()
        return raw
    except (EOFError, KeyboardInterrupt):
        print("\n\n  Alvida! KALAM se dobara baat kar sakte hain.")
        sys.exit(0)


def _show_partial_results(profile: dict, questions_remaining: int) -> None:
    """
    Run match_schemes on whatever profile exists so far and display
    with a clear "incomplete" warning.
    """
    if not profile:
        print(_c("\n  Abhi koi data nahi diya — pehle kuch sawal poochhne hain.", Fore.YELLOW))
        return

    print()
    print(_c(
        f"  ⚠ PARTIAL RESULTS — {questions_remaining} sawal abhi baaki hain.\n"
        f"  Yeh results incomplete hain aur baad mein change ho sakte hain.",
        Fore.YELLOW
    ))

    results = match_schemes(profile)
    print_results(results, "Aapka Abhi Tak Ka Profile (Adhura)")

    # Show what's missing
    gaps = results.get("data_gaps_summary", [])
    if gaps:
        print(_c("\n  📋 Yeh fields provide karein toh results behtar honge:", Fore.CYAN))
        for g in gaps[:4]:
            print(f"     • {g[:100]}")


def _build_next_steps(results: dict) -> str:
    """
    Build a Hinglish next-steps summary from match results.
    Concise, actionable, in the voice of a helpful guide.
    """
    fully = results.get("fully_eligible", [])
    partial = results.get("partially_eligible", [])
    seq = results.get("application_sequence", [])

    lines = ["📋 AAPKE LIYE NEXT STEPS:", "─" * 40]
    step_num = 1

    # Jan Dhan first if bank account missing
    profile_note = ""
    for s in fully + partial:
        if "jan_dhan_or_active_bank_account" in s.get("missing_documents", []):
            lines.append(
                f"  {step_num}. 🏦 Jan Dhan account ke liye nearest bank branch "
                f"jaiye — Aadhaar card lekar. Bilkul free hai."
            )
            step_num += 1
            break

    # Application sequence
    from schemes_database import SCHEMES
    shown = set()
    for sid in seq[:5]:
        if sid.startswith("[") or sid in shown:
            continue
        shown.add(sid)
        scheme = SCHEMES.get(sid, {})
        url = scheme.get("application_url", "")
        helpline = scheme.get("helpline", "")
        name = scheme.get("name", sid)

        line = f"  {step_num}. 📝 {name}"
        if url:
            line += f"\n       Website: {url}"
        if helpline:
            line += f"\n       Helpline: {helpline}"
        lines.append(line)
        step_num += 1

    if not fully and not partial:
        lines.append(
            "  Abhi koi scheme fully match nahi hua. "
            "Zyada information provide karke dobara try karein."
        )

    lines.append("")
    lines.append("  Koi bhi sawal ho toh KALAM se dobara baat karein.")
    lines.append("  National Helpline: 1800-111-555")

    return "\n".join(lines)


def run_conversation() -> dict:
    """
    Run the full Hinglish intake interview.

    State machine:
      GREETING → BLOCK_1 → BLOCK_2 → ... → RESULTS

    Special commands (always available):
      'skip'    → skip current question
      'back'    → go to previous question
      'result'  → show partial results now
      'help'    → explain why this question is asked
      'quit'    → exit

    Returns the completed user_profile dict.
    """

    # ------------------------------------------------------------------
    # GREETING
    # ------------------------------------------------------------------
    print()
    print(_c("  " + "═" * 60, Fore.CYAN))
    print(_c("  KALAM — Aapka Sarkaari Yojana Saathi", Fore.CYAN))
    print(_c("  " + "═" * 60, Fore.CYAN))
    print()
    print("  Namaste! Main KALAM hoon — aapka sarkaari yojana saathi.")
    print()
    print("  Main aapse kuch sawal poochunga aur bataunga ki")
    print("  aap kaunsi government schemes ke liye eligible hain.")
    print()
    print("  Yeh bilkul FREE hai. Koi form nahi. Bas baat karo.")
    print()
    print(_c("  Tips:", Fore.YELLOW))
    print("   • 'skip'   — sawal chhod dein")
    print("   • 'back'   — pichla sawal")
    print("   • 'result' — abhi tak ke results dekhein")
    print("   • 'help'   — yeh sawal kyun pooch rahe hain")
    print()

    start = _prompt("Shuru karte hain? (haan/nahi)")
    if _NO_PATTERNS.search(start.lower()):
        print("\n  Theek hai! Jab chahein tab wapas aayein. Namaste! 🙏")
        return {}

    # ------------------------------------------------------------------
    # INTERVIEW LOOP
    # ------------------------------------------------------------------
    profile: dict[str, Any] = {}
    history: list[str] = []  # list of fields answered, for 'back'
    question_index = 0
    max_clarification_attempts = 3

    while question_index < len(QUESTION_BANK):
        q = QUESTION_BANK[question_index]
        field = q["field"]
        condition = q.get("condition")

        # Check conditional skip
        if condition is not None:
            try:
                if not condition(profile):
                    question_index += 1
                    continue
            except Exception:
                question_index += 1
                continue

        # Show block header
        current_block = q.get("block", 0)
        prev_block = (
            QUESTION_BANK[question_index - 1].get("block", 0)
            if question_index > 0 else 0
        )
        if current_block != prev_block:
            block_names = {
                1: "BLOCK 1 — Aapke Baare Mein",
                2: "BLOCK 2 — Ghar Ki Amdani",
                3: "BLOCK 3 — Zameen Aur Ghar",
                4: "BLOCK 4 — Zaroor i Documents",
                5: "BLOCK 5 — Parivar",
                6: "BLOCK 6 — Kaam-Kaaj",
            }
            _print_section(block_names.get(current_block, f"Block {current_block}"))

        # Ask with clarification retry loop
        attempts = 0
        answered = False

        while attempts < max_clarification_attempts and not answered:
            raw_input_str = _prompt(q["text"])
            raw_lower = raw_input_str.lower().strip()

            # Special commands
            if raw_lower in ("quit", "exit", "bye", "alvida"):
                print("\n  Namaste! Dobara aayein. 🙏")
                return profile

            if raw_lower in ("help", "kyun", "why", "explain"):
                print()
                print(_c("  ℹ " + q["help_text"], Fore.CYAN))
                continue  # re-ask same question

            if raw_lower in ("back", "pichla", "wapas"):
                if history:
                    prev_field = history.pop()
                    # Find previous question index
                    for i, pq in enumerate(QUESTION_BANK):
                        if pq["field"] == prev_field:
                            question_index = i
                            profile.pop(prev_field, None)
                            print(_c(
                                f"  ← Pichle sawal par wapas ja rahe hain...",
                                Fore.YELLOW
                            ))
                            break
                    answered = True  # break inner loop; outer will handle
                else:
                    print(_c("  Yeh pehla sawal hai — aur peeche nahi ja sakte.", Fore.YELLOW))
                continue

            if raw_lower in ("result", "results", "abhi", "dikha"):
                remaining = sum(
                    1 for i in range(question_index, len(QUESTION_BANK))
                    if QUESTION_BANK[i].get("condition") is None
                    or QUESTION_BANK[i]["condition"](profile)
                )
                _show_partial_results(profile, remaining)
                continue

            if raw_lower in ("skip", "aage", "next", "chodo"):
                if q.get("skip_ok", True):
                    print(_c("  → Yeh sawal skip kar rahe hain.", Fore.YELLOW))
                    question_index += 1
                    answered = True
                else:
                    print(_c(
                        "  Yeh sawal skip nahi ho sakta — "
                        "matching ke liye zaroori hai.",
                        Fore.RED
                    ))
                continue

            # Parse the answer
            state_so_far = profile.get("state", "")
            parse_result = parse_natural_language(
                raw_input_str, field, state=state_so_far
            )

            if parse_result["confidence"] == "skipped":
                if q.get("skip_ok", True):
                    question_index += 1
                    answered = True
                else:
                    print(_c("  Yeh skip nahi ho sakta.", Fore.RED))
                continue

            if parse_result["needs_clarification"]:
                attempts += 1
                clarification = parse_result.get("clarification_prompt", "Dobara try karein.")
                print(_c(f"\n  Hmm... {clarification}", Fore.YELLOW))
                if attempts >= max_clarification_attempts:
                    print(_c(
                        "  Theek hai, is sawal ko skip kar rahe hain.",
                        Fore.YELLOW
                    ))
                    question_index += 1
                    answered = True
                continue

            parsed_value = parse_result["parsed_value"]

            # Show unit note if land area
            if "unit_note" in parse_result and parse_result["unit_note"]:
                print(_c(f"\n  {parse_result['unit_note']}", Fore.YELLOW))

            # Contradiction check
            contradiction = detect_contradiction(profile, field, parsed_value)
            if contradiction["has_contradiction"]:
                print()
                print(_c(
                    "  ⚠ " + contradiction["contradiction_description"],
                    Fore.YELLOW
                ))
                if contradiction["suggested_clarification"]:
                    print(_c(
                        "  → " + contradiction["suggested_clarification"],
                        Fore.CYAN
                    ))
                # Still accept the answer — don't block, just warn
                # The user might be correcting a previous wrong answer

            # Accept the answer
            profile[field] = parsed_value
            history.append(field)

            # Special case: num_girls_under_10 = True → set integer to 1 minimum
            if field == "num_girls_under_10" and parsed_value is True:
                profile[field] = 1  # at least 1 girl
                profile["has_girl_child_under_10"] = True
                profile["is_parent_or_legal_guardian"] = True
            elif field == "num_girls_under_10" and isinstance(parsed_value, int) and parsed_value > 0:
                profile["has_girl_child_under_10"] = True
                profile["is_parent_or_legal_guardian"] = True
            elif field == "num_girls_under_10" and parsed_value is False:
                profile["has_girl_child_under_10"] = False
                profile[field] = 0

            # Derive extra fields from answers
            _derive_extra_fields(profile, field, parsed_value)

            # Confirm
            confirmation = _format_confirmation(field, parsed_value)
            if confirmation:
                print(_c(f"  ✓ {confirmation}", Fore.GREEN))

            question_index += 1
            answered = True

    # ------------------------------------------------------------------
    # All questions done — run final match
    # ------------------------------------------------------------------
    print()
    print(_c("  " + "═" * 60, Fore.GREEN))
    print(_c("  Shukriya! Aapka profile complete hua. Results dekh rahe hain...", Fore.GREEN))
    print(_c("  " + "═" * 60, Fore.GREEN))
    print()

    results = match_schemes(profile)
    print_results(results, "AAPKA POORA RESULT")

    # ------------------------------------------------------------------
    # Exit summary
    # ------------------------------------------------------------------
    print()
    print(_c("  " + "═" * 60, Fore.CYAN))
    print(_c(_build_next_steps(results), Fore.WHITE))
    print(_c("  " + "═" * 60, Fore.CYAN))
    print()

    return profile


def _derive_extra_fields(profile: dict, field: str, value: Any) -> None:
    """
    Derive implicit profile fields from user answers.

    Examples:
    - bank_account_status = "none" → has_savings_bank_account = False
    - gender = "female" → is_male = False
    - is_serving_or_retired_govt_employee = False → pension = None
    """
    if field == "bank_account_status":
        if value == "none":
            profile["has_savings_bank_account"] = False
        else:
            profile["has_savings_bank_account"] = True
        if value == "active_with_dbt":
            profile["bank_account_linked_to_aadhaar"] = True

    if field == "gender":
        if value == "male":
            profile["is_pregnant_or_lactating"] = False

    if field == "is_serving_or_retired_govt_employee" and value is False:
        profile["monthly_pension_if_retired_govt"] = None
        profile["is_serving_central_or_state_govt_employee"] = False

    if field == "filed_income_tax_last_assessment_year":
        profile["filed_income_tax"] = value
        profile["is_income_taxpayer"] = value

    if field == "has_bpl_card" and value is True:
        profile["is_bpl_household"] = True
        profile["is_bpl_listed_or_destitute"] = True
        profile["is_bpl_listed_or_qualifying_category"] = True

    if field == "annual_household_income_inr":
        if value is not None:
            profile["is_bpl_listed_or_qualifying_category"] = (
                profile.get("is_bpl_listed_or_qualifying_category", False)
                or value <= 150000
            )

    if field == "is_or_was_elected_representative" and value is True:
        profile["is_current_constitutional_post_holder"] = False
        profile["is_former_constitutional_post_holder"] = False
        profile["is_current_minister"] = False
        profile["is_former_minister"] = False
        profile["is_current_mp_or_mla_or_mlc"] = True
        profile["is_former_mp_or_mla_or_mlc"] = True

    elif field == "is_or_was_elected_representative" and value is False:
        for sub in [
            "is_current_constitutional_post_holder",
            "is_former_constitutional_post_holder",
            "is_current_minister", "is_former_minister",
            "is_current_mp_or_mla_or_mlc", "is_former_mp_or_mla_or_mlc",
            "is_current_zila_panchayat_president_or_mayor",
        ]:
            profile[sub] = False

    if field == "is_farmer" and value is False:
        profile["is_agricultural_laborer"] = False

    if field == "is_serving_or_retired_govt_employee" and value is True:
        # Will ask pension next — set serving flag based on age
        age = profile.get("age", 0)
        if age < 60:
            profile["is_serving_central_or_state_govt_employee"] = True
        else:
            profile["is_serving_central_or_state_govt_employee"] = False


def _format_confirmation(field: str, value: Any) -> str:
    """Return a brief Hinglish confirmation string for the parsed answer."""
    confirmations = {
        "age": lambda v: f"Umar: {v} saal",
        "gender": lambda v: {
            "male": "Aap mard hain",
            "female": "Aap aurat hain",
            "transgender": "Transgender noted"
        }.get(str(v), f"Gender: {v}"),
        "state": lambda v: f"State: {v}",
        "residence_type": lambda v: "Gaon (Rural)" if v == "rural" else "Sheher (Urban)",
        "caste_category": lambda v: f"Category: {str(v).upper()}",
        "is_indian_citizen": lambda v: "Indian citizen: Haan" if v else "Indian citizen: Nahi",
        "annual_household_income_inr": lambda v: (
            f"Annual income: ₹{v:,.0f}" if v else "Income: Not provided"
        ),
        "has_bpl_card": lambda v: "BPL card: Haan" if v else "BPL card: Nahi",
        "owns_agricultural_land": lambda v: "Zameen: Haan" if v else "Zameen: Nahi",
        "land_area_hectares": lambda v: f"Zameen: {v} hectare",
        "has_aadhaar": lambda v: "Aadhaar: Haan ✓" if v else "Aadhaar: Nahi ⚠",
        "bank_account_status": lambda v: f"Bank account: {v}",
        "is_farmer": lambda v: "Farmer: Haan" if v else "Farmer: Nahi",
        "is_street_vendor": lambda v: "Street vendor: Haan" if v else "",
        "monthly_pension_if_retired_govt": lambda v: (
            f"Pension: ₹{v:,.0f}/month" if v else ""
        ),
    }
    fn = confirmations.get(field)
    if fn:
        try:
            return fn(value)
        except Exception:
            return ""
    return ""


# =============================================================================
# SECTION 5 — PARTIAL RESULTS HANDLER (standalone function)
# =============================================================================

def show_partial_match(profile: dict) -> dict:
    """
    Run match_schemes() on partial profile and return results
    with missing-field annotations.

    This is also exposed as a library function so external callers
    (e.g., a web frontend) can call it mid-session.
    """
    results = match_schemes(profile)

    # Count how many questions would still be asked
    answered_fields = set(profile.keys())
    remaining_questions = [
        q for q in QUESTION_BANK
        if q["field"] not in answered_fields
        and (q["condition"] is None or q["condition"](profile))
    ]

    results["_partial_session_meta"] = {
        "questions_answered": len(answered_fields),
        "questions_remaining": len(remaining_questions),
        "remaining_fields": [q["field"] for q in remaining_questions],
        "is_complete": len(remaining_questions) == 0,
    }
    return results


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    try:
        final_profile = run_conversation()
    except KeyboardInterrupt:
        print("\n\n  Alvida! KALAM se dobara baat kar sakte hain. 🙏")
        sys.exit(0)