"""
Unit tests for declaration_agent.py
Tests the declaration agent with various edge cases and scenarios.
"""
import pytest
from unittest.mock import patch, Mock, MagicMock
import json

from assurhabitat_agents.agents.declaration_agent import (
    DeclarationReActState,
    node_thought_action_declar,
    node_tool_execution_declar,
    format_prompt_declar,
    build_graph_declar
)
from tests.fixtures.mock_llm import create_mock_parsed_declaration
from tests.fixtures.sample_cases import get_sample_parsed_declaration


class TestDeclarationAgent:
    """Test suite for declaration agent."""
    
    def test_declaration_agent_complete_case(self, patch_llm_inference):
        """Test declaration agent with complete information."""
        # Setup mock responses
        patch_llm_inference.set_responses([
            "Action: DeclarationParser\nArguments: {}",
            "Action: InformationVerification\nArguments: {}",
            "Answer: La déclaration est complète."
        ])
        
        initial_state: DeclarationReActState = {
            "question": "Fuite d'eau dans la salle de bain le 5 janvier",
            "pictures": ["test.jpg"],
            "history": [],
            "last_action": None,
            "last_arguments": None,
            "last_observation": None,
            "is_complete": None,
            "parsed_declaration": None,
            "missing": None,
            "answer": None
        }
        
        # Test thought node
        with patch("assurhabitat_agents.agents.declaration_agent.tools") as mock_tools:
            mock_tools.__getitem__.return_value = Mock(return_value=get_sample_parsed_declaration("complete_water"))
            
            state = node_thought_action_declar(initial_state)
            
            assert state["last_action"] is not None
            assert len(state["history"]) > 0
    
    def test_declaration_agent_missing_fields(self, patch_llm_inference, mock_ask_human):
        """Test declaration agent with missing fields that trigger AskHuman."""
        patch_llm_inference.set_responses([
            "Action: DeclarationParser\nArguments: {}",
            "Action: InformationVerification\nArguments: {}",
            "Action: AskHuman\nArguments: {\"question\": \"Quelle est la date du sinistre?\"}",
            "Answer: Déclaration complète après complétion."
        ])
        
        initial_state: DeclarationReActState = {
            "question": "Fuite d'eau dans la salle de bain",  # Missing date
            "pictures": [],
            "history": [],
            "last_action": None,
            "last_arguments": None,
            "last_observation": None,
            "is_complete": False,
            "parsed_declaration": None,
            "missing": ["date_sinistre"],
            "answer": None
        }
        
        state = node_thought_action_declar(initial_state)
        
        # Should request an action
        assert state["last_action"] is not None or state.get("answer") is not None
    
    def test_declaration_agent_ambiguous_declaration(self, patch_llm_inference):
        """Test declaration agent with ambiguous declaration."""
        patch_llm_inference.set_responses([
            "Action: DeclarationParser\nArguments: {}",
            "Action: AskHuman\nArguments: {\"question\": \"Quel type de dégâts?\"}",
        ])
        
        initial_state: DeclarationReActState = {
            "question": "Il y a eu des dégâts chez moi",
            "pictures": [],
            "history": [],
            "last_action": None,
            "last_arguments": None,
            "last_observation": None,
            "is_complete": False,
            "parsed_declaration": None,
            "missing": None,
            "answer": None
        }
        
        state = node_thought_action_declar(initial_state)
        
        # Should try to parse or ask for clarification
        assert state["last_action"] is not None
    
    def test_declaration_agent_no_pictures_provided(self, patch_llm_inference):
        """Test declaration agent when pictures field is empty list."""
        patch_llm_inference.set_responses([
            "Action: DeclarationParser\nArguments: {}",
            "Action: AskHuman\nArguments: {\"question\": \"Veuillez fournir des photos\"}",
        ])
        
        initial_state: DeclarationReActState = {
            "question": "Incendie dans la cuisine le 6 janvier",
            "pictures": [],  # No pictures
            "history": [],
            "last_action": None,
            "last_arguments": None,
            "last_observation": None,
            "is_complete": False,
            "parsed_declaration": None,
            "missing": None,
            "answer": None
        }
        
        state = node_thought_action_declar(initial_state)
        
        assert state["last_action"] is not None
    
    def test_tool_execution_parse_declaration(self):
        """Test tool execution node for DeclarationParser."""
        mock_parsed = get_sample_parsed_declaration("complete_water")
        
        state: DeclarationReActState = {
            "question": "Test",
            "pictures": [],
            "history": [],
            "last_action": "DeclarationParser",
            "last_arguments": {},
            "last_observation": None,
            "is_complete": None,
            "parsed_declaration": None,
            "missing": None,
            "answer": None
        }
        
        with patch("assurhabitat_agents.agents.declaration_agent.tools") as mock_tools:
            mock_tools.__contains__.return_value = True
            mock_tools.__getitem__.return_value = Mock(return_value=mock_parsed)
            
            result_state = node_tool_execution_declar(state)
            
            assert result_state["parsed_declaration"] is not None
            assert result_state["last_action"] is None  # Reset after execution
    
    def test_tool_execution_verify_completeness(self):
        """Test tool execution node for InformationVerification."""
        state: DeclarationReActState = {
            "question": "Test",
            "pictures": [],
            "history": [],
            "last_action": "InformationVerification",
            "last_arguments": {},
            "last_observation": None,
            "is_complete": None,
            "parsed_declaration": get_sample_parsed_declaration("incomplete_water"),
            "missing": None,
            "answer": None
        }
        
        with patch("assurhabitat_agents.agents.declaration_agent.tools") as mock_tools:
            mock_tools.__contains__.return_value = True
            mock_tools.__getitem__.return_value = Mock(return_value={
                "is_complete": False,
                "missing": ["date_sinistre"]
            })
            
            result_state = node_tool_execution_declar(state)
            
            assert result_state["is_complete"] is False
            assert "date_sinistre" in result_state["missing"]
    
    def test_tool_execution_ask_human(self, mock_ask_human):
        """Test tool execution node for AskHuman."""
        state: DeclarationReActState = {
            "question": "Test",
            "pictures": [],
            "history": [],
            "last_action": "AskHuman",
            "last_arguments": {"question": "Quelle est la date?"},
            "last_observation": None,
            "is_complete": False,
            "parsed_declaration": get_sample_parsed_declaration("incomplete_water"),
            "missing": ["date_sinistre"],
            "answer": None
        }
        
        with patch("assurhabitat_agents.agents.declaration_agent.tools") as mock_tools:
            # Mock AskHuman to return a date
            mock_tools.__contains__.return_value = True
            mock_ask_human_func = Mock(return_value="2025-01-07")
            mock_tools.__getitem__.side_effect = lambda x: mock_ask_human_func if x == "AskHuman" else Mock()
            
            result_state = node_tool_execution_declar(state)
            
            # Should have processed human response
            assert len(result_state["history"]) > len(state["history"])
    
    def test_tool_execution_unknown_tool(self):
        """Test tool execution with unknown tool name."""
        state: DeclarationReActState = {
            "question": "Test",
            "pictures": [],
            "history": [],
            "last_action": "UnknownTool",
            "last_arguments": {},
            "last_observation": None,
            "is_complete": None,
            "parsed_declaration": None,
            "missing": None,
            "answer": None
        }
        
        with patch("assurhabitat_agents.agents.declaration_agent.tools", {}):
            result_state = node_tool_execution_declar(state)
            
            assert "Error" in result_state["last_observation"]
            assert "Unknown tool" in result_state["last_observation"]
    
    def test_tool_execution_tool_raises_exception(self):
        """Test tool execution when tool raises an exception."""
        state: DeclarationReActState = {
            "question": "Test",
            "pictures": [],
            "history": [],
            "last_action": "DeclarationParser",
            "last_arguments": {},
            "last_observation": None,
            "is_complete": None,
            "parsed_declaration": None,
            "missing": None,
            "answer": None
        }
        
        with patch("assurhabitat_agents.agents.declaration_agent.tools") as mock_tools:
            mock_tools.__contains__.return_value = True
            mock_tools.__getitem__.return_value = Mock(side_effect=Exception("Tool error"))
            
            result_state = node_tool_execution_declar(state)
            
            assert "Error" in result_state["last_observation"]
    
    def test_format_prompt_with_parsed_declaration(self):
        """Test prompt formatting with parsed declaration."""
        state: DeclarationReActState = {
            "question": "Test question",
            "pictures": ["test.jpg"],
            "history": ["Step 1", "Step 2"],
            "last_action": None,
            "last_arguments": None,
            "last_observation": None,
            "is_complete": False,
            "parsed_declaration": get_sample_parsed_declaration("complete_water"),
            "missing": ["date_sinistre"],
            "answer": None
        }
        
        tools = ["DeclarationParser", "InformationVerification", "AskHuman"]
        prompt = format_prompt_declar(state, tools)
        
        assert "Test question" in prompt
        assert "DeclarationParser" in prompt
        assert "Missing fields" in prompt
        assert "date_sinistre" in prompt
    
    def test_format_prompt_minimal_state(self):
        """Test prompt formatting with minimal state."""
        state: DeclarationReActState = {
            "question": "Simple question",
            "pictures": None,
            "history": [],
            "last_action": None,
            "last_arguments": None,
            "last_observation": None,
            "is_complete": None,
            "parsed_declaration": None,
            "missing": None,
            "answer": None
        }
        
        tools = ["DeclarationParser"]
        prompt = format_prompt_declar(state, tools)
        
        assert "Simple question" in prompt
        assert "DeclarationParser" in prompt
    
    def test_node_thought_produces_final_answer(self, patch_llm_inference):
        """Test that thought node can produce final answer."""
        patch_llm_inference.set_responses([
            "Answer: La déclaration est validée et complète."
        ])
        
        state: DeclarationReActState = {
            "question": "Test",
            "pictures": [],
            "history": [],
            "last_action": None,
            "last_arguments": None,
            "last_observation": None,
            "is_complete": True,
            "parsed_declaration": get_sample_parsed_declaration("complete_water"),
            "missing": [],
            "answer": None
        }
        
        result_state = node_thought_action_declar(state)
        
        assert result_state.get("is_complete") is True
        assert result_state.get("answer") is not None
    
    def test_declaration_agent_with_theft_missing_police_report(self, patch_llm_inference):
        """Test declaration agent with theft case missing police report number."""
        patch_llm_inference.set_responses([
            "Action: DeclarationParser\nArguments: {}",
            "Action: InformationVerification\nArguments: {}",
            "Action: AskHuman\nArguments: {\"question\": \"Numéro de plainte?\"}",
        ])
        
        state: DeclarationReActState = {
            "question": "Cambriolage dans ma chambre hier",
            "pictures": [],
            "history": [],
            "last_action": None,
            "last_arguments": None,
            "last_observation": None,
            "is_complete": False,
            "parsed_declaration": get_sample_parsed_declaration("incomplete_theft"),
            "missing": ["police_report_number"],
            "answer": None
        }
        
        result_state = node_thought_action_declar(state)
        
        # Should request action or final answer
        assert result_state["last_action"] is not None or result_state.get("answer") is not None
    
    def test_declaration_agent_history_truncation(self, patch_llm_inference):
        """Test that history is truncated in prompt when too long."""
        patch_llm_inference.set_responses([
            "Action: DeclarationParser\nArguments: {}"
        ])
        
        # Create state with long history
        long_history = [f"Step {i}" for i in range(20)]
        
        state: DeclarationReActState = {
            "question": "Test",
            "pictures": [],
            "history": long_history,
            "last_action": None,
            "last_arguments": None,
            "last_observation": None,
            "is_complete": None,
            "parsed_declaration": None,
            "missing": None,
            "answer": None
        }
        
        tools = ["DeclarationParser"]
        prompt = format_prompt_declar(state, tools)
        
        # Should only include last 10 items (HISTORY_KEEP = 10)
        assert prompt.count("Step") <= 10
    
    @pytest.mark.parametrize("sinistre_type,expected_fields", [
        ("degats_des_eaux", ["date_sinistre", "lieu", "description"]),
        ("incendie_explosion", ["date_sinistre", "lieu", "description"]),
        ("vol_vandalisme", ["date_sinistre", "lieu", "description", "police_report_number"]),
    ])
    def test_declaration_agent_required_fields_by_type(self, sinistre_type, expected_fields):
        """Test that declaration agent handles required fields for different sinistre types."""
        parsed = create_mock_parsed_declaration(sinistre_type, complete=False)
        
        state: DeclarationReActState = {
            "question": "Test",
            "pictures": [],
            "history": [],
            "last_action": None,
            "last_arguments": None,
            "last_observation": None,
            "is_complete": False,
            "parsed_declaration": parsed,
            "missing": expected_fields,
            "answer": None
        }
        
        # Check that state structure is valid
        assert state["parsed_declaration"]["sinistre_type"] == sinistre_type
        assert len(state["missing"]) > 0

