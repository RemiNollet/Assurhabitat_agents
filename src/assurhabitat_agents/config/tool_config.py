from assurhabitat_agents.tools.parse_declaration_tool import parse_declaration
from assurhabitat_agents.tools.ask_human_tool import ask_human
from assurhabitat_agents.tools.verify_completness_tool import verify_completeness

from assurhabitat_agents.tools.sinistre_conformity_tool import sinistre_conformity
from assurhabitat_agents.tools.check_guarantee_tool import check_guarantee

from assurhabitat_agents.tools.cost_estimation_tool import cost_estimation

DECLARATION_TOOLS = {
    "DeclarationParser": parse_declaration,
    "AskHuman": ask_human,
    "InformationVerification": verify_completeness
}

VALIDATION_TOOLS = {
    "CheckConformity": sinistre_conformity,
    "CheckGuarantee": check_guarantee
}

VALIDATION_TOOLS_DESCRIPTION = """
1. CheckConformity
   - Description: Analyze if an image matches the declared sinistre type.
   - Arguments:
       - image_path: str → The path to the image to analyze.
       - sinistre_type: str → The type of sinistre to check conformity with.
   - Example:
       Action: CheckConformity
       Arguments: {"image_path": "path/to/photo.jpg", "sinistre_type": "vol_vandalisme"}

2. CheckGuarantee
   - Description: Check if the parsed declaration is guaranteed by the insurance contract.
   - Arguments:
       - parsed_declaration: dict → The declaration previously extracted and structured.
   - Example:
       Action: CheckGuarantee
       Arguments: {"parsed_declaration": {...}}
"""

EXPERTISE_TOOLS = {
    "CostEstimation": cost_estimation
}

EXPERTISE_TOOLS_DESCRIPTION = """
1. CostEstimation
   - Description: Analyze the image and estimate the cost.
   - Arguments:
       - image_paths: list[str]
       - parsed_declaration: dict
   - Example:
       Action: CostEstimation
       Arguments:
           {"image_paths": ["path/to/photo.jpg"]}
"""