from assurhabitat_agents.agents.orchestrator import Orchestrator
from assurhabitat_agents.agents.declaration_agent import run_graph_declaration
from assurhabitat_agents.agents.validation_agent import run_graph_validation
from assurhabitat_agents.agents.expertise_agent import run_graph_expertise



orch = Orchestrator(
    declaration_agent=run_graph_declaration,
    validation_agent=run_graph_validation,
    expertise_agent=run_graph_expertise
)

result = orch.run(
    user_text="On m’a cambriolé ce matin...",
    images_path=["photos/velux.jpg", "photos/chambre.jpg"]
)

print(result)