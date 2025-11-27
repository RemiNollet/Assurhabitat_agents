import json
from typing import Any, Dict, List, Optional
from assurhabitat_agents.llm.model_loading import llm_inference

def _safe_parse_json(maybe_json: Any) -> Dict[str, Any]:
    """
    Try to convert the LLM output into a Python dict.
    Accepts either a dict (already parsed) or a JSON string.
    Tries a few simple fixes if the string is not pure JSON.
    Raises ValueError if it cannot parse.
    """
    if isinstance(maybe_json, dict):
        return maybe_json

    if not isinstance(maybe_json, str):
        raise ValueError("LLM output is neither dict nor string")

    text = maybe_json.strip()
    # Try direct json.loads
    try:
        return json.loads(text)
    except Exception:
        # Sometimes LLM adds text before JSON -> try to find first '{'
        first_brace = text.find('{')
        if first_brace != -1:
            try:
                return json.loads(text[first_brace:])
            except Exception:
                pass
    # If still failing, raise a clear error
    raise ValueError("Could not parse LLM output as JSON")


def parse_declaration(raw_input: str) -> Dict[str, Any]:
    """
    Parse a free-text insurance claim declaration and classify its type.

    The function sends a single prompt to the LLM and expects a STRICT JSON output
    with the following schema:
      {
        "sinistre_type": "<degats_des_eaux|incendie_explosion|vol_vandalisme|ambiguous>",
        "sinistre_confidence": float,
        "sinistre_explain": "short explanation",
        "candidates": [{"type": "...", "score": float}, ...],
        "extracted": {
            "date_sinistre": "<YYYY-MM-DD or null>",
            "lieu": "<string or null>",
            "description": "<string>",
            "photos": ["path/to/photo1.jpg", ...],
            "biens_impactes": ["...", ...],
            "police_report_number": "<string or null>"
        }
      }

    Notes:
    - The LLM must judge the sinistre type based on the raw_input only.
    - The function returns a dict with defaults for missing fields.
    """

    # Build a simple prompt with a strict JSON output requirement and few examples.
    prompt = f"""
You are an extractor and classifier for AssurHabitat.
You must RETURN ONLY a VALID JSON object (no extra text) following this schema:

{{ 
  "sinistre_type": "<degats_des_eaux|incendie_explosion|vol_vandalisme|ambiguous>",
  "sinistre_confidence": <float 0.0-1.0>,
  "sinistre_explain": "<short explanation>",
  "candidates": [{{"type":"<...>","score":<0-1>}}],

  "extracted": {{
    "date_sinistre": "<YYYY-MM-DD or null>",
    "lieu": "<string or null>",
    "description": "<string>",
    "photos": ["path/to/file1.jpg", "path/to/file2.png"],  # file paths only
    "biens_impactes": ["item1", "item2"],
    "police_report_number": "<string or null>"
  }}
}}

INSTRUCTIONS:
- Read the declaration text and classify it among the three types: degats_des_eaux, incendie_explosion, vol_vandalisme.
- The classification must be based on the text only (no image analysis).
- If uncertain, return "ambiguous" and provide candidates.
- For any unknown field, use null or empty list as appropriate.
- If the input contains already a JSON and new information, add the new information to the old JSON and return the new JSON.
- Return valid JSON only.

FEW-SHOT EXAMPLES:

Example 1:
Input text: "My ceiling has been leaking since yesterday, water on the floor and warped wooden floor."
Expected JSON:
{{"sinistre_type":"degats_des_eaux","sinistre_confidence":0.98,"sinistre_explain":"ceiling leak, water on floor","candidates":[{{"type":"degats_des_eaux","score":0.98}}],"extracted":{{"date_sinistre":null,"lieu":"bathroom","description":"ceiling leaking, water on the floor","photos":[],"biens_impactes":["ceiling","floor"],"police_report_number":null}}}}

Example 2:
Input text: "Someone forced my front door and several items are missing."
Expected JSON:
{{"sinistre_type":"vol_vandalisme","sinistre_confidence":0.99,"sinistre_explain":"forced entry and missing items","candidates":[{{"type":"vol_vandalisme","score":0.99}}],"extracted":{{"date_sinistre":null,"lieu":null,"description":"forced entry, missing items","photos":[],"biens_impactes":[],"police_report_number":null}}}}

Now process this input text:
\"\"\"{raw_input}\"\"\"
""".strip()

    # Call the LLM (llm_inference is expected to return either a dict or a JSON string)
    llm_output = llm_inference(prompt)

    # Parse result safely
    try:
        parsed = _safe_parse_json(llm_output)
    except ValueError as e:
        # On parse error, return a safe fallback structure with error info in explanation
        return {
            "sinistre_type": "ambiguous",
            "sinistre_confidence": 0.0,
            "sinistre_explain": f"LLM parse error: {str(e)}",
            "candidates": [],
            "extracted": {
                "date_sinistre": None,
                "lieu": None,
                "description": raw_input.strip(),
                "photos": [],
                "biens_impactes": [],
                "police_report_number": None
            }
        }

    # Normalize output to ensure expected keys exist
    result: Dict[str, Any] = {}
    result["sinistre_type"] = parsed.get("sinistre_type", "ambiguous")
    try:
        result["sinistre_confidence"] = float(parsed.get("sinistre_confidence", 0.0))
    except Exception:
        result["sinistre_confidence"] = 0.0
    result["sinistre_explain"] = parsed.get("sinistre_explain", "")

    # Candidates: ensure list of dicts
    candidates = parsed.get("candidates", [])
    if not isinstance(candidates, list):
        candidates = []
    result["candidates"] = candidates

    # Extracted sub-dict defaults
    extracted = parsed.get("extracted", {})
    if not isinstance(extracted, dict):
        extracted = {}

    # Fill missing fields with safe defaults
    extracted_safe = {
        "date_sinistre": extracted.get("date_sinistre"),
        "lieu": extracted.get("lieu"),
        "description": extracted.get("description") or raw_input.strip(),
        "photos": extracted.get("photos") if isinstance(extracted.get("photos"), list) else [],
        "biens_impactes": extracted.get("biens_impactes") if isinstance(extracted.get("biens_impactes"), list) else [],
        "police_report_number": extracted.get("police_report_number")
    }
    result["extracted"] = extracted_safe

    return result