import yaml
import re
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Config directory (expects sinistres.yaml and garanties.yaml in a `config` folder
# next to this utils.py file).
CONFIG_DIR = Path(__file__).parent / "config"
SINISTRES_PATH = CONFIG_DIR / "sinistres.yaml"
GARANTIES_PATH = CONFIG_DIR / "garanties.yaml"


def load_yaml(path: Path) -> Dict[str, Any]:
    """
    Load a YAML file and return its content as a Python dict.
    Raises FileNotFoundError when file is missing and ValueError when YAML is invalid.
    """
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        try:
            return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {path}: {e}")


# Load configs once at module import (simple and efficient for a small project).
try:
    SINISTRES_DATA: Dict[str, Any] = load_yaml(SINISTRES_PATH)
except FileNotFoundError:
    SINISTRES_DATA = {}
except ValueError:
    SINISTRES_DATA = {}

try:
    GARANTIES_DATA: Dict[str, Any] = load_yaml(GARANTIES_PATH)
except FileNotFoundError:
    GARANTIES_DATA = {}
except ValueError:
    GARANTIES_DATA = {}


def _normalize_key(key: str) -> str:
    """Normalize a sinistre key for lookups (lowercase, replace spaces)."""
    if not key:
        return ""
    return key.strip().lower().replace(" ", "_")


def get_expected_fields(sinistre_type: str) -> Dict[str, Any]:
    """
    Return the process/expected fields for a given sinistre type.
    This reads from SINISTRES_DATA and returns a dict with defaults.
    Raises KeyError if the type is unknown.
    """
    key = _normalize_key(sinistre_type)
    sinistres = SINISTRES_DATA.get("sinistres", {})
    data = sinistres.get(key)
    if not data:
        raise KeyError(f"Unknown sinistre type in sinistres.yaml: {sinistre_type}")

    # Provide some safe defaults if keys are missing
    return {
        "nom": data.get("nom"),
        "delai_declaration_jours_ouvres": data.get("delai_declaration_jours_ouvres"),
        "attendu_assure": data.get("attendu_assure", []),
        "pieces_justificatives": data.get("pieces_justificatives", []),
        "process_assurance": data.get("process_assurance", []),
        "cloture": data.get("cloture", []),
        # allow YAML to specify required_fields; otherwise keep a minimal set
        "required_fields": data.get("required_fields", ["date_sinistre", "lieu"])
    }


def get_guarantee_for_type(sinistre_type: str) -> Dict[str, Any]:
    """
    Return the guarantee information for a sinistre type from garanties.yaml.
    Raises KeyError if the type is unknown.
    """
    key = _normalize_key(sinistre_type)
    garanties = GARANTIES_DATA.get("garanties", {})
    data = garanties.get(key)
    if not data:
        raise KeyError(f"Unknown sinistre type in garanties.yaml: {sinistre_type}")

    return {
        "couverture": data.get("couverture", []),
        "exclusions": data.get("exclusions", []),
        "plafond": data.get("plafond"),
        "franchise": data.get("franchise"),
    }


def get_required_documents(sinistre_type: str) -> Dict[str, Any]:
    """
    Return required documents for a sinistre type.
    Combines local pieces_justificatives from sinistres.yaml with global pieces_generales.
    Returns a dict: { "documents": [...], "notes": "..." }
    """
    key = _normalize_key(sinistre_type)
    sinistres = SINISTRES_DATA.get("sinistres", {})
    garanties = GARANTIES_DATA

    local = []
    if key in sinistres:
        local = sinistres[key].get("pieces_justificatives", [])

    global_pieces = garanties.get("pieces_generales", []) if garanties else []
    # combine while preserving order and removing duplicates
    combined = []
    for item in (local + global_pieces):
        if item not in combined:
            combined.append(item)

    notes = ""
    if key.startswith("vol"):
        notes = "Dépôt de plainte requis dans les 24h, joindre numéro de procès-verbal."

    return {"documents": combined, "notes": notes}


# Optional helper for consumers: safe_get that doesn't raise KeyError
def safe_get_expected_fields(sinistre_type: str) -> Optional[Dict[str, Any]]:
    """
    Like get_expected_fields but returns None instead of raising KeyError.
    Useful for quick checks.
    """
    try:
        return get_expected_fields(sinistre_type)
    except KeyError:
        return None
    

def parse_output(output: str):
    text = output.strip()

    # Action
    m_action = re.search(r"(?mi)^Action:\s*(?P<tool>[^\n]+)", text)
    m_args = re.search(r"(?mi)^Arguments:\s*(?P<args>[\s\S]+)$", text)

    if m_action:
        tool = m_action.group("tool").strip()
        args = {}

        if m_args:
            raw = m_args.group("args").strip()

            # Trim noise
            for token in ["Observation", "LLM output", "Thought", "Action"]:
                idx = raw.find(token)
                if idx > 0:
                    raw = raw[:idx].strip()

            # JSON only (lists OR dicts)
            try:
                parsed = json.loads(raw)
                if not isinstance(parsed, dict):
                    raise ValueError("Arguments must be a JSON object.")
                args = parsed
            except Exception:
                raise ValueError(f"Invalid JSON arguments: {raw}")

        return ("action", tool, args)

    # Final response
    m_resp = re.search(r"(?mi)^(Réponse|Answer):\s*(?P<ans>[\s\S]+)$", text)
    if m_resp:
        return ("answer", m_resp.group("ans").strip(), None)

    return ("thought", text, None)

