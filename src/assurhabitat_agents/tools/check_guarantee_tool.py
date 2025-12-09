# src/assurhabitat_agents/tools/check_guarantee_tool.py
from assurhabitat_agents.utils import get_guarantee_for_type
from assurhabitat_agents.model.llm_model_loading import llm_inference


from typing import Dict, Any
from assurhabitat_agents.utils import get_guarantee_for_type

def check_guarantee(parsed_declaration: Dict[str, Any]) -> Dict[str, Any]:
    sin_type = parsed_declaration.get("sinistre_type")

    try:
        guarantee = get_guarantee_for_type(sin_type)
    except Exception as e:
        return {"guaranteed": False, "description": f"Lookup failed: {e}"}

    prompt = f"""
You are an insurance expert. 
Determine if the following declaration is covered by the insurance guarantee.

Declaration:
{parsed_declaration}

Guarantee:
{guarantee}

Answer ONLY with a JSON object with keys:
- guaranteed: true/false
- description: one-sentence explanation

Example:
{{"guaranteed": true, "description": "Covered because X"}}
"""

    raw = llm_inference(prompt)
    try:
        data = json.loads(extract_json(raw))
    except:
        # fallback simple logic
        data = {
            "guaranteed": "true" in raw.lower(),
            "description": raw
        }

    return data