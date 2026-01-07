"""
Mock LLM for testing purposes.
Provides predictable responses based on the prompt content.
"""
import json
import re


class MockLLM:
    """Mock LLM that returns predictable responses based on prompt patterns."""
    
    def __init__(self, default_response=None):
        self.default_response = default_response or "Action: DeclarationParser\nArguments: {}"
        self.call_count = 0
        self.last_prompt = None
        self.responses = []
        
    def __call__(self, prompt: str) -> str:
        """Called when used as llm_inference replacement."""
        self.call_count += 1
        self.last_prompt = prompt
        
        # Return custom responses if set
        if self.responses:
            return self.responses.pop(0)
        
        # Pattern-based responses for realistic behavior
        if "DeclarationParser" in prompt and "parsed_declaration is None" in prompt:
            return """Action: DeclarationParser
Arguments: {}"""
        
        if "InformationVerification" in prompt or "verify_completeness" in prompt:
            return """Action: InformationVerification
Arguments: {}"""
        
        if "AskHuman" in prompt and "missing" in prompt.lower():
            return """Action: AskHuman
Arguments: {"question": "Please provide missing information"}"""
        
        if "CheckConformity" in prompt:
            return """Action: CheckConformity
Arguments: {"image_paths": [], "parsed_declaration": {}}"""
        
        if "CheckGuarantee" in prompt:
            return """Action: CheckGuarantee
Arguments: {"parsed_declaration": {}}"""
        
        if "CostEstimation" in prompt:
            return """Action: CostEstimation
Arguments: {"image_paths": [], "parsed_declaration": {}}"""
        
        # Final answer when everything is complete
        if "answer" in prompt.lower() or "final" in prompt.lower():
            return """Answer: La déclaration est complète et validée."""
        
        return self.default_response
    
    def set_responses(self, responses: list):
        """Set a sequence of responses to return."""
        self.responses = responses.copy()
        
    def reset(self):
        """Reset the mock state."""
        self.call_count = 0
        self.last_prompt = None
        self.responses = []


def mock_llm_inference(prompt: str) -> str:
    """Simple mock function that can replace llm_inference."""
    # Parse declaration requests
    if "parse_declaration" in prompt.lower() or "DeclarationParser" in prompt:
        if "vol" in prompt.lower() or "effraction" in prompt.lower():
            return json.dumps({
                "sinistre_type": "vol_vandalisme",
                "sinistre_confidence": 0.95,
                "sinistre_explain": "Forced entry detected",
                "candidates": [{"type": "vol_vandalisme", "score": 0.95}],
                "extracted": {
                    "date_sinistre": "2025-01-07",
                    "lieu": "chambre",
                    "description": "Effraction avec vol",
                    "biens_impactes": ["porte"],
                    "police_report_number": None
                }
            })
        elif "feu" in prompt.lower() or "incendie" in prompt.lower():
            return json.dumps({
                "sinistre_type": "incendie_explosion",
                "sinistre_confidence": 0.98,
                "sinistre_explain": "Fire damage detected",
                "candidates": [{"type": "incendie_explosion", "score": 0.98}],
                "extracted": {
                    "date_sinistre": "2025-01-06",
                    "lieu": "cuisine",
                    "description": "Incendie dans la cuisine",
                    "biens_impactes": ["four", "mur"]
                }
            })
        else:
            return json.dumps({
                "sinistre_type": "degats_des_eaux",
                "sinistre_confidence": 0.92,
                "sinistre_explain": "Water damage detected",
                "candidates": [{"type": "degats_des_eaux", "score": 0.92}],
                "extracted": {
                    "date_sinistre": "2025-01-05",
                    "lieu": "salle de bain",
                    "description": "Fuite d'eau au plafond",
                    "biens_impactes": ["plafond", "sol"]
                }
            })
    
    # Guarantee check requests
    if "guarantee" in prompt.lower() or "garantie" in prompt.lower():
        return json.dumps({
            "guaranteed": True,
            "description": "Covered by policy"
        })
    
    # Default action response
    return "Action: DeclarationParser\nArguments: {}"


def create_mock_parsed_declaration(sinistre_type="degats_des_eaux", complete=True):
    """Create a mock parsed declaration for testing."""
    base = {
        "sinistre_type": sinistre_type,
        "sinistre_confidence": 0.95,
        "sinistre_explain": "Test declaration",
        "candidates": [{"type": sinistre_type, "score": 0.95}],
        "extracted": {
            "date_sinistre": "2025-01-07",
            "lieu": "salon",
            "description": "Test damage",
            "biens_impactes": ["mur", "sol"]
        }
    }
    
    if not complete:
        base["extracted"]["date_sinistre"] = None
        base["extracted"]["lieu"] = None
    
    if sinistre_type == "vol_vandalisme":
        base["extracted"]["police_report_number"] = "12345" if complete else None
    
    return base

