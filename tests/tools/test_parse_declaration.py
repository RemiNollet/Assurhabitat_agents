"""
Unit tests for parse_declaration_tool.py
Tests declaration parsing and classification.
"""
import pytest
from unittest.mock import patch
import json

from assurhabitat_agents.tools.parse_declaration_tool import parse_declaration, _safe_parse_json


class TestParseDeclaration:
    """Test suite for parse_declaration tool."""
    
    def test_parse_water_damage_declaration(self, patch_llm_inference):
        """Test parsing a clear water damage declaration."""
        patch_llm_inference.set_responses([
            json.dumps({
                "sinistre_type": "degats_des_eaux",
                "sinistre_confidence": 0.95,
                "sinistre_explain": "Water leak detected",
                "candidates": [{"type": "degats_des_eaux", "score": 0.95}],
                "extracted": {
                    "date_sinistre": "2025-01-05",
                    "lieu": "salle de bain",
                    "description": "Fuite d'eau au plafond",
                    "biens_impactes": ["plafond", "sol"]
                }
            })
        ])
        
        result = parse_declaration(
            "Fuite d'eau dans la salle de bain le 5 janvier 2025, dégâts au plafond et au sol"
        )
        
        assert result["sinistre_type"] == "degats_des_eaux"
        assert result["sinistre_confidence"] > 0.9
        assert "extracted" in result
        assert result["extracted"]["date_sinistre"] == "2025-01-05"
        assert result["extracted"]["lieu"] == "salle de bain"
    
    def test_parse_fire_damage_declaration(self, patch_llm_inference):
        """Test parsing a fire damage declaration."""
        patch_llm_inference.set_responses([
            json.dumps({
                "sinistre_type": "incendie_explosion",
                "sinistre_confidence": 0.98,
                "sinistre_explain": "Kitchen fire",
                "candidates": [{"type": "incendie_explosion", "score": 0.98}],
                "extracted": {
                    "date_sinistre": "2025-01-06",
                    "lieu": "cuisine",
                    "description": "Incendie dans la cuisine, four et mur brûlés",
                    "biens_impactes": ["four", "mur"]
                }
            })
        ])
        
        result = parse_declaration(
            "Un incendie s'est déclaré dans ma cuisine le 6 janvier 2025"
        )
        
        assert result["sinistre_type"] == "incendie_explosion"
        assert result["extracted"]["lieu"] == "cuisine"
    
    def test_parse_theft_declaration_with_police_report(self, patch_llm_inference):
        """Test parsing theft declaration with police report number."""
        patch_llm_inference.set_responses([
            json.dumps({
                "sinistre_type": "vol_vandalisme",
                "sinistre_confidence": 0.96,
                "sinistre_explain": "Break-in detected",
                "candidates": [{"type": "vol_vandalisme", "score": 0.96}],
                "extracted": {
                    "date_sinistre": "2025-01-07",
                    "lieu": "chambre",
                    "description": "Effraction avec vol",
                    "biens_impactes": ["porte", "télévision"],
                    "police_report_number": "12345"
                }
            })
        ])
        
        result = parse_declaration(
            "Cambriolage dans la chambre le 7 janvier, numéro de plainte 12345"
        )
        
        assert result["sinistre_type"] == "vol_vandalisme"
        assert "police_report_number" in result["extracted"]
        assert result["extracted"]["police_report_number"] == "12345"
    
    def test_parse_ambiguous_declaration(self, patch_llm_inference):
        """Test parsing an ambiguous or unclear declaration."""
        patch_llm_inference.set_responses([
            json.dumps({
                "sinistre_type": "ambiguous",
                "sinistre_confidence": 0.3,
                "sinistre_explain": "Unclear damage type",
                "candidates": [
                    {"type": "degats_des_eaux", "score": 0.4},
                    {"type": "incendie_explosion", "score": 0.3}
                ],
                "extracted": {
                    "date_sinistre": None,
                    "lieu": None,
                    "description": "Il y a eu des dégâts",
                    "biens_impactes": []
                }
            })
        ])
        
        result = parse_declaration("Il y a eu des dégâts chez moi")
        
        assert result["sinistre_type"] == "ambiguous"
        assert result["sinistre_confidence"] < 0.5
        assert len(result["candidates"]) > 0
    
    def test_parse_incomplete_declaration_missing_date(self, patch_llm_inference):
        """Test parsing declaration with missing date."""
        patch_llm_inference.set_responses([
            json.dumps({
                "sinistre_type": "degats_des_eaux",
                "sinistre_confidence": 0.92,
                "sinistre_explain": "Water leak, date not specified",
                "candidates": [{"type": "degats_des_eaux", "score": 0.92}],
                "extracted": {
                    "date_sinistre": None,
                    "lieu": "cuisine",
                    "description": "Fuite d'eau importante",
                    "biens_impactes": ["sol"]
                }
            })
        ])
        
        result = parse_declaration("Fuite d'eau dans la cuisine")
        
        assert result["sinistre_type"] == "degats_des_eaux"
        assert result["extracted"]["date_sinistre"] is None
        assert result["extracted"]["lieu"] is not None
    
    def test_parse_very_detailed_declaration(self, patch_llm_inference):
        """Test parsing a very detailed declaration."""
        detailed_text = """Le 5 janvier 2025 vers 14h30, j'ai constaté une importante fuite d'eau 
        provenant du plafond de ma salle de bain. L'eau s'est infiltrée et a endommagé 
        le plafond, le sol et le meuble sous-lavabo."""
        
        patch_llm_inference.set_responses([
            json.dumps({
                "sinistre_type": "degats_des_eaux",
                "sinistre_confidence": 0.99,
                "sinistre_explain": "Detailed water leak description",
                "candidates": [{"type": "degats_des_eaux", "score": 0.99}],
                "extracted": {
                    "date_sinistre": "2025-01-05",
                    "lieu": "salle de bain",
                    "description": detailed_text,
                    "biens_impactes": ["plafond", "sol", "meuble sous-lavabo"]
                }
            })
        ])
        
        result = parse_declaration(detailed_text)
        
        assert result["sinistre_type"] == "degats_des_eaux"
        assert result["sinistre_confidence"] > 0.95
        assert len(result["extracted"]["biens_impactes"]) >= 3
    
    def test_parse_minimal_declaration(self, patch_llm_inference):
        """Test parsing a minimal declaration."""
        patch_llm_inference.set_responses([
            json.dumps({
                "sinistre_type": "degats_des_eaux",
                "sinistre_confidence": 0.75,
                "sinistre_explain": "Minimal info",
                "candidates": [{"type": "degats_des_eaux", "score": 0.75}],
                "extracted": {
                    "date_sinistre": None,
                    "lieu": None,
                    "description": "fuite",
                    "biens_impactes": []
                }
            })
        ])
        
        result = parse_declaration("fuite")
        
        assert result["sinistre_type"] in ["degats_des_eaux", "ambiguous"]
        assert "extracted" in result
    
    def test_parse_llm_returns_invalid_json(self, patch_llm_inference):
        """Test parsing when LLM returns invalid JSON."""
        patch_llm_inference.set_responses([
            "This is not valid JSON at all"
        ])
        
        result = parse_declaration("Test declaration")
        
        # Should return fallback structure with error info
        assert result["sinistre_type"] == "ambiguous"
        assert result["sinistre_confidence"] == 0.0
        assert "error" in result["sinistre_explain"].lower() or "parse" in result["sinistre_explain"].lower()
    
    def test_parse_llm_returns_partial_json(self, patch_llm_inference):
        """Test parsing when LLM returns incomplete JSON."""
        patch_llm_inference.set_responses([
            json.dumps({
                "sinistre_type": "degats_des_eaux",
                # Missing other required fields
            })
        ])
        
        result = parse_declaration("Fuite d'eau")
        
        # Should normalize with defaults
        assert result["sinistre_type"] == "degats_des_eaux"
        assert "extracted" in result
        assert "date_sinistre" in result["extracted"]
    
    def test_safe_parse_json_with_dict(self):
        """Test _safe_parse_json with already parsed dict."""
        input_dict = {"key": "value"}
        result = _safe_parse_json(input_dict)
        assert result == input_dict
    
    def test_safe_parse_json_with_valid_json_string(self):
        """Test _safe_parse_json with valid JSON string."""
        json_str = '{"key": "value"}'
        result = _safe_parse_json(json_str)
        assert result == {"key": "value"}
    
    def test_safe_parse_json_with_text_before_json(self):
        """Test _safe_parse_json with text before JSON."""
        mixed_str = 'Some text before {"key": "value"}'
        result = _safe_parse_json(mixed_str)
        assert result == {"key": "value"}
    
    def test_safe_parse_json_with_invalid_input(self):
        """Test _safe_parse_json with completely invalid input."""
        with pytest.raises(ValueError):
            _safe_parse_json("Not JSON at all, no braces")
    
    def test_safe_parse_json_with_non_string_non_dict(self):
        """Test _safe_parse_json with invalid type."""
        with pytest.raises(ValueError):
            _safe_parse_json(12345)
    
    @pytest.mark.parametrize("input_text,expected_type", [
        ("Fuite d'eau dans la salle de bain", "degats_des_eaux"),
        ("Incendie dans la cuisine", "incendie_explosion"),
        ("Cambriolage avec effraction", "vol_vandalisme"),
        ("Des dégâts quelque part", "ambiguous"),
    ])
    def test_parse_various_declarations(self, patch_llm_inference, input_text, expected_type):
        """Test parsing various types of declarations."""
        patch_llm_inference.set_responses([
            json.dumps({
                "sinistre_type": expected_type,
                "sinistre_confidence": 0.9,
                "sinistre_explain": "Test",
                "candidates": [{"type": expected_type, "score": 0.9}],
                "extracted": {
                    "date_sinistre": "2025-01-07",
                    "lieu": "test",
                    "description": input_text,
                    "biens_impactes": []
                }
            })
        ])
        
        result = parse_declaration(input_text)
        assert result["sinistre_type"] == expected_type
    
    def test_parse_declaration_with_existing_json_merge(self, patch_llm_inference):
        """Test parsing when input contains existing JSON + new info."""
        existing_json = json.dumps({
            "sinistre_type": "vol_vandalisme",
            "extracted": {
                "date_sinistre": None,
                "lieu": "chambre",
                "description": "effraction"
            }
        })
        
        new_info = "La date était le 7 janvier"
        combined_input = f"{existing_json}\n\n{new_info}"
        
        patch_llm_inference.set_responses([
            json.dumps({
                "sinistre_type": "vol_vandalisme",
                "sinistre_confidence": 0.95,
                "sinistre_explain": "Merged info",
                "candidates": [{"type": "vol_vandalisme", "score": 0.95}],
                "extracted": {
                    "date_sinistre": "2025-01-07",
                    "lieu": "chambre",
                    "description": "effraction",
                    "biens_impactes": [],
                    "police_report_number": None
                }
            })
        ])
        
        result = parse_declaration(combined_input)
        
        assert result["sinistre_type"] == "vol_vandalisme"
        assert result["extracted"]["date_sinistre"] == "2025-01-07"

