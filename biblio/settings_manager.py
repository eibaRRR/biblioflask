# biblio/settings_manager.py
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, 'settings.json')

def load_settings():
    """Charge la configuration complète depuis le fichier JSON."""
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # En cas d'erreur, retournez une configuration par défaut pour éviter de planter
        return {
            "max_loans_per_user": 5,
            "loan_duration_days": 14, # Added default here as well for consistency
            "categories": ["Roman", "Essai"],
            "notification_templates": {
                "loan_approved": "Votre demande pour '{livre_titre}' a été acceptée.",
                "loan_refused": "Votre demande pour '{livre_titre}' a été refusée."
            }
        }

def save_settings(settings_data):
    """Sauvegarde la configuration complète dans le fichier JSON."""
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings_data, f, indent=4, ensure_ascii=False)

def get_setting(key, default=None): # Added default=None here
    """Récupère une valeur de paramètre spécifique par sa clé.
    
    Args:
        key (str): La clé du paramètre à récupérer.
        default (any, optional): La valeur à retourner si la clé n'est pas trouvée. 
                                 Defaults to None.
    
    Returns:
        any: La valeur du paramètre ou la valeur par défaut.
    """
    settings = load_settings()
    return settings.get(key, default) # Use the default value if key is not found

def update_setting(key, value):
    """Met à jour une valeur de paramètre spécifique."""
    settings = load_settings()
    settings[key] = value
    save_settings(settings)

def get_categories():
    """Retourne la liste des catégories."""
    return get_setting('categories', []) # Provide a default empty list

def get_notification_template(template_name):
    """Récupère un modèle de message de notification."""
    templates = get_setting('notification_templates', {}) # Provide a default empty dict
    return templates.get(template_name, "")
