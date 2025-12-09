# src/assurhabitat_agents/tools/sinistre_conformity_tool.py
"""
This tool take a picture and the sinistre type as arguments and analyze if the picture is conforme to the declared sinistre, using a VLM
"""
from transformers import Qwen2VLForConditionalGeneration, AutoTokenizer, AutoProcessor
from qwen_vl_utils import process_vision_info

from assurhabitat_agents.model.vlm_model_loading import vlm_inference

def check_conformity(image_paths, sinistre_type):
    if not image_paths:
        return {"error": "Missing images"}
    
    image_path = image_paths[0]

    prompt = f"""
You are an insurance expert analyzing a claim.
Here is the declared sinistre type: **{sinistre_type}**

TASK 1 — Describe what is visible in the picture in 1–2 sentences.
TASK 2 — Decide whether the picture matches the declared sinistre.
Answer strictly in JSON using this format:

{{
  "description": "...",
  "match": true/false
}}

Do NOT add any text outside the JSON.
"""

    output = vlm_inference(image_path, prompt)

    # Try parsing JSON
    import json
    try:
        parsed = json.loads(output)
        description = parsed.get("description", "")
        match = bool(parsed.get("match", False))
    except Exception:
        # fallback: classical detection
        description = output.strip()
        match = "true" in output.lower()

    return {
        "match": match,
        "description": description,
        "raw_output": output
    }