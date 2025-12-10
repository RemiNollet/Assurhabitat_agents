from assurhabitat_agents.agents.orchestrator import Orchestrator
from assurhabitat_agents.agents.declaration_agent import run_declar_agent
from assurhabitat_agents.agents.validation_agent import run_valid_agent
from assurhabitat_agents.agents.expertise_agent import run_expert_agent



orch = Orchestrator(
    declaration_agent=run_declar_agent,
    validation_agent=run_valid_agent,
    expertise_agent=run_expert_agent
)

result = orch.run(
    user_text=input("Please enter your declaration: "),
    image_paths=input("Please insert your pictures: (local path to image for testing)")
)

print(result)