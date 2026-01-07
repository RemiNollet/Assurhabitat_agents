# Tests for AssurHabitat Agents

This folder contains comprehensive unit tests for the AssurHabitat Agents project.

## Structure

```
tests/
├── agents/                      # Agent tests
│   ├── test_declaration_agent.py
│   ├── test_validation_agent.py
│   ├── test_expertise_agent.py
│   └── test_orchestrator.py
│
├── tools/                       # Tool tests
│   ├── test_check_conformity.py
│   ├── test_check_guarantee.py
│   └── test_parse_declaration.py
│
├── fixtures/                    # Test fixtures and mocks
│   ├── mock_llm.py             # LLM mock
│   ├── mock_vlm.py             # VLM (Vision Language Model) mock
│   └── sample_cases.py         # Predefined test cases
│
├── conftest.py                 # Pytest configuration and shared fixtures
├── test_utils.py               # Utility tests (existing)
└── test_get_sinistre_type.py   # Existing tests

```

## Running Tests

### All tests
```bash
pytest tests/
```

### Specific module tests
```bash
# Agent tests
pytest tests/agents/

# Tool tests
pytest tests/tools/

# Specific agent test
pytest tests/agents/test_declaration_agent.py

# Specific tool test
pytest tests/tools/test_check_conformity.py
```

### Tests with markers
```bash
# Unit tests only
pytest -m unit

# Integration tests
pytest -m integration

# Slow tests
pytest -m slow
```

### Tests with code coverage
```bash
pytest --cov=src/assurhabitat_agents --cov-report=html tests/
```

### Verbose tests
```bash
pytest -v tests/
```

## Available Fixtures

### LLM/VLM Mocks

- `mock_llm`: MockLLM instance for testing without calling the real model
- `mock_vlm`: MockVLM instance for testing image analysis
- `patch_llm_inference`: Automatic patch for llm_inference
- `patch_vlm_inference`: Automatic patch for vlm_inference
- `patch_both_models`: Patch both LLM and VLM together

### Test Data

- `sample_parsed_declarations`: Parsed declarations for various scenarios
- `sample_cases`: All test cases (complete, incomplete, ambiguous, etc.)
- `temp_yaml_configs`: Temporary YAML files for testing
- `doc_tools`: DocTools instance with test configs
- `sample_image_paths`: Paths to test images
- `mock_guarantee_data`: Mocked guarantee data

### Human Interaction Mock

- `mock_ask_human`: Mock for the AskHuman tool that returns predefined responses

## Test Coverage

### Declaration Agent

✅ Complete case with all information  
✅ Missing fields case (triggers AskHuman)  
✅ Ambiguous declaration  
✅ No photos provided  
✅ Theft/vandalism with missing police report number  
✅ Tool error handling  
✅ History truncation when too long  

### Validation Agent

✅ Images matching declared claim  
✅ Non-conforming images (type mismatch)  
✅ Guarantee verification  
✅ Claim not covered (exclusions)  
✅ No images available  
✅ Compatibility rules (water, fire, theft)  
✅ Tool error handling  

### Expertise Agent

✅ Cost estimation  
✅ Expertise report generation  
✅ Cost exceeding ceiling (capped)  
✅ Cost below deductible (compensation = 0)  
✅ Multiple images  
✅ Various compensation calculations  
✅ Does not request photos (already validated)  

### Orchestrator

✅ Complete successful flow  
✅ Declaration failure  
✅ Non-conforming images  
✅ Claim not covered by guarantee  
✅ Exception handling  
✅ Different claim types (water, fire, theft)  
✅ No images provided  

### Tools

#### CheckConformity
✅ Images of different damage types  
✅ No images  
✅ VLM returns invalid JSON  
✅ VLM returns partial JSON  
✅ Multiple images (uses first one)  

#### CheckGuarantee
✅ Covered claim  
✅ Uncovered claim (exclusions)  
✅ Unknown claim type  
✅ LLM returns invalid JSON  
✅ Ambiguous cases  

#### ParseDeclaration
✅ Clear water damage declaration  
✅ Fire declaration  
✅ Theft with police report number  
✅ Ambiguous declaration  
✅ Incomplete declaration (missing fields)  
✅ Very detailed declaration  
✅ Minimal declaration  
✅ LLM returns invalid JSON  
✅ Merging existing JSON + new info  

## Best Practices

1. **Test isolation**: Each test is independent and doesn't affect others
2. **Mocks**: Use mocks for LLM/VLM to avoid real API calls
3. **Fixtures**: Reuse fixtures to avoid duplication
4. **Edge cases**: Test error cases and edge cases
5. **Parametrize**: Use `@pytest.mark.parametrize` to test multiple scenarios

## Adding New Tests

### For a new agent

```python
from tests.fixtures import MockLLM, get_sample_parsed_declaration

def test_my_agent(patch_llm_inference):
    patch_llm_inference.set_responses([
        "Action: MyTool\nArguments: {}"
    ])
    
    state = {...}
    result = my_agent_function(state)
    
    assert result["expected_field"] == expected_value
```

### For a new tool

```python
def test_my_tool(patch_llm_inference):
    result = my_tool(param1, param2)
    
    assert "expected_key" in result
    assert result["expected_key"] == expected_value
```

## Debugging

### View test outputs
```bash
pytest -s tests/
```

### View detailed logs
```bash
pytest --log-cli-level=DEBUG tests/
```

### Stop on first failure
```bash
pytest -x tests/
```

### Rerun failed tests
```bash
pytest --lf tests/
```

## Current Code Coverage

Tests cover:
- ✅ All agents (declaration, validation, expertise, orchestrator)
- ✅ All tools (parse_declaration, check_conformity, check_guarantee)
- ✅ Utilities (utils.py)
- ✅ Edge cases and errors
- ✅ Different claim types

## Maintenance

- Update tests when business logic changes
- Add tests for each new edge case discovered
- Keep mocks in sync with real interfaces
- Document new test cases in sample_cases.py

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Pytest fixtures](https://docs.pytest.org/en/stable/fixture.html)
