# biblio/classes/bibliotheque.py
import json
import os 
from .livre import Livre

class Bibliotheque:
    """Classe gérant la collection de livres et la logique des emprunts."""
    def __init__(self, json_path):
        self.json_path = json_path
        self.livres = self._charger_livres()

    def _charger_livres(self):
        """Charge les livres depuis le JSON."""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [Livre.from_dict(livre_data) for livre_data in data]
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _sauvegarder_livres(self):
        """
        Sauvegarde la liste des livres de manière atomique pour éviter la corruption
        du fichier en cas d'erreur pendant l'écriture.
        """
        temp_path = self.json_path + ".tmp"
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                data = [livre.to_dict() for livre in self.livres]
                json.dump(data, f, indent=4, ensure_ascii=False)
            os.replace(temp_path, self.json_path)
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e

    def get_livres(self):
        """Retourne la liste de tous les objets Livre."""
        return self.livres

    def rechercher_livre(self, titre):
        """Recherche un livre par son titre (insensible à la casse)."""
        for livre in self.livres:
            if livre.titre.lower() == titre.lower():
                return livre
        return None

    def rechercher_livres(self, query: str):
        """Recherche des livres par mot-clé."""
        query = query.lower()
        return [livre for livre in self.livres if query in livre.titre.lower() or query in livre.auteur.lower() or query in str(livre.annee)]

    def nombre_de_livres_empruntes(self):
        """Compte le nombre total de livres actuellement empruntés ou en attente de retour."""
        # Ne compte plus 'demande_emprunt_en_attente' comme emprunté ici, seulement les réélement empruntés ou en retour
        return len([livre for livre in self.livres if livre.est_emprunte() or livre.est_en_attente_de_retour()])

    def get_livres_empruntes_par(self, user_id: int):
        """Retourne la liste des livres empruntés ou en attente de retour par un utilisateur."""
        return [livre for livre in self.livres if (livre.est_emprunte() or livre.est_en_attente_de_retour()) and livre.statut.get('par_id') == user_id]

    def get_livres_en_attente_de_retour(self):
        """Retourne la liste des livres en attente de retour."""
        return [livre for livre in self.livres if livre.est_en_attente_de_retour()]

    # NOUVELLE METHODE
    def get_livres_en_demande_emprunt(self):
        """Retourne la liste des livres avec une demande d'emprunt en attente."""
        return [livre for livre in self.livres if livre.est_demande_emprunt_en_attente()]

    def ajouter_livre(self, titre: str, auteur: str, annee: str, genre: str, note: int, description: str = ""):
        """Ajoute un nouveau livre à la bibliothèque."""
        if self.rechercher_livre(titre):
            return False # Ou lever une exception
        nouveau_livre_data = {
            "titre": titre, "auteur": auteur, "annee": annee, "genre": genre,
            "statut": {"etat": "disponible", "par_id": None}, "note": note,
            "description": description
        }
        self.livres.append(Livre.from_dict(nouveau_livre_data))
        self._sauvegarder_livres()
        return True

    def supprimer_livre(self, titre: str):
        """Supprime un livre de la bibliothèque."""
        livre = self.rechercher_livre(titre)
        if livre:
            # On pourrait ajouter une vérification ici : ne pas supprimer si non disponible
            self.livres.remove(livre)
            self._sauvegarder_livres()
            return True
        return False

    def modifier_livre(self, titre_original: str, nouveaux_details: dict):
        """Modifie les informations d'un livre existant."""
        livre = self.rechercher_livre(titre_original)
        if not livre: return False

        nouveau_titre = nouveaux_details.get('titre', titre_original)
        # Vérifier si le nouveau titre (s'il a changé) n'existe pas déjà pour un autre livre
        if titre_original.lower() != nouveau_titre.lower() and self.rechercher_livre(nouveau_titre):
            # Gérer le cas où le nouveau titre existe déjà (par exemple, renvoyer une erreur spécifique ou False)
            return False # Exemple: Echec si le nouveau titre est déjà pris

        livre.titre = nouveau_titre # Mettre à jour le titre si changé
        livre.auteur = nouveaux_details.get('auteur', livre.auteur)
        livre.annee = nouveaux_details.get('annee', livre.annee)
        livre.genre = nouveaux_details.get('genre', livre.genre)
        livre.note = int(nouveaux_details.get('note', livre.note))
        livre.description = nouveaux_details.get('description', livre.description)
        self._sauvegarder_livres()
        return True

    # NOUVELLE METHODE
    def creer_demande_emprunt(self, titre: str, user_id: int):
        """Gère la demande d'emprunt d'un livre par un utilisateur."""
        livre = self.rechercher_livre(titre)
        if livre and livre.demander_emprunt(user_id):
            self._sauvegarder_livres()
            return True
        return False

    # METHODE MODIFIEE (anciennement emprunter_livre)
    def approuver_la_demande_emprunt(self, titre: str):
        """Gère l'approbation d'une demande d'emprunt (action admin)."""
        livre = self.rechercher_livre(titre)
        # La logique d'enregistrement de l'historique sera dans bibliotheque_manager
        if livre and livre.approuver_emprunt():
            self._sauvegarder_livres()
            return True # Retourne True si l'approbation a réussi au niveau du livre
        return False

    # NOUVELLE METHODE
    def refuser_la_demande_emprunt(self, titre: str):
        """Gère le refus d'une demande d'emprunt (action admin)."""
        livre = self.rechercher_livre(titre)
        if livre and livre.refuser_emprunt():
            self._sauvegarder_livres()
            return True
        return False

    def demander_retour_livre(self, titre: str): # Pas de user_id ici, car l'utilisateur est dans livre.statut
        """Gère la demande de retour d'un livre."""
        livre = self.rechercher_livre(titre)
        if livre and livre.demander_retour():
            self._sauvegarder_livres()
            return True
        return False

    def retourner_livre(self, titre: str): # Approbation du retour par l'admin
        """Gère l'approbation de retour d'un livre."""
        livre = self.rechercher_livre(titre)
        # La logique d'enregistrement de l'historique sera dans bibliotheque_manager
        if livre and livre.retourner():
            self._sauvegarder_livres()
            return True
        return False