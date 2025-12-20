import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))
from assurhabitat_agents.config.langfuse_config import langfuse, observe
from scoring import score_declaration, score_validation

from assurhabitat_agents.agents.orchestrator import Orchestrator
from assurhabitat_agents.agents.declaration_agent import run_declar_agent
from assurhabitat_agents.agents.validation_agent import run_valid_agent
from assurhabitat_agents.agents.expertise_agent import run_expert_agent

DATASET_NAME = "assurhabitat-golden-dataset"


# =====================================================
# 1. Load Golden Dataset
# =====================================================
with open("/workspace/Assurhabitat_agents/eval/golden_dataset.json", "r") as f:
    golden_cases = json.load(f)


# =====================================================
# 2. Create dataset if not exists
# =====================================================
try:
    langfuse.get_dataset(DATASET_NAME)
    print(f"Dataset '{DATASET_NAME}' already exists.")
except Exception:
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

    # -------- Declaration Agent --------
    decl_score, decl_details = score_declaration(
        output=result["validation"]["parsed_declaration"],
        expected=case["expected_declaration_agent"]
    )

    # -------- Validation Agent --------
    val_score, val_details = score_validation(
        output=result["validation"],
        expected=case["expected_validation_agent"]
    )

    # ---- Log scores properly ----
    langfuse.score(
        name="declaration_agent_score",
        value=decl_score,
        comment=decl_details
    )

    langfuse.score(
        name="validation_agent_score",
        value=val_score,
        comment=val_details
    )

    return {
        "case_id": case["case_id"],
        "scores": {
            "declaration_agent": decl_score,
            "validation_agent": val_score
        }
    }


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

if __name__ == "__main__":

    print("Starting Golden Dataset evaluation...")

    orchestrator = Orchestrator(
        declaration_agent=run_declar_agent,
        validation_agent=run_valid_agent,
        expertise_agent=run_expert_agent
    )

    results = run_evaluation(orchestrator)

    print("\nEvaluation completed")
    for r in results:
        print(r)