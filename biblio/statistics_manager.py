import collections
from . import historique_manager
from . import bibliotheque_manager as bm
from .user_manager import User, load_all_users
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
from . import settings_manager as sm

def get_general_stats():
    """Récupère les statistiques générales de la bibliothèque."""
    stats = {
        'total_books': len(bm.get_livres()),
        'total_users': len(load_all_users()),
        'total_loans': len(historique_manager._charger_historique()),
        'current_loans': bm.nombre_de_livres_empruntes()
    }
    return stats

def get_popular_books(limit=5):
    """Retourne les livres les plus empruntés."""
    historique = historique_manager._charger_historique()
    if not historique:
        return []
    
    # Compte le nombre d'emprunts pour chaque titre de livre
    counter = collections.Counter([emprunt['livre_titre'] for emprunt in historique])
    
    # Récupère les 'limit' plus populaires
    popular_books = counter.most_common(limit)
    return popular_books # Retourne une liste de tuples (titre, nombre_emprunts)

def get_most_active_readers(limit=5):
    """Retourne les lecteurs les plus actifs."""
    historique = historique_manager._charger_historique()
    if not historique:
        return []
        
    # Compte le nombre d'emprunts pour chaque utilisateur
    counter = collections.Counter([emprunt['username'] for emprunt in historique])
    
    # Récupère les 'limit' plus actifs
    active_readers = counter.most_common(limit)
    return active_readers # Retourne une liste de tuples (username, nombre_emprunts)
def generate_report_excel(report_type='popular_books'):
    """Génère un rapport Excel sous forme de bytes."""
    if report_type == 'popular_books':
        data = get_popular_books(limit=None) # Obtenir toutes les données
        df = pd.DataFrame(data, columns=['Livre', 'Nombre d\'emprunts'])
    elif report_type == 'active_readers':
        data = get_most_active_readers(limit=None)
        df = pd.DataFrame(data, columns=['Lecteur', 'Nombre d\'emprunts'])
    else:
        return None

    # Créer un fichier Excel en mémoire
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Rapport')
    
    output.seek(0)
    return output
def get_overdue_books():
    """Retourne la liste des livres qui n'ont pas été retournés à temps."""
    historique = historique_manager._charger_historique()
    livres_en_retard = []
    now = datetime.utcnow()

    for emprunt in historique:
        # Si le livre n'est pas retourné et que la date de retour prévue est passée
        if emprunt.get('date_retour') is None:
            date_prevue_str = emprunt.get('date_retour_prevue')
            if date_prevue_str:
                date_prevue = datetime.fromisoformat(date_prevue_str.replace('Z', ''))
                if now > date_prevue:
                    jours_retard = (now - date_prevue).days
                    emprunt['jours_retard'] = jours_retard
                    livres_en_retard.append(emprunt)
    
    return sorted(livres_en_retard, key=lambda x: x['jours_retard'], reverse=True)