from assurhabitat_agents.agents.orchestrator import Orchestrator
from assurhabitat_agents.agents.declaration_agent import run_declar_agent
from assurhabitat_agents.agents.validation_agent import run_valid_agent
from assurhabitat_agents.agents.expertise_agent import run_expert_agent

user_text = input("Please enter your declaration: ")
images_input = input("Please insert your pictures (comma separated paths): ")

image_paths = [p.strip() for p in images_input.split(",") if p.strip()]

orch = Orchestrator(
    declaration_agent=run_declar_agent,
    validation_agent=run_valid_agent,
    expertise_agent=run_expert_agent
)

result = orch.run(user_text=user_text, image_paths=image_paths)

print(result)