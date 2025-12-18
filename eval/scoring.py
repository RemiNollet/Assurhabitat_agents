def score_declaration(output, expected):
    score = 1.0
    reasons = []

    if output.get("is_complete") != expected["is_complete"]:
        score = 0.0
        reasons.append("is_complete mismatch")

    if set(output.get("missing", [])) != set(expected["missing_fields"]):
        score = 0.5
        reasons.append("missing_fields mismatch")

    return score, reasons


def score_validation(output, expected):
    score = 1.0
    reasons = []

    if output["image_conformity"]["compatible"] != expected["image_conformity"]:
        score = 0.0
        reasons.append("image conformity mismatch")

    if output["guarantee_report"]["guaranteed"] != expected["is_guaranteed"]:
        score = 0.0
        reasons.append("guarantee mismatch")

    return score, reasons