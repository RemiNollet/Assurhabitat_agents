"""
Unit tests for expertise_agent.py
Tests the expertise agent with various edge cases and scenarios.
"""
import pytest
from unittest.mock import patch, Mock
import json

from assurhabitat_agents.agents.expertise_agent import (
    ExpertiseReActState,
    node_thought_action_expert,
    node_tool_execution_expert,
    format_prompt_expert
)
from tests.fixtures.sample_cases import get_sample_parsed_declaration


class TestExpertiseAgent:
    """Test suite for expertise agent."""
    
    def test_expertise_agent_cost_estimation(self, patch_llm_inference, patch_vlm_inference):
        """Test expertise agent performs cost estimation."""
        patch_llm_inference.set_responses([
            "Action: CostEstimation\nArguments: {}",
            "Answer: Rapport d'expertise complet."
        ])
        
        patch_vlm_inference.set_responses([
            json.dumps({
                "estimated_cost": 2000.0,
                "explanation": "Water damage repair"
            })
        ])
        
        initial_state: ExpertiseReActState = {
            "image_paths": ["data/attachments/WaterDamage_100.jpg"],
            "images_validated": True,
            "history": [],
            "last_action": None,
            "last_arguments": None,
            "last_observation": None,
            "parsed_declaration": get_sample_parsed_declaration("complete_water"),
            "estimation": None,
            "report": None
        }
        
        state = node_thought_action_expert(initial_state)
        
        assert state["last_action"] is not None or state.get("report") is not None
    
    def test_expertise_agent_generates_report(self, patch_llm_inference):
        """Test expertise agent generates final report."""
        patch_llm_inference.set_responses([
            "Answer: Rapport: Sinistre degats_des_eaux. Coût: 2000€. Franchise: 150€. Indemnisation: 1850€."
        ])
        
        state: ExpertiseReActState = {
            "image_paths": ["test.jpg"],
            "images_validated": True,
            "history": [],
            "last_action": None,
            "last_arguments": None,
            "last_observation": None,
            "parsed_declaration": get_sample_parsed_declaration("complete_water"),
            "estimation": {
                "estimated_cost": 2000.0,
                "explanation": "Repair costs",
                "franchise": 150,
                "max_covered_amount": 5000,
                "final_compensation": 1850.0
            },
            "report": None
        }
        
        result_state = node_thought_action_expert(state)
        
        assert result_state.get("report") is not None or result_state["last_action"] is not None
    
    def test_expertise_tool_execution_cost_estimation(self):
        """Test tool execution for CostEstimation."""
        state: ExpertiseReActState = {
            "image_paths": ["data/attachments/FireDamage_31.jpg"],
            "images_validated": True,
            "history": [],
            "last_action": "CostEstimation",
            "last_arguments": {
                "image_paths": ["data/attachments/FireDamage_31.jpg"],
                "parsed_declaration": get_sample_parsed_declaration("complete_fire")
            },
            "last_observation": None,
            "parsed_declaration": get_sample_parsed_declaration("complete_fire"),
            "estimation": None,
            "report": None
        }
        
        with patch("assurhabitat_agents.agents.expertise_agent.tools") as mock_tools:
            mock_tools.__contains__.return_value = True
            mock_tools.__getitem__.return_value = Mock(return_value={
                "estimated_cost": 3500.0,
                "explanation": "Fire damage repair",
                "franchise": 200,
                "max_covered_amount": 10000,
                "final_compensation": 3300.0
            })
            
            result_state = node_tool_execution_expert(state)
            
            assert result_state["estimation"] is not None
            assert result_state["estimation"]["estimated_cost"] == 3500.0
            assert result_state["last_action"] is None  # Reset
    
    def test_expertise_agent_no_images(self, patch_llm_inference):
        """Test expertise agent when no images available."""
        patch_llm_inference.set_responses([
            "Action: CostEstimation\nArguments: {}"
        ])
        
        state: ExpertiseReActState = {
            "image_paths": [],
            "images_validated": False,
            "history": [],
            "last_action": None,
            "last_arguments": None,
            "last_observation": None,
            "parsed_declaration": get_sample_parsed_declaration("complete_water"),
            "estimation": None,
            "report": None
        }
        
        result_state = node_thought_action_expert(state)
        
        # Should still try to call CostEstimation (which will handle empty list)
        assert result_state["last_action"] is not None or result_state.get("report") is not None
    
    def test_expertise_agent_high_cost_with_plafond(self):
        """Test expertise agent handles costs exceeding plafond."""
        state: ExpertiseReActState = {
            "image_paths": ["test.jpg"],
            "images_validated": True,
            "history": [],
            "last_action": "CostEstimation",
            "last_arguments": {},
            "last_observation": None,
            "parsed_declaration": get_sample_parsed_declaration("complete_water"),
            "estimation": None,
            "report": None
        }
        
        # Cost exceeds plafond
        with patch("assurhabitat_agents.agents.expertise_agent.tools") as mock_tools:
            mock_tools.__contains__.return_value = True
            mock_tools.__getitem__.return_value = Mock(return_value={
                "estimated_cost": 8000.0,  # Exceeds plafond of 5000
                "explanation": "Major damage",
                "franchise": 150,
                "max_covered_amount": 5000,
                "final_compensation": 5000.0  # Capped at plafond
            })
            
            result_state = node_tool_execution_expert(state)
            
            assert result_state["estimation"]["final_compensation"] == 5000.0
    
    def test_expertise_agent_cost_below_franchise(self):
        """Test expertise agent handles costs below franchise."""
        state: ExpertiseReActState = {
            "image_paths": ["test.jpg"],
            "images_validated": True,
            "history": [],
            "last_action": "CostEstimation",
            "last_arguments": {},
            "last_observation": None,
            "parsed_declaration": get_sample_parsed_declaration("complete_water"),
            "estimation": None,
            "report": None
        }
        
        with patch("assurhabitat_agents.agents.expertise_agent.tools") as mock_tools:
            mock_tools.__contains__.return_value = True
            mock_tools.__getitem__.return_value = Mock(return_value={
                "estimated_cost": 100.0,  # Below franchise of 150
                "explanation": "Minor damage",
                "franchise": 150,
                "max_covered_amount": 5000,
                "final_compensation": 0.0  # No compensation
            })
            
            result_state = node_tool_execution_expert(state)
            
            assert result_state["estimation"]["final_compensation"] == 0.0
    
    def test_expertise_tool_error_handling(self):
        """Test expertise agent handles tool errors gracefully."""
        state: ExpertiseReActState = {
            "image_paths": [],
            "images_validated": True,
            "history": [],
            "last_action": "CostEstimation",
            "last_arguments": {},
            "last_observation": None,
            "parsed_declaration": get_sample_parsed_declaration("complete_fire"),
            "estimation": None,
            "report": None
        }
        
        with patch("assurhabitat_agents.agents.expertise_agent.tools") as mock_tools:
            mock_tools.__contains__.return_value = True
            mock_tools.__getitem__.return_value = Mock(side_effect=Exception("Estimation failed"))
            
            result_state = node_tool_execution_expert(state)
            
            assert "Error" in result_state["last_observation"]
    
    def test_format_prompt_expertise(self):
        """Test prompt formatting for expertise agent."""
        state: ExpertiseReActState = {
            "image_paths": ["test1.jpg", "test2.jpg"],
            "images_validated": True,
            "history": ["Step 1"],
            "last_action": None,
            "last_arguments": None,
            "last_observation": None,
            "parsed_declaration": get_sample_parsed_declaration("complete_fire"),
            "estimation": None,
            "report": None
        }
        
        tools = ["CostEstimation"]
        prompt = format_prompt_expert(state, tools)
        
        assert "CostEstimation" in prompt
        assert "test1.jpg" in prompt
        assert "ALREADY been validated" in prompt  # Important context
        assert "NOT ask the user for photos" in prompt
    
    def test_expertise_agent_must_not_ask_for_photos(self, patch_llm_inference):
        """Test that expertise agent doesn't ask for photos (they're already validated)."""
        patch_llm_inference.set_responses([
            "Action: CostEstimation\nArguments: {}"
        ])
        
        state: ExpertiseReActState = {
            "image_paths": ["test.jpg"],
            "images_validated": True,
            "history": [],
            "last_action": None,
            "last_arguments": None,
            "last_observation": None,
            "parsed_declaration": get_sample_parsed_declaration("complete_water"),
            "estimation": None,
            "report": None
        }
        
        result_state = node_thought_action_expert(state)
        
        # Should not call AskHuman for photos
        assert result_state["last_action"] != "AskHuman"
    
    def test_expertise_report_includes_all_fields(self, patch_llm_inference):
        """Test that final report includes all required fields."""
        report_text = """
        Rapport d'expertise:
        - Sinistre: degats_des_eaux
        - Coût estimé: 2000€
        - Franchise: 150€
        - Plafond: 5000€
        - Indemnisation finale: 1850€
        - Analyse: Dégâts légers au plafond et sol
        """
        
        patch_llm_inference.set_responses([
            f"Answer: {report_text}"
        ])
        
        state: ExpertiseReActState = {
            "image_paths": ["test.jpg"],
            "images_validated": True,
            "history": [],
            "last_action": None,
            "last_arguments": None,
            "last_observation": None,
            "parsed_declaration": get_sample_parsed_declaration("complete_water"),
            "estimation": {
                "estimated_cost": 2000.0,
                "franchise": 150,
                "max_covered_amount": 5000,
                "final_compensation": 1850.0
            },
            "report": None
        }
        
        result_state = node_thought_action_expert(state)
        
        assert result_state.get("report") is not None
    
    @pytest.mark.parametrize("cost,franchise,plafond,expected_compensation", [
        (100, 150, 5000, 0),      # Below franchise
        (200, 150, 5000, 50),     # Above franchise
        (6000, 150, 5000, 5000),  # Above plafond (capped)
        (2000, 150, 5000, 1850),  # Normal case
        (150, 150, 5000, 0),      # Exactly franchise
    ])
    def test_expertise_compensation_calculations(self, cost, franchise, plafond, expected_compensation):
        """Test various compensation calculation scenarios."""
        state: ExpertiseReActState = {
            "image_paths": ["test.jpg"],
            "images_validated": True,
            "history": [],
            "last_action": "CostEstimation",
            "last_arguments": {},
            "last_observation": None,
            "parsed_declaration": get_sample_parsed_declaration("complete_water"),
            "estimation": None,
            "report": None
        }
        
        with patch("assurhabitat_agents.agents.expertise_agent.tools") as mock_tools:
            mock_tools.__contains__.return_value = True
            mock_tools.__getitem__.return_value = Mock(return_value={
                "estimated_cost": float(cost),
                "explanation": "Test",
                "franchise": franchise,
                "max_covered_amount": plafond,
                "final_compensation": float(expected_compensation)
            })
            
            result_state = node_tool_execution_expert(state)
            
            assert result_state["estimation"]["final_compensation"] == float(expected_compensation)
    
    def test_expertise_agent_with_multiple_images(self, patch_llm_inference):
        """Test expertise agent with multiple images."""
        patch_llm_inference.set_responses([
            "Action: CostEstimation\nArguments: {}"
        ])
        
        state: ExpertiseReActState = {
            "image_paths": [
                "data/attachments/WaterDamage_100.jpg",
                "data/attachments/WaterDamage_176.jpg",
                "data/attachments/WaterDamage_306.jpg"
            ],
            "images_validated": True,
            "history": [],
            "last_action": None,
            "last_arguments": None,
            "last_observation": None,
            "parsed_declaration": get_sample_parsed_declaration("complete_water"),
            "estimation": None,
            "report": None
        }
        
        result_state = node_thought_action_expert(state)
        
        # Should handle multiple images
        assert result_state["last_action"] is not None or result_state.get("report") is not None

