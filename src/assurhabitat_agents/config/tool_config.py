from assurhabitat_agents.tools.parse_declaration_tool import parse_declaration
from assurhabitat_agents.tools.ask_human_tool import ask_human
from assurhabitat_agents.tools.verify_completness_tool import verify_completeness

from assurhabitat_agents.tools.check_conformity_tool import check_conformity
from assurhabitat_agents.tools.check_guarantee_tool import check_guarantee

from assurhabitat_agents.tools.cost_estimation_tool import cost_estimation

DECLARATION_TOOLS = {
    "DeclarationParser": parse_declaration,
    "AskHuman": ask_human,
    "InformationVerification": verify_completeness
}

DECLARATION_TOOLS_DESCRIPTION = """
1. DeclarationParser
   - Description:
       Extract and structure all relevant information from the user's natural-language declaration
       (date, lieu, description, photos, biens impactés, type de sinistre, etc.).
       Returns a JSON object representing the parsed declaration.
   - Arguments:
       - text: str → The raw input text from the user or combined text+previous JSON.
   - Example:
       Action: DeclarationParser
       Arguments:
           {
               "text": "Mon appartement a été cambriolé hier soir, le 12 juin..."
           }

2. AskHuman
   - Description:
       Ask the human user for missing information (e.g. missing date, missing photos, missing details).
       Returns the human's response as plain text.
   - Arguments:
       - question: str → The question you want to ask the user.
   - Example:
       Action: AskHuman
       Arguments:
           {
               "question": "Pouvez-vous préciser la date exacte du sinistre ?"
           }

3. InformationVerification
   - Description:
       Verify if all required fields are present and valid in the parsed declaration.
       Returns:
         {
           "is_complete": bool,
           "missing": [list of missing fields]
         }
   - Arguments:
       - parsed_declaration: dict → The JSON produced by DeclarationParser.
   - Example:
       Action: InformationVerification
       Arguments:
           {
               "parsed_declaration": { ...full JSON... }
           }
"""

VALIDATION_TOOLS = {
    "CheckConformity": check_conformity,
    "CheckGuarantee": check_guarantee
}

VALIDATION_TOOLS_DESCRIPTION = """
1. CheckConformity
   - Description: Analyze if an image matches the declared sinistre type.
   - Arguments:
       - image_paths: list[str] → The paths to the images to analyze.
       - parsed_declaration: dict → Details about the declaration of the sinister by the customer.
   - Example:
       Action: CheckConformity
       Arguments: {"image_paths": ["path/to/photo1.jpg", "path/to/photo2.jpg"], "parsed_declaration": {...}}

2. CheckGuarantee
   - Description: Check if the parsed declaration is guaranteed by the insurance contract.
   - Arguments:
       - parsed_declaration: dict → The declaration previously extracted and structured.
   - Example:
       Action: CheckGuarantee
       Arguments: {"parsed_declaration": {...}}
"""

EXPERTISE_TOOLS = {
    "CostEstimation": cost_estimation,
    "AskHuman": ask_human
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
           
2. AskHuman
   - Description:
       Ask the human user for missing information (e.g. missing date, missing photos, missing details).
       Returns the human's response as plain text.
   - Arguments:
       - question: str → The question you want to ask the user.
   - Example:
       Action: AskHuman
       Arguments:
           {
               "question": "Pouvez-vous préciser la date exacte du sinistre ?"
           }
"""