class Orchestrator:
    def __init__(self, declaration_agent, validation_agent, expertise_agent):
        self.declaration_agent = declaration_agent
        self.validation_agent = validation_agent
        self.expertise_agent = expertise_agent

    def run(self, user_text, images_path=None):
        images_path = images_path or []

        print("\n=== STEP 1 : DECLARATION AGENT ===")
        parsed = self.run_declaration_agent(user_text)
        if parsed is None:
            return {"status": "error", "message": "Impossible de comprendre la déclaration."}

        print("\n=== STEP 2 : VALIDATION AGENT ===")
        validation = self.run_validation_agent(parsed, images_path)

        if validation["image_conformity"] is False:
            return {
                "status": "rejected",
                "reason": "Les photos ne correspondent pas au sinistre déclaré.",
                "details": validation
            }

        if validation["is_garanteed"] is False:
            return {
                "status": "not_covered",
                "reason": "Le sinistre n'est pas couvert par le contrat.",
                "details": validation
            }

        print("\n=== STEP 3 : EXPERTISE AGENT ===")
        expertise = self.run_expertise_agent(parsed, images_path)

        return {
            "status": "completed",
            "expertise_report": expertise["report"],
            "estimation": expertise["estimation"],
            "validation": validation,
        }

    # ---- RUN AGENTS ----

    def run_declaration_agent(self, user_text):
        initial_state = {
            "question": user_text,
            "history": [],
            "last_action": None,
            "last_arguments": None,
            "last_observation": None,
            "parsed_declaration": None,
            "is_complete": False,
            "missing": []
        }
        final = self.declaration_agent(initial_state)
        return final.get("parsed_declaration")

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
        return final

    def run_expertise_agent(self, parsed_decl, images):
        initial_state = {
            "images_path": images,
            "history": [],
            "last_action": None,
            "last_arguments": None,
            "last_observation": None,
            "parsed_declaration": parsed_decl,
            "estimation": None,
            "report": None
        }
        final = self.expertise_agent(initial_state)
        return final