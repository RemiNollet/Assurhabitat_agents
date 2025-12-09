from PIL import Image
import json

from assurhabitat_agents.model.vlm_model_loading import vlm_inference
from assurhabitat_agents.utils import get_guarantee_for_type

def cost_estimation(image_paths: list[str], parsed_declaration: dict):
    if not image_paths:
        return {"error": "Missing images"}
    try:
        image = Image.open(image_paths[0])
    except Exception:
        return {"error": "Cannot open image"}

    image = Image.open(image_paths[0])
    prompt = """
Analyze the following photos of a home insurance claim.
Estimate the total cost of visible damages in euros.
Return ONLY a JSON object, strictly in this format:
{
  "estimated_cost": <number>,
  "explanation": "<short explanation>"
}

- Return ONLY valid JSON.
- No commentary, no markdown.
"""
    raw_output = vlm_inference(image, prompt)

    try:
        analysis = json.loads(raw_output)
        estimated_cost = float(analysis["estimated_cost"])
        explanation = analysis["explanation"]
    except Exception:
        return {"error": f"VLM JSON parsing failed: {raw_output}"}

    garant = get_guarantee_for_type(parsed_declaration["sinistre_type"])
    plafond = garant.get("plafond", None)
    franchise = garant.get("franchise", 0)
    after_franchise = max(estimated_cost - franchise, 0)
    if plafond is None:
        final_compensation = after_franchise
    else:
        final_compensation = min(after_franchise, plafond)

    output = {
        "estimated_cost": estimated_cost,
        "explanation": explanation,
        "max_covered_amount": plafond,
        "franchise": franchise,
        "final_compensation": final_compensation,
    }
    return output


