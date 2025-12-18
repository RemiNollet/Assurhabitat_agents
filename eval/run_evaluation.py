import json
from assurhabitat_agents.config.langfuse_config import langfuse, observe
from assurhabitat_agents.agents.orchestrator import Orchestrator
from scoring import score_declaration, score_validation

DATASET_NAME = "assurhabitat-golden-dataset"


# =====================================================
# 1. Load Golden Dataset
# =====================================================
with open("golden_dataset.json", "r") as f:
    golden_cases = json.load(f)


# =====================================================
# 2. Create dataset if not exists
# =====================================================
existing = langfuse.get_datasets()
if DATASET_NAME not in [d.name for d in existing]:
    langfuse.create_dataset(
        name=DATASET_NAME,
        description="Golden dataset for AssurHabitat agents evaluation",
        metadata={
            "domain": "insurance",
            "agents": ["declaration", "validation", "expertise"],
            "author": "RemiNollet"
        }
    )

    for case in golden_cases:
        langfuse.create_dataset_item(
            dataset_name=DATASET_NAME,
            input=case["input"],
            expected_output={
                "expected_declaration_agent": case["expected_declaration_agent"],
                "expected_validation_agent": case["expected_validation_agent"]
            },
            metadata={
                "case_id": case["case_id"],
                "sinistre_family": case["sinistre_family"]
            }
        )

    print("Langfuse dataset initialized.")


# =====================================================
# 3. Evaluation run
# =====================================================
@observe(name="golden_dataset_evaluation")
def evaluate_case(case, orchestrator):
    result = orchestrator.run(
        user_text=case["input"]["user_text"],
        image_paths=case["input"]["image_paths"]
    )

    scores = {}

    # -------- Declaration Agent --------
    decl_score, decl_details = score_declaration(
        output=result["validation"]["parsed_declaration"],
        expected=case["expected_declaration_agent"]
    )

    scores["declaration_agent"] = {
        "score": decl_score,
        "details": decl_details
    }

    # -------- Validation Agent --------
    val_score, val_details = score_validation(
        output=result["validation"],
        expected=case["expected_validation_agent"]
    )

    scores["validation_agent"] = {
        "score": val_score,
        "details": val_details
    }

    return scores


# =====================================================
# 4. Run evaluation on all cases
# =====================================================
def run_evaluation(orchestrator):
    results = []

    for case in golden_cases:
        scores = evaluate_case(case, orchestrator)
        results.append({
            "case_id": case["case_id"],
            "scores": scores
        })

    return results