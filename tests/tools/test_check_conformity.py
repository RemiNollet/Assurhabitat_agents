"""
Unit tests for check_conformity_tool.py
Tests image conformity checking with various damage types.
"""
import pytest
from unittest.mock import patch, Mock
import json

from assurhabitat_agents.tools.check_conformity_tool import check_conformity
from tests.fixtures.mock_vlm import mock_vlm_inference


class TestCheckConformity:
    """Test suite for check_conformity tool."""
    
    def test_conformity_with_fire_image(self, patch_vlm_inference):
        """Test conformity check with fire damage image."""
        # Setup mock VLM to return fire damage
        patch_vlm_inference.set_responses([
            json.dumps({
                "description": "Fire damage visible with soot on walls",
                "detected_damage_types": ["fire", "soot"]
            })
        ])
        
        parsed_declaration = {
            "sinistre_type": "incendie_explosion",
            "extracted": {"description": "Fire in kitchen"}
        }
        
        result = check_conformity(
            image_paths=["data/attachments/FireDamage_31.jpg"],
            parsed_declaration=parsed_declaration
        )
        
        assert "description" in result
        assert "detected_damage_types" in result
        assert "fire" in result["detected_damage_types"]
        assert patch_vlm_inference.call_count == 1
    
    def test_conformity_with_water_image(self, patch_vlm_inference):
        """Test conformity check with water damage image."""
        patch_vlm_inference.set_responses([
            json.dumps({
                "description": "Water stains visible on ceiling",
                "detected_damage_types": ["water"]
            })
        ])
        
        parsed_declaration = {
            "sinistre_type": "degats_des_eaux",
            "extracted": {"description": "Water leak"}
        }
        
        result = check_conformity(
            image_paths=["data/attachments/WaterDamage_100.jpg"],
            parsed_declaration=parsed_declaration
        )
        
        assert "water" in result["detected_damage_types"]
        assert result["description"] != ""
    
    def test_conformity_with_mold_image(self, patch_vlm_inference):
        """Test conformity check with mold damage (water-related)."""
        patch_vlm_inference.set_responses([
            json.dumps({
                "description": "Mold growth from water damage",
                "detected_damage_types": ["water", "mold"]
            })
        ])
        
        parsed_declaration = {
            "sinistre_type": "degats_des_eaux",
            "extracted": {"description": "Mold in bathroom"}
        }
        
        result = check_conformity(
            image_paths=["data/attachments/Mold_Severe_187.jpg"],
            parsed_declaration=parsed_declaration
        )
        
        assert "mold" in result["detected_damage_types"]
        assert "water" in result["detected_damage_types"]
    
    def test_conformity_with_theft_image(self, patch_vlm_inference):
        """Test conformity check with theft/vandalism image."""
        patch_vlm_inference.set_responses([
            json.dumps({
                "description": "Broken door with impact damage",
                "detected_damage_types": ["impact", "theft_signs"]
            })
        ])
        
        parsed_declaration = {
            "sinistre_type": "vol_vandalisme",
            "extracted": {"description": "Break-in"}
        }
        
        result = check_conformity(
            image_paths=["eval/eval_pictures/VOL_01.png"],
            parsed_declaration=parsed_declaration
        )
        
        assert "impact" in result["detected_damage_types"] or "theft_signs" in result["detected_damage_types"]
    
    def test_conformity_no_images(self):
        """Test conformity check when no images provided."""
        parsed_declaration = {
            "sinistre_type": "degats_des_eaux",
            "extracted": {"description": "Water leak"}
        }
        
        result = check_conformity(
            image_paths=[],
            parsed_declaration=parsed_declaration
        )
        
        assert "error" in result
        assert result["error"] == "Missing images"
    
    def test_conformity_empty_image_list(self):
        """Test conformity check with empty image list."""
        result = check_conformity(
            image_paths=[],
            parsed_declaration={"sinistre_type": "incendie_explosion"}
        )
        
        assert "error" in result
    
    def test_conformity_vlm_returns_invalid_json(self, patch_vlm_inference):
        """Test conformity check when VLM returns invalid JSON."""
        # Mock VLM to return non-JSON text
        patch_vlm_inference.set_responses([
            "This is not JSON, just plain text describing damage"
        ])
        
        parsed_declaration = {
            "sinistre_type": "degats_des_eaux",
            "extracted": {"description": "Water leak"}
        }
        
        result = check_conformity(
            image_paths=["data/attachments/WaterDamage_100.jpg"],
            parsed_declaration=parsed_declaration
        )
        
        # Should handle gracefully, returning description as raw output
        assert "raw_output" in result
        assert result["raw_output"] != ""
    
    def test_conformity_vlm_returns_partial_json(self, patch_vlm_inference):
        """Test conformity check when VLM returns incomplete JSON."""
        patch_vlm_inference.set_responses([
            json.dumps({
                "description": "Some damage visible"
                # Missing detected_damage_types
            })
        ])
        
        parsed_declaration = {
            "sinistre_type": "incendie_explosion"
        }
        
        result = check_conformity(
            image_paths=["data/attachments/FireDamage_45.jpg"],
            parsed_declaration=parsed_declaration
        )
        
        # Should handle missing fields gracefully
        assert "description" in result
    
    def test_conformity_multiple_images_uses_first(self, patch_vlm_inference):
        """Test that conformity check uses the first image when multiple provided."""
        patch_vlm_inference.set_responses([
            json.dumps({
                "description": "First image analyzed",
                "detected_damage_types": ["water"]
            })
        ])
        
        parsed_declaration = {
            "sinistre_type": "degats_des_eaux"
        }
        
        result = check_conformity(
            image_paths=[
                "data/attachments/WaterDamage_100.jpg",
                "data/attachments/WaterDamage_176.jpg",
                "data/attachments/WaterDamage_306.jpg"
            ],
            parsed_declaration=parsed_declaration
        )
        
        # Should have called VLM once with first image
        assert patch_vlm_inference.call_count == 1
        assert "description" in result
    
    @pytest.mark.parametrize("damage_type,expected_types", [
        ("fire", ["fire", "soot", "smoke"]),
        ("water", ["water"]),
        ("theft", ["impact", "theft_signs", "vandalism"]),
    ])
    def test_conformity_various_damage_types(self, patch_vlm_inference, damage_type, expected_types):
        """Test conformity detection for various damage types."""
        patch_vlm_inference.set_responses([
            json.dumps({
                "description": f"{damage_type} damage",
                "detected_damage_types": [expected_types[0]]
            })
        ])
        
        parsed_declaration = {
            "sinistre_type": "test_type",
            "extracted": {"description": f"{damage_type} test"}
        }
        
        result = check_conformity(
            image_paths=[f"test_{damage_type}.jpg"],
            parsed_declaration=parsed_declaration
        )
        
        assert result["detected_damage_types"][0] in expected_types
    
    def test_conformity_unknown_damage_type(self, patch_vlm_inference):
        """Test conformity when damage type is unknown or unclear."""
        patch_vlm_inference.set_responses([
            json.dumps({
                "description": "Unclear damage in image",
                "detected_damage_types": ["unknown"]
            })
        ])
        
        parsed_declaration = {
            "sinistre_type": "ambiguous"
        }
        
        result = check_conformity(
            image_paths=["data/attachments/test.jpg"],
            parsed_declaration=parsed_declaration
        )
        
        assert "detected_damage_types" in result
        assert result["detected_damage_types"] == ["unknown"]

