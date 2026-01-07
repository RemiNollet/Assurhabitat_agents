"""Test fixtures for assurhabitat_agents tests."""
from .mock_llm import MockLLM, mock_llm_inference, create_mock_parsed_declaration
from .mock_vlm import MockVLM, mock_vlm_inference
from .sample_cases import (
    ALL_CASES,
    get_sample_parsed_declaration,
    COMPLETE_WATER_DAMAGE,
    COMPLETE_FIRE_DAMAGE,
    COMPLETE_THEFT,
    INCOMPLETE_MISSING_DATE,
    EDGE_CASE_NO_IMAGES,
)

__all__ = [
    "MockLLM",
    "MockVLM",
    "mock_llm_inference",
    "mock_vlm_inference",
    "create_mock_parsed_declaration",
    "get_sample_parsed_declaration",
    "ALL_CASES",
    "COMPLETE_WATER_DAMAGE",
    "COMPLETE_FIRE_DAMAGE",
    "COMPLETE_THEFT",
    "INCOMPLETE_MISSING_DATE",
    "EDGE_CASE_NO_IMAGES",
]

