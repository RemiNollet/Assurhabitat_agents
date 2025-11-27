from assurhabitat_agents.tools.parse_declaration_tool import parse_declaration
from assurhabitat_agents.tools.ask_human_tool import ask_human
from assurhabitat_agents.tools.verify_completness_tool import verify_completeness

TOOLS = {
    "DeclarationParser": parse_declaration,
    "AskHuman": ask_human,
    "InformationVerification": verify_completeness
}