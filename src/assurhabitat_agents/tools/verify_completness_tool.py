from typing import Dict, Any, List
from assurhabitat_agents.utils import get_expected_fields
from assurhabitat_agents.config.langfuse_config import observe

@observe(name="verify_completeness")
def verify_completeness(parsed_declaration: dict) -> Dict[str, Any]:
    """
    Check if the extracted claim information is complete.

    This function uses the YAML configuration to know which fields
    are required for each type of claim (sinistre). It compares the
    extracted information with the required fields and returns:
      {
        "is_complete": True/False,
        "missing": [list of missing fields]
      }

    Rules:
    - required fields come from sinistres.yaml
    - if a required field is missing or empty, it is reported
    - photos are not required unless explicitly listed in YAML
    - description is always present (fallback), so usually not required
    """
    sinistre_type = parsed_declaration["sinistre_type"]
    extracted = parsed_declaration["extracted"]

    # Load expected config from YAML
    expected = get_expected_fields(sinistre_type)
    
    # if a JSON string accidentally passed, try to parse it
    if isinstance(parsed_declaration, str):
        try:
            parsed_declaration = json.loads(parsed_declaration)
        except Exception:
            import ast
            try:
                parsed_declaration = ast.literal_eval(parsed_declaration)
            except Exception:
                # give a clear error early
                return {"is_complete": False, "missing": [], "error": "parsed_declaration not parseable"}

    # Get the required_fields list from the YAML,
    # or a minimal default
    required_fields: List[str] = expected.get(
        "required_fields",
        ["date_sinistre", "lieu"]  # simplified minimal default
    )

    missing_fields: List[str] = []

    for field_name in required_fields:
        value = extracted.get(field_name)

        # Case 1: completely missing
        if value is None:
            missing_fields.append(field_name)
            continue

        # Case 2: empty string
        if isinstance(value, str) and value.strip() == "":
            missing_fields.append(field_name)
            continue

        # Case 3: empty list (ex: photos or biens_impactes)
        if isinstance(value, list) and len(value) == 0:
            missing_fields.append(field_name)
            continue

        # Otherwise: field is OK

    # Return final result
    return {
        "is_complete": len(missing_fields) == 0,
        "missing": missing_fields
    }