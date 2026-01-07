"""
Mock VLM (Vision Language Model) for testing purposes.
Provides predictable responses based on image analysis prompts.
"""
import json


class MockVLM:
    """Mock VLM that returns predictable responses for image analysis."""
    
    def __init__(self, default_response=None):
        self.default_response = default_response
        self.call_count = 0
        self.last_image_path = None
        self.last_prompt = None
        self.responses = []
        
    def __call__(self, image_path: str, prompt: str) -> str:
        """Called when used as vlm_inference replacement."""
        self.call_count += 1
        self.last_image_path = image_path
        self.last_prompt = prompt
        
        # Return custom responses if set
        if self.responses:
            return self.responses.pop(0)
        
        # Default response based on image filename patterns
        if "fire" in image_path.lower() or "incendie" in image_path.lower():
            return self._fire_response()
        elif "water" in image_path.lower() or "eau" in image_path.lower():
            return self._water_response()
        elif "mold" in image_path.lower() or "moisissure" in image_path.lower():
            return self._mold_response()
        elif "vol" in image_path.lower() or "vandal" in image_path.lower():
            return self._theft_response()
        
        # Default based on prompt content
        if "cost" in prompt.lower() or "estimation" in prompt.lower():
            return self._cost_estimation_response()
        
        return self.default_response or self._generic_conformity_response()
    
    def _fire_response(self) -> str:
        """Response for fire damage images."""
        return json.dumps({
            "description": "Visible fire damage with soot on walls and ceiling",
            "detected_damage_types": ["fire", "soot", "smoke"]
        })
    
    def _water_response(self) -> str:
        """Response for water damage images."""
        return json.dumps({
            "description": "Water stains visible on ceiling and walls",
            "detected_damage_types": ["water"]
        })
    
    def _mold_response(self) -> str:
        """Response for mold damage images."""
        return json.dumps({
            "description": "Mold growth visible on walls, likely from water damage",
            "detected_damage_types": ["water", "mold"]
        })
    
    def _theft_response(self) -> str:
        """Response for theft/vandalism images."""
        return json.dumps({
            "description": "Broken door with visible impact damage",
            "detected_damage_types": ["impact", "theft_signs"]
        })
    
    def _generic_conformity_response(self) -> str:
        """Generic conformity check response."""
        return json.dumps({
            "description": "Damage visible in image",
            "detected_damage_types": ["unknown"]
        })
    
    def _cost_estimation_response(self) -> str:
        """Cost estimation response."""
        return json.dumps({
            "estimated_cost": 1500.0,
            "explanation": "Based on visible damage, estimated repair cost"
        })
    
    def set_responses(self, responses: list):
        """Set a sequence of responses to return."""
        self.responses = responses.copy()
    
    def reset(self):
        """Reset the mock state."""
        self.call_count = 0
        self.last_image_path = None
        self.last_prompt = None
        self.responses = []


def mock_vlm_inference(image_path: str, prompt: str) -> str:
    """Simple mock function that can replace vlm_inference."""
    # Cost estimation
    if "cost" in prompt.lower() or "estimation" in prompt.lower():
        return json.dumps({
            "estimated_cost": 2000.0,
            "explanation": "Mock estimation based on visible damage"
        })
    
    # Conformity check - detect damage type from image filename
    if "fire" in image_path.lower():
        return json.dumps({
            "description": "Fire damage visible",
            "detected_damage_types": ["fire", "soot"]
        })
    elif "water" in image_path.lower():
        return json.dumps({
            "description": "Water damage visible",
            "detected_damage_types": ["water"]
        })
    elif "mold" in image_path.lower():
        return json.dumps({
            "description": "Mold and water damage",
            "detected_damage_types": ["water", "mold"]
        })
    elif "vol" in image_path.lower() or "vandal" in image_path.lower():
        return json.dumps({
            "description": "Vandalism/theft signs visible",
            "detected_damage_types": ["impact", "theft_signs"]
        })
    
    # Default generic response
    return json.dumps({
        "description": "Damage visible in image",
        "detected_damage_types": ["unknown"]
    })

