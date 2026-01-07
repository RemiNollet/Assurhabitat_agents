"""
Unit tests for check_guarantee_tool.py
Tests guarantee checking logic for various sinistre types.
"""
import pytest
from unittest.mock import patch, Mock
import json

from assurhabitat_agents.tools.check_guarantee_tool import check_guarantee
from tests.fixtures.sample_cases import get_sample_parsed_declaration


class TestCheckGuarantee:
    """Test suite for check_guarantee tool."""
    
    def test_guarantee_water_damage_covered(self, patch_llm_inference, doc_tools):
        """Test guarantee check for covered water damage."""
        patch_llm_inference.set_responses([
            json.dumps({
                "guaranteed": True,
                "description": "Water leak from pipe rupture is covered"
            })
        ])
        
        parsed_declaration = get_sample_parsed_declaration("complete_water")
        
        with patch("assurhabitat_agents.tools.check_guarantee_tool.get_guarantee_for_type") as mock_get:
            mock_get.return_value = {
                "couverture": ["fuite", "infiltration"],
                "exclusions": ["négligence"],
                "plafond": 5000,
                "franchise": 150
            }
            
            result = check_guarantee(parsed_declaration)
        
        assert result["guaranteed"] is True
        assert "description" in result
    
    def test_guarantee_fire_damage_covered(self, patch_llm_inference):
        """Test guarantee check for covered fire damage."""
        patch_llm_inference.set_responses([
            json.dumps({
                "guaranteed": True,
                "description": "Fire damage is covered by the policy"
            })
        ])
        
        parsed_declaration = get_sample_parsed_declaration("complete_fire")
        
        with patch("assurhabitat_agents.tools.check_guarantee_tool.get_guarantee_for_type") as mock_get:
            mock_get.return_value = {
                "couverture": ["incendie", "explosion"],
                "exclusions": ["acte volontaire"],
                "plafond": 10000,
                "franchise": 200
            }
            
            result = check_guarantee(parsed_declaration)
        
        assert result["guaranteed"] is True
    
    def test_guarantee_theft_covered(self, patch_llm_inference):
        """Test guarantee check for covered theft."""
        patch_llm_inference.set_responses([
            json.dumps({
                "guaranteed": True,
                "description": "Theft with forced entry is covered"
            })
        ])
        
        parsed_declaration = get_sample_parsed_declaration("complete_theft")
        
        with patch("assurhabitat_agents.tools.check_guarantee_tool.get_guarantee_for_type") as mock_get:
            mock_get.return_value = {
                "couverture": ["vol par effraction"],
                "exclusions": ["vol sans effraction"],
                "plafond": 8000,
                "franchise": 300
            }
            
            result = check_guarantee(parsed_declaration)
        
        assert result["guaranteed"] is True
    
    def test_guarantee_negligence_not_covered(self, patch_llm_inference):
        """Test guarantee check for excluded case (negligence)."""
        patch_llm_inference.set_responses([
            json.dumps({
                "guaranteed": False,
                "description": "Not covered due to user negligence"
            })
        ])
        
        parsed_declaration = {
            "sinistre_type": "degats_des_eaux",
            "extracted": {
                "description": "Water damage due to leaving tap open for days"
            }
        }
        
        with patch("assurhabitat_agents.tools.check_guarantee_tool.get_guarantee_for_type") as mock_get:
            mock_get.return_value = {
                "couverture": ["fuite", "infiltration"],
                "exclusions": ["négligence"],
                "plafond": 5000,
                "franchise": 150
            }
            
            result = check_guarantee(parsed_declaration)
        
        assert result["guaranteed"] is False
        assert "négligence" in result["description"].lower() or "negligence" in result["description"].lower()
    
    def test_guarantee_voluntary_act_not_covered(self, patch_llm_inference):
        """Test guarantee check for voluntary act (not covered)."""
        patch_llm_inference.set_responses([
            json.dumps({
                "guaranteed": False,
                "description": "Voluntary fire is excluded from coverage"
            })
        ])
        
        parsed_declaration = {
            "sinistre_type": "incendie_explosion",
            "extracted": {
                "description": "Intentional fire"
            }
        }
        
        with patch("assurhabitat_agents.tools.check_guarantee_tool.get_guarantee_for_type") as mock_get:
            mock_get.return_value = {
                "couverture": ["incendie"],
                "exclusions": ["acte volontaire"],
                "plafond": 10000,
                "franchise": 200
            }
            
            result = check_guarantee(parsed_declaration)
        
        assert result["guaranteed"] is False
    
    def test_guarantee_unknown_sinistre_type(self):
        """Test guarantee check with unknown sinistre type."""
        parsed_declaration = {
            "sinistre_type": "unknown_type",
            "extracted": {"description": "Unknown damage"}
        }
        
        with patch("assurhabitat_agents.tools.check_guarantee_tool.get_guarantee_for_type") as mock_get:
            mock_get.side_effect = KeyError("Unknown sinistre type")
            
            result = check_guarantee(parsed_declaration)
        
        assert result["guaranteed"] is False
        assert "failed" in result["description"].lower()
    
    def test_guarantee_llm_returns_invalid_json(self, patch_llm_inference):
        """Test guarantee check when LLM returns invalid JSON."""
        patch_llm_inference.set_responses([
            "This is not JSON but it says true so it should be covered"
        ])
        
        parsed_declaration = get_sample_parsed_declaration("complete_water")
        
        with patch("assurhabitat_agents.tools.check_guarantee_tool.get_guarantee_for_type") as mock_get:
            mock_get.return_value = {
                "couverture": ["fuite"],
                "exclusions": [],
                "plafond": 5000,
                "franchise": 150
            }
            
            result = check_guarantee(parsed_declaration)
        
        # Fallback logic should detect "true" in text
        assert result["guaranteed"] is True
        assert "description" in result
    
    def test_guarantee_missing_sinistre_type(self):
        """Test guarantee check with missing sinistre_type."""
        parsed_declaration = {
            "extracted": {"description": "Some damage"}
        }
        
        with pytest.raises(KeyError):
            check_guarantee(parsed_declaration)
    
    def test_guarantee_check_with_ambiguous_case(self, patch_llm_inference):
        """Test guarantee check for ambiguous sinistre."""
        patch_llm_inference.set_responses([
            json.dumps({
                "guaranteed": False,
                "description": "Cannot determine coverage due to unclear declaration"
            })
        ])
        
        parsed_declaration = {
            "sinistre_type": "ambiguous",
            "extracted": {"description": "Unclear damage"}
        }
        
        with patch("assurhabitat_agents.tools.check_guarantee_tool.get_guarantee_for_type") as mock_get:
            mock_get.side_effect = KeyError("Unknown type")
            
            result = check_guarantee(parsed_declaration)
        
        assert result["guaranteed"] is False
    
    @pytest.mark.parametrize("sinistre_type,expected_covered", [
        ("degats_des_eaux", True),
        ("incendie_explosion", True),
        ("vol_vandalisme", True),
    ])
    def test_guarantee_various_covered_types(self, patch_llm_inference, sinistre_type, expected_covered):
        """Test guarantee coverage for various sinistre types."""
        patch_llm_inference.set_responses([
            json.dumps({
                "guaranteed": expected_covered,
                "description": f"{sinistre_type} coverage check"
            })
        ])
        
        parsed_declaration = {
            "sinistre_type": sinistre_type,
            "extracted": {"description": "Test"}
        }
        
        with patch("assurhabitat_agents.tools.check_guarantee_tool.get_guarantee_for_type") as mock_get:
            mock_get.return_value = {
                "couverture": ["test"],
                "exclusions": [],
                "plafond": 5000,
                "franchise": 150
            }
            
            result = check_guarantee(parsed_declaration)
        
        assert result["guaranteed"] == expected_covered

