import os
from dotenv import load_dotenv

from assurhabitat_agents.tools.parse_declaration_tool import parse_declaration
from assurhabitat_agents.tools.ask_human_tool import ask_human
from assurhabitat_agents.tools.verify_completness_tool import verify_completeness

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

BASE_MODEL = "mistralai/Devstral-Small-2507"
MAX_NEW_TOKENS = 4096

TOOLS = {
    "DeclarationParser": parse_declaration,
    "AskHuman": ask_human,
    "InformationVerification": verify_completeness
}

N_HISTORY_ENTRIES = 10