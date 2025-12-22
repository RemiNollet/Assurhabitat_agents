import re
from typing import Dict, Tuple
from utils_scoring import text_similarity, list_similarity


def score_declaration(
    parsed_declaration: Dict,
    expected: Dict
) -> Tuple[float, Dict]:
    """
    Advanced scoring of declaration agent output.
    Returns:
        score (float between 0 and 1)
        details (dict explaining per-field scores)
    """

    weights = {
        "sinistre_type": 0.25,
        "date_sinistre": 0.15,
        "lieu": 0.15,
        "description": 0.20,
        "biens_impactes": 0.25,
    }

    details = {}
    total_score = 0.0

    output_extracted = parsed_declaration.get("extracted", {})
    expected_extracted = expected["parsed_declaration"]["extracted"]

    # ---- sinistre_type (exact match) ----
    st_score = 1.0 if parsed_declaration.get("sinistre_type") == expected["parsed_declaration"]["sinistre_type"] else 0.0
    total_score += st_score * weights["sinistre_type"]
    details["sinistre_type"] = st_score

    # ---- date_sinistre (exact or both None) ----
    out_date = output_extracted.get("date_sinistre")
    exp_date = expected_extracted.get("date_sinistre")
    date_score = 1.0 if out_date == exp_date else 0.0
    total_score += date_score * weights["date_sinistre"]
    details["date_sinistre"] = date_score

    # ---- lieu (text similarity) ----
    lieu_score = text_similarity(
        output_extracted.get("lieu", ""),
        expected_extracted.get("lieu", "")
    )
    total_score += lieu_score * weights["lieu"]
    details["lieu"] = round(lieu_score, 2)

    # ---- description (text similarity) ----
    desc_score = text_similarity(
        output_extracted.get("description", ""),
        expected_extracted.get("description", "")
    )
    total_score += desc_score * weights["description"]
    details["description"] = round(desc_score, 2)

    # ---- biens_impactes (list similarity) ----
    biens_score = list_similarity(
        output_extracted.get("biens_impactes", []),
        expected_extracted.get("biens_impactes", [])
    )
    total_score += biens_score * weights["biens_impactes"]
    details["biens_impactes"] = round(biens_score, 2)

    return round(total_score, 3), str(details)


def score_validation(output, expected):
    score = 1.0
    reasons = []

    if output["image_conformity"]["compatible"] != expected["image_conformity"]:
        score = 0.0
        reasons.append("image conformity mismatch")

    if output["guarantee_report"]["guaranteed"] != expected["is_guaranteed"]:
        score = 0.5
        reasons.append("guarantee mismatch")

    return score, str(reasons)