import pytest
from pathlib import Path
from src.assurhabitat_agents.utils import DocTools


@pytest.fixture
def doc_tools(tmp_path):
    """
    On crée deux faux fichiers YAML minimaux utilisés par DocTools.
    """
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
""", encoding="utf-8")

    garanties_yaml.write_text("""
garanties:
  degats_des_eaux:
    couverture: ["fuite", "infiltration"]
    exclusions: ["négligence"]
    plafond: 5000
    franchise: 150
pieces_generales:
  - pièce d’identité
  - RIB
""", encoding="utf-8")

    return DocTools(
        sinistres_path=sinistres_yaml,
        garanties_path=garanties_yaml
    )


def test_get_expected_fields(doc_tools):
    result = doc_tools.get_expected_fields("degats_des_eaux")

    assert result["nom"] == "Dégâts des eaux"
    assert result["delai_declaration_jours_ouvres"] == 5
    assert "limiter les dégâts" in result["attendu_assure"]
    assert result["required_fields"] == ["date_sinistre", "lieu", "description"]


def test_get_expected_fields_invalid(doc_tools):
    with pytest.raises(KeyError):
        doc_tools.get_expected_fields("inconnu")


def test_get_guarantee_for_type(doc_tools):
    result = doc_tools.get_guarantee_for_type("degats_des_eaux")

    assert "fuite" in result["couverture"]
    assert result["plafond"] == 5000
    assert result["franchise"] == 150


def test_get_guarantee_invalid(doc_tools):
    with pytest.raises(KeyError):
        doc_tools.get_guarantee_for_type("inconnu")


def test_get_required_documents(doc_tools):
    result = doc_tools.get_required_documents("degats_des_eaux")

    # fusion des pièces spécifiques + globales
    assert "photos dégât" in result["documents"]
    assert "RIB" in result["documents"]
    assert len(result["documents"]) == 4  # pas de duplication


def test_get_required_documents_vol_special_case(tmp_path):
    """
    Test spécifique pour le cas vol_vandalisme.
    """
    sin = tmp_path / "s.yaml"
    gar = tmp_path / "g.yaml"

    sin.write_text("""
sinistres:
  vol_vandalisme:
    pieces_justificatives: ["photos"]
""")

    gar.write_text("""
garanties:
  vol_vandalisme:
    couverture: []
    exclusions: []
    plafond: 0
    franchise: 0
pieces_generales:
  - carte identité
""")

    tools = DocTools(sinistres_path=sin, garanties_path=gar)
    result = tools.get_required_documents("vol_vandalisme")

    assert "Dépôt de plainte" in result["notes"]