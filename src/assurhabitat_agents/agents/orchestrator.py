from assurhabitat_agents.config.langfuse_config import observe

class Orchestrator:
    def __init__(self, declaration_agent, validation_agent, expertise_agent):
        self.declaration_agent = declaration_agent
        self.validation_agent = validation_agent
        self.expertise_agent = expertise_agent
        
    @observe(name="orchestration")
    def run(self, user_text, image_paths=None):
        image_paths = image_paths or []

        print("\n=== STEP 1 : DECLARATION AGENT ===")
        declar_state = self.run_declaration_agent(user_text, image_paths)
        parsed = declar_state.get("parsed_declaration", None)
        if parsed is None:
            return {"status": "error", "message": "Impossible de comprendre la déclaration.", "validation": "Error"}

        print("\n=== STEP 2 : VALIDATION AGENT ===")
        valid_state = self.run_validation_agent(parsed, image_paths)

        if valid_state.get("image_conformity"):
            if valid_state.get("image_conformity")['compatible'] is False:
                return {
                    "status": "rejected",
                    "reason": "Les photos ne correspondent pas au sinistre déclaré.",
                    "details": valid_state,
                    "validation": "Error"
                }

        if valid_state.get("is_garanteed"):
            if valid_state.get("is_garanteed")['match'] is False:
                return {
                    "status": "not_covered",
                    "reason": "Le sinistre n'est pas couvert par le contrat.",
                    "details": valid_state,
                    "validation": "Error"
                }

        print("\n=== STEP 3 : EXPERTISE AGENT ===")
        expertise = self.run_expertise_agent(parsed, image_paths)

        return {
            "status": "completed",
            "expertise_report": expertise["report"],
            "estimation": expertise["estimation"],
            "validation": valid_state,
        }

    # ---- RUN AGENTS ----
    @observe(name="run_declaration_agent")  
    def run_declaration_agent(self, user_text, image_paths):
        initial_state = {
            "question": user_text,
            "pictures": image_paths,
            "history": [],
            "last_action": None,
            "last_arguments": None,
            "last_observation": None,
            "is_complete": False,
            "parsed_declaration": None,
            "missing": []
        }
        final = self.declaration_agent(initial_state)
        print(f"--------Final return of run_declaration_agent: ----------\n {final}")
        return final
        
    @observe(name="run_validation_agent")  
    def run_validation_agent(self, parsed_decl, images):
        initial_state = {
            "images_path": images,
            "history": [],
            "last_action": None,
            "last_arguments": None,
            "last_observation": None,
            "parsed_declaration": parsed_decl,
            "image_conformity": None,
            "guarantee_report": None
        }
        final = self.validation_agent(initial_state)
        print(f"--------Final return of run_validation_agent: ----------\n {final}")
        return final

    @observe(name="run_validation_agent")  
    def run_expertise_agent(self, parsed_decl, images):
        initial_state = {
            "image_paths": images,
            "history": [],
            "last_action": None,
            "last_arguments": None,
            "last_observation": None,
            "parsed_declaration": parsed_decl,
            "estimation": None,
            "report": None,
            "images_validated": True
        }
        final = self.expertise_agent(initial_state)
        print(f"--------Final return of run_expertise_agent: ----------\n {final}")
        return final