# src/assurhabitat_agents/tools/check_guarantee_tool.py
from assurhabitat_agents.utils import get_guarantee_for_type
from assurhabitat_agents.model.llm_model_loading import llm_inference


from typing import Dict, Any
from assurhabitat_agents.utils import get_guarantee_for_type

def check_guarantee(parsed_declaration: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return {"is_garanteed": bool, "guarantee": {...}}
    """
    if not parsed_declaration:
        return {"is_garanteed": False, "reason": "parsed_declaration missing", "guarantee": None}
    sin_type = parsed_declaration.get("sinistre_type")
    if not sin_type:
        return {"is_garanteed": False, "reason": "sinistre_type unknown", "guarantee": None}
    try:
        guarant = get_guarantee_for_type(sin_type)
    except Exception as e:
        return {"is_garanteed": False, "reason": f"guarantee lookup failed: {e}", "guarantee": None}

    prompt = f"""
    You are an agent from an insurrance company. Your role is to analyze if the folowing declaration is garanteed or not.
    declaration: {parsed_declaration}\n
    garantee: {garant}
    Return only True is the declaration matches with the garantee, if not return False. 
    DO NOT RETURN SOMETHING ELSE THAN TRUE OR FALSE!
    """
    llm_answer = llm_inference(prompt).strip().lower()
    is_garanteed = llm_answer == "true"
    
    return {"is_garanteed": is_garanteed, "guarantee": guarant, "raw": llm_answer}