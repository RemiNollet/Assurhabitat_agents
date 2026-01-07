"""
Unit tests for orchestrator.py
Tests the orchestrator that coordinates all agents.
"""
import pytest
from unittest.mock import patch, Mock, MagicMock
import json

from assurhabitat_agents.agents.orchestrator import Orchestrator
from tests.fixtures.sample_cases import get_sample_parsed_declaration


class TestOrchestrator:
    """Test suite for orchestrator."""
    
    @pytest.fixture
    def mock_agents(self):
        """Create mock agents for testing."""
        declaration_agent = Mock()
        validation_agent = Mock()
        expertise_agent = Mock()
        
        return {
            "declaration": declaration_agent,
            "validation": validation_agent,
            "expertise": expertise_agent
        }
    
    @pytest.fixture
    def orchestrator(self, mock_agents):
        """Create orchestrator with mock agents."""
        return Orchestrator(
            declaration_agent=mock_agents["declaration"],
            validation_agent=mock_agents["validation"],
            expertise_agent=mock_agents["expertise"]
        )
    
    def test_orchestrator_complete_success_flow(self, orchestrator, mock_agents):
        """Test orchestrator with successful complete flow."""
        # Mock declaration agent
        mock_agents["declaration"].return_value = {
            "parsed_declaration": get_sample_parsed_declaration("complete_water"),
            "is_complete": True,
            "missing": [],
            "answer": "Declaration complete"
        }
        
        # Mock validation agent
        mock_agents["validation"].return_value = {
            "image_conformity": {"compatible": True, "detected_damage_types": ["water"]},
            "guarantee_report": {"guaranteed": True, "description": "Covered"}
        }
        
        # Mock expertise agent
        mock_agents["expertise"].return_value = {
            "estimation": {
                "estimated_cost": 2000.0,
                "franchise": 150,
                "final_compensation": 1850.0
            },
            "report": "Expertise complete"
        }
        
        result = orchestrator.run(
            user_text="Fuite d'eau dans la salle de bain",
            image_paths=["test.jpg"]
        )
        
        assert result["status"] == "completed"
        assert "expertise_report" in result
        assert result["validation"]["image_conformity"]["compatible"] is True
        assert mock_agents["declaration"].call_count == 1
        assert mock_agents["validation"].call_count == 1
        assert mock_agents["expertise"].call_count == 1
    
    def test_orchestrator_declaration_fails(self, orchestrator, mock_agents):
        """Test orchestrator when declaration agent fails."""
        mock_agents["declaration"].return_value = {
            "parsed_declaration": None,
            "is_complete": False,
            "answer": None
        }
        
        result = orchestrator.run(
            user_text="Unclear text",
            image_paths=[]
        )
        
        assert result["status"] == "error"
        assert "Impossible de comprendre" in result["message"]
        assert mock_agents["validation"].call_count == 0  # Should not reach validation
        assert mock_agents["expertise"].call_count == 0   # Should not reach expertise
    
    def test_orchestrator_image_conformity_fails(self, orchestrator, mock_agents):
        """Test orchestrator when images don't match declaration."""
        mock_agents["declaration"].return_value = {
            "parsed_declaration": get_sample_parsed_declaration("complete_water"),
            "is_complete": True,
            "missing": [],
            "answer": "Complete"
        }
        
        mock_agents["validation"].return_value = {
            "image_conformity": {
                "compatible": False,
                "detected_damage_types": ["fire"]
            },
            "guarantee_report": None
        }
        
        result = orchestrator.run(
            user_text="Water damage",
            image_paths=["fire_image.jpg"]
        )
        
        assert result["status"] == "rejected"
        assert "photos ne correspondent pas" in result["reason"]
        assert mock_agents["expertise"].call_count == 0  # Should not reach expertise
    
    def test_orchestrator_not_covered_by_guarantee(self, orchestrator, mock_agents):
        """Test orchestrator when sinistre is not covered."""
        mock_agents["declaration"].return_value = {
            "parsed_declaration": get_sample_parsed_declaration("complete_water"),
            "is_complete": True,
            "missing": [],
            "answer": "Complete"
        }
        
        mock_agents["validation"].return_value = {
            "image_conformity": {"compatible": True, "detected_damage_types": ["water"]},
            "is_garanteed": {"match": False},
            "guarantee_report": {"guaranteed": False, "description": "Excluded"}
        }
        
        result = orchestrator.run(
            user_text="Water damage due to negligence",
            image_paths=["water.jpg"]
        )
        
        assert result["status"] == "not_covered"
        assert "pas couvert" in result["reason"]
        assert mock_agents["expertise"].call_count == 0  # Should not reach expertise
    
    def test_orchestrator_with_no_images(self, orchestrator, mock_agents):
        """Test orchestrator when no images provided."""
        mock_agents["declaration"].return_value = {
            "parsed_declaration": get_sample_parsed_declaration("complete_water"),
            "is_complete": True,
            "missing": [],
            "answer": "Complete"
        }
        
        mock_agents["validation"].return_value = {
            "image_conformity": {"compatible": True, "detected_damage_types": []},
            "guarantee_report": {"guaranteed": True}
        }
        
        mock_agents["expertise"].return_value = {
            "estimation": {"estimated_cost": 0, "final_compensation": 0},
            "report": "No images available"
        }
        
        result = orchestrator.run(
            user_text="Water damage",
            image_paths=None  # No images
        )
        
        # Should still proceed but with limitations
        assert result["status"] in ["completed", "error"]
    
    def test_orchestrator_run_declaration_agent_method(self, orchestrator, mock_agents):
        """Test run_declaration_agent method."""
        mock_agents["declaration"].return_value = {
            "parsed_declaration": get_sample_parsed_declaration("complete_fire"),
            "is_complete": True
        }
        
        result = orchestrator.run_declaration_agent(
            user_text="Fire in kitchen",
            image_paths=["fire.jpg"]
        )
        
        assert result["parsed_declaration"] is not None
        assert result["parsed_declaration"]["sinistre_type"] == "incendie_explosion"
    
    def test_orchestrator_run_validation_agent_method(self, orchestrator, mock_agents):
        """Test run_validation_agent method."""
        mock_agents["validation"].return_value = {
            "image_conformity": {"compatible": True},
            "guarantee_report": {"guaranteed": True}
        }
        
        parsed_decl = get_sample_parsed_declaration("complete_water")
        result = orchestrator.run_validation_agent(
            parsed_decl=parsed_decl,
            images=["water.jpg"]
        )
        
        assert result["image_conformity"] is not None
        assert result["guarantee_report"] is not None
    
    def test_orchestrator_run_expertise_agent_method(self, orchestrator, mock_agents):
        """Test run_expertise_agent method."""
        mock_agents["expertise"].return_value = {
            "estimation": {
                "estimated_cost": 3000.0,
                "final_compensation": 2800.0
            },
            "report": "Full expertise report"
        }
        
        parsed_decl = get_sample_parsed_declaration("complete_fire")
        result = orchestrator.run_expertise_agent(
            parsed_decl=parsed_decl,
            images=["fire.jpg"]
        )
        
        assert result["estimation"] is not None
        assert result["report"] is not None
    
    def test_orchestrator_handles_agent_exceptions(self, orchestrator, mock_agents):
        """Test orchestrator handles exceptions from agents."""
        mock_agents["declaration"].side_effect = Exception("Agent error")
        
        with pytest.raises(Exception):
            orchestrator.run(
                user_text="Test",
                image_paths=[]
            )
    
    def test_orchestrator_with_theft_complete_flow(self, orchestrator, mock_agents):
        """Test orchestrator with theft case (includes police report)."""
        mock_agents["declaration"].return_value = {
            "parsed_declaration": get_sample_parsed_declaration("complete_theft"),
            "is_complete": True,
            "missing": [],
            "answer": "Complete"
        }
        
        mock_agents["validation"].return_value = {
            "image_conformity": {
                "compatible": True,
                "detected_damage_types": ["impact", "theft_signs"]
            },
            "guarantee_report": {"guaranteed": True, "description": "Break-in covered"}
        }
        
        mock_agents["expertise"].return_value = {
            "estimation": {
                "estimated_cost": 5000.0,
                "franchise": 300,
                "final_compensation": 4700.0
            },
            "report": "Theft expertise complete"
        }
        
        result = orchestrator.run(
            user_text="Break-in with theft, police report 12345",
            image_paths=["broken_door.jpg"]
        )
        
        assert result["status"] == "completed"
        assert result["expertise_report"] == "Theft expertise complete"
    
    def test_orchestrator_with_fire_complete_flow(self, orchestrator, mock_agents):
        """Test orchestrator with fire damage case."""
        mock_agents["declaration"].return_value = {
            "parsed_declaration": get_sample_parsed_declaration("complete_fire"),
            "is_complete": True,
            "missing": [],
            "answer": "Complete"
        }
        
        mock_agents["validation"].return_value = {
            "image_conformity": {
                "compatible": True,
                "detected_damage_types": ["fire", "soot"]
            },
            "guarantee_report": {"guaranteed": True, "description": "Fire covered"}
        }
        
        mock_agents["expertise"].return_value = {
            "estimation": {
                "estimated_cost": 8000.0,
                "franchise": 200,
                "max_covered_amount": 10000,
                "final_compensation": 7800.0
            },
            "report": "Fire damage expertise"
        }
        
        result = orchestrator.run(
            user_text="Fire in kitchen",
            image_paths=["fire_damage.jpg"]
        )
        
        assert result["status"] == "completed"
        assert result["estimation"]["estimated_cost"] == 8000.0
    
    def test_orchestrator_validation_status_field(self, orchestrator, mock_agents):
        """Test that orchestrator includes validation status in result."""
        mock_agents["declaration"].return_value = {
            "parsed_declaration": get_sample_parsed_declaration("complete_water"),
            "is_complete": True,
            "missing": [],
            "answer": "Complete"
        }
        
        validation_result = {
            "image_conformity": {"compatible": True, "detected_damage_types": ["water"]},
            "guarantee_report": {"guaranteed": True}
        }
        mock_agents["validation"].return_value = validation_result
        
        mock_agents["expertise"].return_value = {
            "estimation": {"estimated_cost": 2000, "final_compensation": 1850},
            "report": "Report"
        }
        
        result = orchestrator.run(
            user_text="Water damage",
            image_paths=["water.jpg"]
        )
        
        assert "validation" in result
        assert result["validation"] == validation_result
    
    @pytest.mark.parametrize("sinistre_type,expected_status", [
        ("complete_water", "completed"),
        ("complete_fire", "completed"),
        ("complete_theft", "completed"),
    ])
    def test_orchestrator_various_sinistre_types(self, orchestrator, mock_agents, sinistre_type, expected_status):
        """Test orchestrator with various sinistre types."""
        mock_agents["declaration"].return_value = {
            "parsed_declaration": get_sample_parsed_declaration(sinistre_type),
            "is_complete": True,
            "missing": [],
            "answer": "Complete"
        }
        
        mock_agents["validation"].return_value = {
            "image_conformity": {"compatible": True, "detected_damage_types": ["test"]},
            "guarantee_report": {"guaranteed": True}
        }
        
        mock_agents["expertise"].return_value = {
            "estimation": {"estimated_cost": 1000, "final_compensation": 850},
            "report": "Report"
        }
        
        result = orchestrator.run(
            user_text="Test",
            image_paths=["test.jpg"]
        )
        
        assert result["status"] == expected_status
    
    def test_orchestrator_image_paths_default_to_empty(self, orchestrator, mock_agents):
        """Test that image_paths defaults to empty list when None."""
        mock_agents["declaration"].return_value = {
            "parsed_declaration": None,
            "is_complete": False
        }
        
        # Call without image_paths
        result = orchestrator.run(user_text="Test")
        
        # Should default to empty list (not crash)
        assert result["status"] == "error"

