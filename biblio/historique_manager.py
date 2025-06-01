import json
import os
from datetime import datetime, timedelta
from . import settings_manager as sm

# Chemin vers le fichier d'historique
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, 'historique_emprunts.json')

def _charger_historique():
    """Charge l'historique depuis le fichier JSON."""
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Si le fichier n'existe pas ou est vide, on en crée un
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
        return []

def _sauvegarder_historique(historique):
    """Sauvegarde la liste d'historique dans le fichier JSON."""
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(historique, f, indent=4, ensure_ascii=False)

def enregistrer_emprunt(user, livre_titre):
    """Ajoute une nouvelle entrée d'emprunt à l'historique."""
    historique = _charger_historique()
    nouvelle_entree = {
        "user_id": user.id,
        "username": user.username,
        "livre_titre": livre_titre,
        "date_emprunt": datetime.utcnow().isoformat() + 'Z',  # Format ISO 8601 UTC
        "date_retour": None
    }
    historique.append(nouvelle_entree)
    _sauvegarder_historique(historique)

def enregistrer_retour(livre_titre):
    """Met à jour une entrée d'historique en ajoutant la date de retour."""
    historique = _charger_historique()
    # On parcourt la liste à l'envers pour trouver le dernier emprunt non retourné de ce livre
    for entree in reversed(historique):
        if entree['livre_titre'] == livre_titre and entree['date_retour'] is None:
            entree['date_retour'] = datetime.utcnow().isoformat() + 'Z'
            _sauvegarder_historique(historique)
            return

def get_historique_utilisateur(user_id):
    """Récupère l'historique d'emprunts pour un utilisateur spécifique."""
    historique = _charger_historique()
    # Filtre les entrées pour l'utilisateur et les trie par date d'emprunt (plus récent d'abord)
    user_history = [entree for entree in historique if entree['user_id'] == user_id]
    user_history.sort(key=lambda x: x['date_emprunt'], reverse=True)
    return user_history
def get_date_emprunt_actuel(livre_titre, user_id):
    """
    Récupère la date d'emprunt pour un livre actuellement emprunté par un utilisateur spécifique.
    Cherche la dernière entrée d'historique pour ce livre et cet utilisateur où le retour n'est pas encore enregistré.
    """
    historique = _charger_historique()
    for entree in reversed(historique): # Parcourir du plus récent au plus ancien
        if entree.get('livre_titre') == livre_titre and \
           entree.get('user_id') == user_id and \
           entree.get('date_retour') is None:
            return entree.get('date_emprunt')
    return None
def enregistrer_emprunt(user, livre_titre):
    """Ajoute une nouvelle entrée d'emprunt à l'historique."""
    historique = _charger_historique()
    date_emprunt = datetime.utcnow()
    
    # Récupérer la durée de prêt depuis les paramètres
    loan_duration = sm.get_setting('loan_duration_days') or 14 # 14 jours par défaut
    date_retour_prevue = date_emprunt + timedelta(days=loan_duration)

    nouvelle_entree = {
        "user_id": user.id,
        "username": user.username,
        "livre_titre": livre_titre,
        "date_emprunt": date_emprunt.isoformat() + 'Z',
        "date_retour_prevue": date_retour_prevue.isoformat() + 'Z', # <-- NOUVEAU
        "date_retour": None
    }
    historique.append(nouvelle_entree)
    _sauvegarder_historique(historique)