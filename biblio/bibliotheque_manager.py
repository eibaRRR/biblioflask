# biblio/bibliotheque_manager.py
import os
from .classes.bibliotheque import Bibliotheque
from . import historique_manager
from .user_manager import User # <-- Assurez-vous que User est importé

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(BASE_DIR, 'bibliotheque.json')

_manager = Bibliotheque(JSON_FILE)

# --- Fonctions publiques qui délèguent à l'instance du gestionnaire ---
# (Vos fonctions existantes : get_livres, rechercher_livre, etc.)
def get_livres(): return _manager.get_livres()
def rechercher_livre(titre: str): return _manager.rechercher_livre(titre)
def rechercher_livres(query: str): return _manager.rechercher_livres(query)
def nombre_de_livres_empruntes(): return _manager.nombre_de_livres_empruntes()
def get_livres_empruntes_par(user_id: int): return _manager.get_livres_empruntes_par(user_id)
def get_livres_en_attente_de_retour(): return _manager.get_livres_en_attente_de_retour()
def get_livres_en_demande_emprunt(): return _manager.get_livres_en_demande_emprunt()
def ajouter_livre(titre: str, auteur: str, annee: str, genre: str, note: int, description: str = ""): 
    return _manager.ajouter_livre(titre, auteur, annee, genre, note, description)
def supprimer_livre(titre: str): return _manager.supprimer_livre(titre)
def modifier_livre(titre_original: str, nouveaux_details: dict): 
    return _manager.modifier_livre(titre_original, nouveaux_details)
def demander_emprunt_livre_par_utilisateur(titre: str, current_user_id: int):
    return _manager.creer_demande_emprunt(titre, current_user_id)
def approuver_emprunt(titre: str):
    livre = _manager.rechercher_livre(titre)
    if not livre or not livre.est_demande_emprunt_en_attente():
        return False
    user_id_emprunteur = livre.statut.get('par_id')
    if user_id_emprunteur is None:
        return False
    if _manager.approuver_la_demande_emprunt(titre):
        user_emprunteur = User.get(user_id_emprunteur)
        if user_emprunteur:
            historique_manager.enregistrer_emprunt(user_emprunteur, titre)
            return True
        return False
    return False
def refuser_emprunt(titre: str):
    return _manager.refuser_la_demande_emprunt(titre)
def demander_retour_livre(titre: str):
    return _manager.demander_retour_livre(titre)
def retourner_livre(titre: str): 
    if _manager.retourner_livre(titre):
        historique_manager.enregistrer_retour(titre)
        return True
    return False

# VÉRIFIEZ OU AJOUTEZ CETTE FONCTION CI-DESSOUS :
def get_details_livres_empruntes():
    """
    Retourne une liste de dictionnaires, chaque dictionnaire représentant un livre 
    actuellement emprunté avec le titre, l'auteur, le nom de l'emprunteur et la date d'emprunt.
    """
    livres_empruntes_details = []
    # Utilise la fonction get_livres() définie dans ce même module (bibliotheque_manager.py)
    # qui elle-même appelle _manager.get_livres()
    tous_les_livres = get_livres() 

    for livre_obj in tous_les_livres: # Renommé la variable de boucle pour éviter confusion avec le module 'livre'
        if livre_obj.statut.get('etat') == 'emprunté' and livre_obj.statut.get('par_id'):
            user_id_emprunteur = livre_obj.statut['par_id']
            emprunteur = User.get(user_id_emprunteur)
            nom_emprunteur = emprunteur.username if emprunteur else "Utilisateur inconnu"
            
            # Récupérer la date d'emprunt depuis l'historique
            # Assurez-vous que historique_manager est bien importé en haut du fichier
            date_emprunt = historique_manager.get_date_emprunt_actuel(livre_obj.titre, user_id_emprunteur)
            
            livres_empruntes_details.append({
                'titre': livre_obj.titre,
                'auteur': livre_obj.auteur,
                'emprunteur_nom': nom_emprunteur,
                'date_emprunt': date_emprunt
            })
    # Trier par date d'emprunt (plus récent d'abord), si les dates sont disponibles
    # Gérer le cas où date_emprunt peut être None pour le tri
    livres_empruntes_details.sort(key=lambda x: x['date_emprunt'] if x['date_emprunt'] else '', reverse=True)
    return livres_empruntes_details
def reserver_livre(titre: str, user_id: int):
    """Permet à un utilisateur de réserver un livre déjà emprunté."""
    livre = _manager.rechercher_livre(titre)
    if livre and livre.ajouter_reservation(user_id):
        _manager._sauvegarder_livres()
        return True
    return False
def get_livres_reserves_par(user_id: int):
    """Retourne la liste des livres réservés par un utilisateur."""
    livres_reserves = []
    tous_les_livres = get_livres()
    for livre in tous_les_livres:
        if user_id in livre.reservations:
            livres_reserves.append(livre)
    return livres_reserves