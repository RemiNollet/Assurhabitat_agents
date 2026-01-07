"""
Sample test cases for different scenarios.
Includes complete declarations, incomplete declarations, and edge cases.
"""


# === Complete declarations ===

COMPLETE_WATER_DAMAGE = {
    "user_text": "Il y a eu une fuite d'eau dans ma salle de bain le 5 janvier 2025. L'eau a endommagé le plafond et le sol.",
    "expected_type": "degats_des_eaux",
    "image_paths": ["data/attachments/WaterDamage_100.jpg"],
    "complete": True
}

COMPLETE_FIRE_DAMAGE = {
    "user_text": "Un incendie s'est déclaré dans ma cuisine le 6 janvier 2025. Le four et une partie du mur sont brûlés.",
    "expected_type": "incendie_explosion",
    "image_paths": ["data/attachments/FireDamage_31.jpg"],
    "complete": True
}

COMPLETE_THEFT = {
    "user_text": "Cambriolage chez moi le 7 janvier 2025 dans la chambre. La porte a été forcée. Numéro de plainte: 12345",
    "expected_type": "vol_vandalisme",
    "image_paths": ["eval/eval_pictures/VOL_01.png"],
    "complete": True
}


# === Incomplete declarations (missing fields) ===

INCOMPLETE_MISSING_DATE = {
    "user_text": "Il y a eu une fuite d'eau dans ma salle de bain. L'eau a endommagé le plafond.",
    "expected_type": "degats_des_eaux",
    "missing_fields": ["date_sinistre"],
    "image_paths": ["data/attachments/WaterDamage_176.jpg"],
    "complete": False
}

INCOMPLETE_MISSING_LOCATION = {
    "user_text": "Un incendie s'est déclaré hier soir. Des dégâts importants.",
    "expected_type": "incendie_explosion",
    "missing_fields": ["lieu"],
    "image_paths": ["data/attachments/FireDamage_45.jpg"],
    "complete": False
}

INCOMPLETE_MISSING_POLICE_REPORT = {
    "user_text": "Cambriolage chez moi ce matin dans le salon. La fenêtre a été brisée.",
    "expected_type": "vol_vandalisme",
    "missing_fields": ["police_report_number"],
    "image_paths": ["eval/eval_pictures/VOL_02.png"],
    "complete": False
}

INCOMPLETE_MULTIPLE_MISSING = {
    "user_text": "Il y a eu des dégâts chez moi.",
    "expected_type": "ambiguous",
    "missing_fields": ["date_sinistre", "lieu", "description"],
    "image_paths": [],
    "complete": False
}


# === Ambiguous declarations ===

AMBIGUOUS_UNCLEAR_TYPE = {
    "user_text": "Il y a eu des dégâts dans ma maison, je ne sais pas trop ce qui s'est passé.",
    "expected_type": "ambiguous",
    "image_paths": [],
    "complete": False
}

AMBIGUOUS_CONTRADICTORY = {
    "user_text": "Il y a eu du feu et de l'eau dans mon salon hier.",
    "expected_type": "ambiguous",
    "image_paths": ["data/attachments/WaterDamage_79.jpg"],
    "complete": False
}


# === Edge cases ===

EDGE_CASE_NO_IMAGES = {
    "user_text": "Fuite d'eau importante le 5 janvier dans la cuisine, dégâts au plafond et au sol.",
    "expected_type": "degats_des_eaux",
    "image_paths": [],
    "complete": True,
    "should_ask_for_images": True
}

EDGE_CASE_WRONG_IMAGE_TYPE = {
    "user_text": "Incendie dans la cuisine le 6 janvier, four et mur brûlés.",
    "expected_type": "incendie_explosion",
    "image_paths": ["data/attachments/WaterDamage_100.jpg"],  # Wrong image type
    "complete": True,
    "image_should_not_match": True
}

EDGE_CASE_VERY_DETAILED = {
    "user_text": """Le 5 janvier 2025 vers 14h30, j'ai constaté une importante fuite d'eau provenant 
    du plafond de ma salle de bain située au premier étage. L'eau s'est infiltrée à travers le 
    plafond et a endommagé le revêtement du sol, le placo du plafond, et partiellement le meuble 
    sous-lavabo. J'ai immédiatement coupé l'arrivée d'eau et placé des seaux pour limiter les dégâts. 
    Le plombier est intervenu le jour même et a identifié une rupture du joint du flexible du robinet 
    de la douche à l'étage supérieur.""",
    "expected_type": "degats_des_eaux",
    "image_paths": ["data/attachments/WaterDamage_306.jpg"],
    "complete": True
}

