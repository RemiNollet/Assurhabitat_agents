# src/assurhabitat_agents/tools/sinistre_conformity_tool.py
"""
This tool take a picture and the sinistre type as arguments and analyze if the picture is conforme to the declared sinistre, using a VLM
"""
from transformers import Qwen2VLForConditionalGeneration, AutoTokenizer, AutoProcessor
from qwen_vl_utils import process_vision_info

from assurhabitat_agents.model.vlm_model_loading import vlm_inference
from assurhabitat_agents.config.langfuse_config import observe

@observe(name="check_conformity")
def check_conformity(image_paths, parsed_declaration):
    if not image_paths:
        return {"error": "Missing images"}
    
    image_path = image_paths[0]

    prompt = f"""
You are an insurance expert analyzing a claim.

Here is the declared sinistre:
{parsed_declaration}

TASK 1 — Describe what is visible in the picture in 1–2 sentences.

TASK 2 — Identify visible damage types.

Return the types of damage visible in the image among:
["fire", "soot", "smoke", "water", "mold", "impact", "theft_signs", "unknown"]

Do NOT decide if the image matches the declaration.
Only report what is visible.
Answer strictly in JSON using this format:

{{
  "description": "...",
  "detected_damage_types": ["fire", "soot"]
}}

Do NOT add any text outside the JSON.
"""

    output = vlm_inference(image_path, prompt)

    # Try parsing JSON
    import json
    try:
        parsed = json.loads(output)
        description = parsed.get("description", "")
        detected_damage_types = parsed.get("detected_damage_types", [])
    except Exception:
        description = output.strip()

    return {
        "description": description,
        "detected_damage_types": detected_damage_types,
        "raw_output": output
    }