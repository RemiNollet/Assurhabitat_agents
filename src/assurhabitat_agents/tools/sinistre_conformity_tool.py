# src/assurhabitat_agents/tools/sinistre_conformity_tool.py
"""
This tool take a picture and the sinistre type as arguments and analyze if the picture is conforme to the declared sinistre, using a VLM
"""
from PIL import Image

from assurhabitat_agents.model.vlm_model_loading import vlm_inference

def sinistre_conformity(image_paths, sinistre_type):
    if not image_paths:
        return {"error": "Missing images"}
    try:
        image = Image.open(image_paths[0])
    except Exception:
        return {"error": "Cannot open image"}

    image = Image.open(image_paths[0])
    
    text = f"You are an agent from an insurrance company. You have to analyze picture and answer if the picture correspond to the declared sinister type. The sinister type is {sinistre_type}. Answer 'True' if the picture correspond to the described sinister and 'False' if it doen't match. DO NOT ANSWER SOMETHING MORE."

    output = vlm_inference(image, text)
    match = "true" in output.lower()
    return {"match": match, "raw_output": output}