EDGE_CASE_MINIMAL = {
    "user_text": "Fuite hier cuisine",
    "expected_type": "degats_des_eaux",
    "missing_fields": ["date_sinistre"],
    "image_paths": [],
    "complete": False
}


# === Non-covered scenarios ===

NOT_COVERED_EXCLUDED = {
    "user_text": "Dégâts d'eau suite à une négligence de ma part, j'ai laissé le robinet ouvert pendant 2 jours.",
    "expected_type": "degats_des_eaux",
    "image_paths": ["data/attachments/WaterDamage_90.jpg"],
    "should_be_rejected": True,
    "rejection_reason": "negligence"
}


# === Sample parsed declarations ===

def get_sample_parsed_declaration(case_type="complete_water"):
    """Get a sample parsed declaration for testing."""
    if case_type == "complete_water":
        return {
            "sinistre_type": "degats_des_eaux",
            "sinistre_confidence": 0.95,
            "sinistre_explain": "Water leak from ceiling",
            "candidates": [{"type": "degats_des_eaux", "score": 0.95}],
            "extracted": {
                "date_sinistre": "2025-01-05",
                "lieu": "salle de bain",
                "description": "Fuite d'eau au plafond avec dégâts",
                "biens_impactes": ["plafond", "sol"]
            }
        }
    elif case_type == "incomplete_water":
        return {
            "sinistre_type": "degats_des_eaux",
            "sinistre_confidence": 0.92,
            "sinistre_explain": "Water leak, missing date",
            "candidates": [{"type": "degats_des_eaux", "score": 0.92}],
            "extracted": {
                "date_sinistre": None,
                "lieu": "salle de bain",
                "description": "Fuite d'eau au plafond",
                "biens_impactes": ["plafond"]
            }
        }
    elif case_type == "complete_fire":
        return {
            "sinistre_type": "incendie_explosion",
            "sinistre_confidence": 0.98,
            "sinistre_explain": "Fire in kitchen",
            "candidates": [{"type": "incendie_explosion", "score": 0.98}],
            "extracted": {
                "date_sinistre": "2025-01-06",
                "lieu": "cuisine",
                "description": "Incendie dans la cuisine",
                "biens_impactes": ["four", "mur"]
            }
        }
    elif case_type == "complete_theft":
        return {
            "sinistre_type": "vol_vandalisme",
            "sinistre_confidence": 0.96,
            "sinistre_explain": "Break-in with theft",
            "candidates": [{"type": "vol_vandalisme", "score": 0.96}],
            "extracted": {
                "date_sinistre": "2025-01-07",
                "lieu": "chambre",
                "description": "Effraction avec vol",
                "biens_impactes": ["porte", "fenêtre"],
                "police_report_number": "12345"
            }
        }
    elif case_type == "incomplete_theft":
        return {
            "sinistre_type": "vol_vandalisme",
            "sinistre_confidence": 0.94,
            "sinistre_explain": "Break-in, missing police report",
            "candidates": [{"type": "vol_vandalisme", "score": 0.94}],
            "extracted": {
                "date_sinistre": "2025-01-07",
                "lieu": "salon",
                "description": "Effraction",
                "biens_impactes": ["fenêtre"],
                "police_report_number": None
            }
        }
    else:
        raise ValueError(f"Unknown case type: {case_type}")


# === All sample cases as a dict for easy access ===

ALL_CASES = {
    "complete_water": COMPLETE_WATER_DAMAGE,
    "complete_fire": COMPLETE_FIRE_DAMAGE,
    "complete_theft": COMPLETE_THEFT,
    "incomplete_date": INCOMPLETE_MISSING_DATE,
    "incomplete_location": INCOMPLETE_MISSING_LOCATION,
    "incomplete_police": INCOMPLETE_MISSING_POLICE_REPORT,
    "incomplete_multiple": INCOMPLETE_MULTIPLE_MISSING,
    "ambiguous_unclear": AMBIGUOUS_UNCLEAR_TYPE,
    "ambiguous_contradictory": AMBIGUOUS_CONTRADICTORY,
    "edge_no_images": EDGE_CASE_NO_IMAGES,
    "edge_wrong_image": EDGE_CASE_WRONG_IMAGE_TYPE,
    "edge_detailed": EDGE_CASE_VERY_DETAILED,
    "edge_minimal": EDGE_CASE_MINIMAL,
    "not_covered": NOT_COVERED_EXCLUDED,
}

