"""
Unit tests for validation_agent.py
Tests the validation agent with various edge cases and scenarios.
"""
import pytest
from unittest.mock import patch, Mock
import json

from assurhabitat_agents.agents.validation_agent import (
    ValidationReActState,
    node_thought_action_valid,
    node_tool_execution_valid,
    format_prompt_valid
)
from tests.fixtures.sample_cases import get_sample_parsed_declaration


class TestValidationAgent:
    """Test suite for validation agent."""
    
    def test_validation_agent_conformity_match(self, patch_llm_inference, patch_vlm_inference):
        """Test validation agent with conforming images."""
        patch_llm_inference.set_responses([
            "Action: CheckConformity\nArguments: {}",
            "Action: CheckGuarantee\nArguments: {}",
            "Answer: Validation réussie."
        ])
        
        patch_vlm_inference.set_responses([
            json.dumps({
                "description": "Water damage visible",
                "detected_damage_types": ["water"]
            })
        ])
        
        initial_state: ValidationReActState = {
            "images_path": ["data/attachments/WaterDamage_100.jpg"],
            "history": [],
            "last_action": None,
            "last_arguments": None,
            "last_observation": None,
            "parsed_declaration": get_sample_parsed_declaration("complete_water"),
            "image_conformity": None,
            "guarantee_report": None,
            "answer": None
        }
        
        state = node_thought_action_valid(initial_state)
        
        assert state["last_action"] is not None or state.get("answer") is not None
    
    def test_validation_agent_conformity_mismatch(self, patch_vlm_inference):
        """Test validation agent with non-conforming images."""
        # Fire image for water damage declaration -> should not match
        patch_vlm_inference.set_responses([
            json.dumps({
                "description": "Fire damage visible",
                "detected_damage_types": ["fire", "soot"]
            })
        ])
        
        state: ValidationReActState = {
            "images_path": ["data/attachments/FireDamage_31.jpg"],
            "history": [],
            "last_action": "CheckConformity",
            "last_arguments": {
                "image_paths": ["data/attachments/FireDamage_31.jpg"],
                "parsed_declaration": get_sample_parsed_declaration("complete_water")
            },
            "last_observation": None,
            "parsed_declaration": get_sample_parsed_declaration("complete_water"),
            "image_conformity": None,
            "guarantee_report": None,
            "answer": None
        }
        
        with patch("assurhabitat_agents.agents.validation_agent.tools") as mock_tools:
            mock_tools.__contains__.return_value = True
            mock_tools.__getitem__.return_value = Mock(return_value={
                "description": "Fire damage",
                "detected_damage_types": ["fire", "soot"],
                "raw_output": "..."
            })
            
            result_state = node_tool_execution_valid(state)
            
            # Compatibility should be False (fire != water)
            assert result_state["image_conformity"] is not None
            assert result_state["image_conformity"].get("compatible") is False
    
    def test_validation_agent_guarantee_check(self, patch_llm_inference):
        """Test validation agent guarantee check."""
        patch_llm_inference.set_responses([
            "Action: CheckGuarantee\nArguments: {}"
        ])
        
        state: ValidationReActState = {
            "images_path": ["data/attachments/WaterDamage_100.jpg"],
            "history": [],
            "last_action": None,
            "last_arguments": None,
            "last_observation": None,
            "parsed_declaration": get_sample_parsed_declaration("complete_water"),
            "image_conformity": {
                "description": "Water damage",
                "detected_damage_types": ["water"],
                "compatible": True
            },
            "guarantee_report": None,
            "answer": None
        }
        
        result_state = node_thought_action_valid(state)
        
        # Should request guarantee check
        assert result_state["last_action"] == "CheckGuarantee" or result_state.get("answer") is not None
    
    def test_validation_agent_guarantee_not_covered(self):
        """Test validation agent when guarantee is not covered."""
        state: ValidationReActState = {
            "images_path": [],
            "history": [],
            "last_action": "CheckGuarantee",
            "last_arguments": {},
            "last_observation": None,
            "parsed_declaration": get_sample_parsed_declaration("complete_water"),
            "image_conformity": {"compatible": True, "detected_damage_types": ["water"]},
            "guarantee_report": None,
            "answer": None
        }
        
        with patch("assurhabitat_agents.agents.validation_agent.tools") as mock_tools:
            mock_tools.__contains__.return_value = True
            mock_tools.__getitem__.return_value = Mock(return_value={
                "guaranteed": False,
                "description": "Not covered due to exclusion"
            })
            
            result_state = node_tool_execution_valid(state)
            
            assert result_state["guarantee_report"] is not None
            assert result_state["guarantee_report"]["guaranteed"] is False
    
    def test_validation_agent_no_images(self, patch_llm_inference):
        """Test validation agent when no images provided."""
        patch_llm_inference.set_responses([
            "Action: CheckConformity\nArguments: {}"
        ])
        
        state: ValidationReActState = {
            "images_path": [],
            "history": [],
            "last_action": None,
            "last_arguments": None,
            "last_observation": None,
            "parsed_declaration": get_sample_parsed_declaration("complete_water"),
            "image_conformity": None,
            "guarantee_report": None,
            "answer": None
        }
        
        result_state = node_thought_action_valid(state)
        
        # Should still request conformity check (which will handle empty list)
        assert result_state["last_action"] is not None or result_state.get("answer") is not None
    
    def test_validation_tool_execution_conformity(self):
        """Test tool execution for CheckConformity."""
        state: ValidationReActState = {
            "images_path": ["data/attachments/WaterDamage_100.jpg"],
            "history": [],
            "last_action": "CheckConformity",
            "last_arguments": {
                "image_paths": ["data/attachments/WaterDamage_100.jpg"],
                "parsed_declaration": get_sample_parsed_declaration("complete_water")
            },
            "last_observation": None,
            "parsed_declaration": get_sample_parsed_declaration("complete_water"),
            "image_conformity": None,
            "guarantee_report": None,
            "answer": None
        }
        
        with patch("assurhabitat_agents.agents.validation_agent.tools") as mock_tools:
            mock_tools.__contains__.return_value = True
            mock_tools.__getitem__.return_value = Mock(return_value={
                "description": "Water damage",
                "detected_damage_types": ["water"],
                "raw_output": "..."
            })
            
            result_state = node_tool_execution_valid(state)
            
            assert result_state["image_conformity"] is not None
            assert "compatible" in result_state["image_conformity"]
            assert result_state["last_action"] is None  # Reset
    
    def test_validation_tool_execution_guarantee(self):
        """Test tool execution for CheckGuarantee."""
        state: ValidationReActState = {
            "images_path": [],
            "history": [],
            "last_action": "CheckGuarantee",
            "last_arguments": {"parsed_declaration": get_sample_parsed_declaration("complete_fire")},
            "last_observation": None,
            "parsed_declaration": get_sample_parsed_declaration("complete_fire"),
            "image_conformity": {"compatible": True},
            "guarantee_report": None,
            "answer": None
        }
        
        with patch("assurhabitat_agents.agents.validation_agent.tools") as mock_tools:
            mock_tools.__contains__.return_value = True
            mock_tools.__getitem__.return_value = Mock(return_value={
                "guaranteed": True,
                "description": "Covered by policy"
            })
            
            result_state = node_tool_execution_valid(state)
            
            assert result_state["guarantee_report"] is not None
            assert result_state["guarantee_report"]["guaranteed"] is True
    
    def test_validation_conformity_compatibility_rules_fire(self):
        """Test conformity compatibility rules for fire damage."""
        state: ValidationReActState = {
            "images_path": ["data/attachments/FireDamage_31.jpg"],
            "history": [],
            "last_action": "CheckConformity",
            "last_arguments": {},
            "last_observation": None,
            "parsed_declaration": get_sample_parsed_declaration("complete_fire"),
            "image_conformity": None,
            "guarantee_report": None,
            "answer": None
        }
        
        with patch("assurhabitat_agents.agents.validation_agent.tools") as mock_tools:
            mock_tools.__contains__.return_value = True
            mock_tools.__getitem__.return_value = Mock(return_value={
                "description": "Fire damage",
                "detected_damage_types": ["fire", "soot"]
            })
            
            result_state = node_tool_execution_valid(state)
            
            # Fire detected + incendie_explosion type = compatible
            assert result_state["image_conformity"]["compatible"] is True
    
    def test_validation_conformity_compatibility_rules_water(self):
        """Test conformity compatibility rules for water damage."""
        state: ValidationReActState = {
            "images_path": ["data/attachments/WaterDamage_100.jpg"],
            "history": [],
            "last_action": "CheckConformity",
            "last_arguments": {},
            "last_observation": None,
            "parsed_declaration": get_sample_parsed_declaration("complete_water"),
            "image_conformity": None,
            "guarantee_report": None,
            "answer": None
        }
        
        with patch("assurhabitat_agents.agents.validation_agent.tools") as mock_tools:
            mock_tools.__contains__.return_value = True
            mock_tools.__getitem__.return_value = Mock(return_value={
                "description": "Water damage",
                "detected_damage_types": ["water"]
            })
            
            result_state = node_tool_execution_valid(state)
            
            # Water detected + degats_des_eaux type = compatible
            assert result_state["image_conformity"]["compatible"] is True
    
    def test_validation_conformity_compatibility_rules_theft(self):
        """Test conformity compatibility rules for theft/vandalism."""
        state: ValidationReActState = {
            "images_path": ["eval/eval_pictures/VOL_01.png"],
            "history": [],
            "last_action": "CheckConformity",
            "last_arguments": {},
            "last_observation": None,
            "parsed_declaration": get_sample_parsed_declaration("complete_theft"),
            "image_conformity": None,
            "guarantee_report": None,
            "answer": None
        }
        
        with patch("assurhabitat_agents.agents.validation_agent.tools") as mock_tools:
            mock_tools.__contains__.return_value = True
            mock_tools.__getitem__.return_value = Mock(return_value={
                "description": "Break-in damage",
                "detected_damage_types": ["impact", "theft_signs"]
            })
            
            result_state = node_tool_execution_valid(state)
            
            # Impact/theft_signs detected + vol_vandalisme type = compatible
            assert result_state["image_conformity"]["compatible"] is True
    
    def test_validation_tool_error_handling(self):
        """Test validation agent handles tool errors gracefully."""
        state: ValidationReActState = {
            "images_path": [],
            "history": [],
            "last_action": "CheckConformity",
            "last_arguments": {},
            "last_observation": None,
            "parsed_declaration": get_sample_parsed_declaration("complete_water"),
            "image_conformity": None,
            "guarantee_report": None,
            "answer": None
        }
        
        with patch("assurhabitat_agents.agents.validation_agent.tools") as mock_tools:
            mock_tools.__contains__.return_value = True
            mock_tools.__getitem__.return_value = Mock(side_effect=Exception("Tool error"))
            
            result_state = node_tool_execution_valid(state)
            
            assert "Error" in result_state["last_observation"]
    
    def test_format_prompt_validation(self):
        """Test prompt formatting for validation agent."""
        state: ValidationReActState = {
            "images_path": ["test.jpg"],
            "history": ["Step 1"],
            "last_action": None,
            "last_arguments": None,
            "last_observation": None,
            "parsed_declaration": get_sample_parsed_declaration("complete_water"),
            "image_conformity": None,
            "guarantee_report": None,
            "answer": None
        }
        
        tools = ["CheckConformity", "CheckGuarantee"]
        prompt = format_prompt_valid(state, tools)
        
        assert "CheckConformity" in prompt
        assert "CheckGuarantee" in prompt
        assert "test.jpg" in prompt
    
    def test_validation_produces_final_answer(self, patch_llm_inference):
        """Test validation agent produces final answer when both checks complete."""
        patch_llm_inference.set_responses([
            "Answer: Validation complète, tout est conforme."
        ])
        
        state: ValidationReActState = {
            "images_path": ["test.jpg"],
            "history": [],
            "last_action": None,
            "last_arguments": None,
            "last_observation": None,
            "parsed_declaration": get_sample_parsed_declaration("complete_water"),
            "image_conformity": {"compatible": True, "detected_damage_types": ["water"]},
            "guarantee_report": {"guaranteed": True, "description": "Covered"},
            "answer": None
        }
        
        result_state = node_thought_action_valid(state)
        
        assert result_state.get("answer") is not None
    
    @pytest.mark.parametrize("sinistre_type,damage_types,expected_compatible", [
        ("incendie_explosion", ["fire", "soot"], True),
        ("incendie_explosion", ["water"], False),
        ("degats_des_eaux", ["water"], True),
        ("degats_des_eaux", ["fire"], False),
        ("vol_vandalisme", ["impact"], True),
        ("vol_vandalisme", ["water"], False),
    ])
    def test_validation_compatibility_matrix(self, sinistre_type, damage_types, expected_compatible):
        """Test various combinations of sinistre types and detected damage types."""
        parsed = {
            "sinistre_type": sinistre_type,
            "extracted": {"description": "Test"}
        }
        
        state: ValidationReActState = {
            "images_path": ["test.jpg"],
            "history": [],
            "last_action": "CheckConformity",
            "last_arguments": {},
            "last_observation": None,
            "parsed_declaration": parsed,
            "image_conformity": None,
            "guarantee_report": None,
            "answer": None
        }
        
        with patch("assurhabitat_agents.agents.validation_agent.tools") as mock_tools:
            mock_tools.__contains__.return_value = True
            mock_tools.__getitem__.return_value = Mock(return_value={
                "description": "Test",
                "detected_damage_types": damage_types
            })
            
            result_state = node_tool_execution_valid(state)
            
            assert result_state["image_conformity"]["compatible"] == expected_compatible

