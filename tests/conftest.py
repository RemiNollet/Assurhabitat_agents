"""
Pytest configuration and shared fixtures.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# Add src to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    from tests.fixtures.mock_llm import MockLLM, mock_llm_inference, create_mock_parsed_declaration
    from tests.fixtures.mock_vlm import MockVLM, mock_vlm_inference
    from tests.fixtures.sample_cases import get_sample_parsed_declaration, ALL_CASES
except ImportError:
    # When running from project root
    from fixtures.mock_llm import MockLLM, mock_llm_inference, create_mock_parsed_declaration
    from fixtures.mock_vlm import MockVLM, mock_vlm_inference
    from fixtures.sample_cases import get_sample_parsed_declaration, ALL_CASES


# === Fixtures for mocking LLM/VLM ===

@pytest.fixture
def mock_llm():
    """Fixture that provides a MockLLM instance."""
    return MockLLM()


@pytest.fixture
def mock_vlm():
    """Fixture that provides a MockVLM instance."""
    return MockVLM()


@pytest.fixture
def patch_llm_inference(mock_llm):
    """Patch the llm_inference function with a mock."""
    with patch("assurhabitat_agents.model.llm_model_loading.llm_inference", side_effect=mock_llm):
        yield mock_llm


@pytest.fixture
def patch_vlm_inference(mock_vlm):
    """Patch the vlm_inference function with a mock."""
    with patch("assurhabitat_agents.model.vlm_model_loading.vlm_inference", side_effect=mock_vlm):
        yield mock_vlm


@pytest.fixture
def patch_both_models(patch_llm_inference, patch_vlm_inference):
    """Patch both LLM and VLM together."""
    return {
        "llm": patch_llm_inference,
        "vlm": patch_vlm_inference
    }


# === Fixtures for test data ===

@pytest.fixture
def sample_parsed_declarations():
    """Provides sample parsed declarations for various scenarios."""
    return {
        "complete_water": get_sample_parsed_declaration("complete_water"),
        "incomplete_water": get_sample_parsed_declaration("incomplete_water"),
        "complete_fire": get_sample_parsed_declaration("complete_fire"),
        "complete_theft": get_sample_parsed_declaration("complete_theft"),
        "incomplete_theft": get_sample_parsed_declaration("incomplete_theft"),
    }


@pytest.fixture
def sample_cases():
    """Provides all sample test cases."""
    return ALL_CASES


@pytest.fixture
def temp_yaml_configs(tmp_path):
    """Create temporary YAML config files for testing."""
    sinistres_yaml = tmp_path / "sinistres.yaml"
    garanties_yaml = tmp_path / "garanties.yaml"
    
    sinistres_yaml.write_text("""
sinistres:
  degats_des_eaux:
    nom: "Dégâts des eaux"
    delai_declaration_jours_ouvres: 5
    attendu_assure:
      - prévenir rapidement
      - limiter les dégâts
    process_assurance:
      - ouverture dossier
      - expertise
    cloture:
      - remboursement
    pieces_justificatives:
      - photos dégât
      - rapport plombier
    required_fields:
      - date_sinistre
      - lieu
      - description
      
  incendie_explosion:
    nom: "Incendie et explosion"
    delai_declaration_jours_ouvres: 5
    attendu_assure:
      - prévenir pompiers
      - sécuriser les lieux
    pieces_justificatives:
      - photos dégâts
      - rapport pompiers
    required_fields:
      - date_sinistre
      - lieu
      - description
      
  vol_vandalisme:
    nom: "Vol et vandalisme"
    delai_declaration_jours_ouvres: 2
    attendu_assure:
      - déposer plainte
      - liste des biens volés
    pieces_justificatives:
      - photos
      - dépôt de plainte
    required_fields:
      - date_sinistre
      - lieu
      - description
      - police_report_number
""", encoding="utf-8")
    
    garanties_yaml.write_text("""
garanties:
  degats_des_eaux:
    couverture: ["fuite", "infiltration", "rupture canalisation"]
    exclusions: ["négligence", "usure normale"]
    plafond: 5000
    franchise: 150
    
  incendie_explosion:
    couverture: ["incendie", "explosion", "foudre"]
    exclusions: ["acte volontaire"]
    plafond: 10000
    franchise: 200
    
  vol_vandalisme:
    couverture: ["vol par effraction", "vandalisme"]
    exclusions: ["vol sans effraction", "négligence"]
    plafond: 8000
    franchise: 300
    
pieces_generales:
  - pièce d'identité
  - RIB
  - attestation d'assurance
""", encoding="utf-8")
    
    return {
        "sinistres_path": sinistres_yaml,
        "garanties_path": garanties_yaml
    }


# === Fixtures for DocTools ===

@pytest.fixture
def doc_tools(temp_yaml_configs):
    """Provides a DocTools instance with temporary test config files."""
    from assurhabitat_agents.utils import DocTools
    return DocTools(
        sinistres_path=temp_yaml_configs["sinistres_path"],
        garanties_path=temp_yaml_configs["garanties_path"]
    )


# === Fixtures for mocking human input ===

@pytest.fixture
def mock_ask_human():
    """Mock the ask_human tool to return predetermined responses."""
    def _mock_input(question):
        # Return sensible defaults based on the question
        if "date" in question.lower():
            return "2025-01-07"
        elif "lieu" in question.lower() or "location" in question.lower():
            return "salon"
        elif "police" in question.lower() or "plainte" in question.lower():
            return "12345"
        elif "photo" in question.lower():
            return "data/attachments/test.jpg"
        else:
            return "Information fournie par l'utilisateur"
    
    with patch("assurhabitat_agents.tools.ask_human_tool.ask_human", side_effect=_mock_input):
        yield _mock_input


# === Utility fixtures ===

@pytest.fixture
def sample_image_paths():
    """Provides sample image paths for testing."""
    return {
        "water": "data/attachments/WaterDamage_100.jpg",
        "fire": "data/attachments/FireDamage_31.jpg",
        "theft": "eval/eval_pictures/VOL_01.png",
        "mold": "data/attachments/Mold_Minor_164.jpg",
    }


@pytest.fixture
def mock_guarantee_data():
    """Mock guarantee data for testing."""
    return {
        "degats_des_eaux": {
            "couverture": ["fuite", "infiltration"],
            "exclusions": ["négligence"],
            "plafond": 5000,
            "franchise": 150
        },
        "incendie_explosion": {
            "couverture": ["incendie", "explosion"],
            "exclusions": ["acte volontaire"],
            "plafond": 10000,
            "franchise": 200
        },
        "vol_vandalisme": {
            "couverture": ["vol par effraction"],
            "exclusions": ["vol sans effraction"],
            "plafond": 8000,
            "franchise": 300
        }
    }


# === Pytest configuration ===

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )

