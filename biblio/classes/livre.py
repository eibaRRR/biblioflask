# biblio/classes/livre.py

class Livre:
    """Classe représentant un livre dans la bibliothèque."""
    # Ajout de 'reservations=None' au constructeur
    def __init__(self, titre, auteur, annee, genre, note, description, statut, reservations=None):
        self.titre = titre
        self.auteur = auteur
        self.annee = str(annee)
        self.genre = genre
        self.note = int(note)
        self.description = description
        self.statut = statut
        # Initialise une liste vide si aucune réservation n'est fournie
        self.reservations = reservations if reservations is not None else []

    @staticmethod
    def from_dict(data):
        """Crée une instance de Livre à partir d'un dictionnaire."""
        return Livre(
            titre=data.get('titre'),
            auteur=data.get('auteur'),
            annee=data.get('annee'),
            genre=data.get('genre'),
            note=data.get('note', 0),
            description=data.get('description', ''),
            statut=data.get('statut', {"etat": "disponible", "par_id": None}),
            # Gérer les réservations lors du chargement
            reservations=data.get('reservations', [])
        )

    def to_dict(self):
        """Convertit l'objet Livre en dictionnaire pour la sérialisation JSON."""
        return self.__dict__

    def est_disponible(self):
        """Vérifie si le livre est disponible."""
        return self.statut['etat'] == 'disponible'

    def est_demande_emprunt_en_attente(self):
        """Vérifie si le livre est en attente d'approbation d'emprunt."""
        return self.statut['etat'] == 'demande_emprunt_en_attente'

    def est_emprunte(self):
        """Vérifie si le livre est emprunté."""
        return self.statut['etat'] == 'emprunté'

    def est_en_attente_de_retour(self):
        """Vérifie si le livre est en attente de retour."""
        return self.statut['etat'] == 'retour_en_attente'

    def demander_emprunt(self, user_id):
        """Marque le livre comme demandé pour emprunt par un utilisateur."""
        if self.est_disponible():
            self.statut['etat'] = 'demande_emprunt_en_attente'
            self.statut['par_id'] = user_id
            return True
        return False

    def approuver_emprunt(self):
        """Approuve la demande d'emprunt (action admin)."""
        if self.est_demande_emprunt_en_attente() and self.statut.get('par_id') is not None:
            self.statut['etat'] = 'emprunté'
            return True
        return False

    def refuser_emprunt(self):
        """Refuse la demande d'emprunt (action admin)."""
        if self.est_demande_emprunt_en_attente():
            self.statut['etat'] = 'disponible'
            self.statut['par_id'] = None
            return True
        return False

    def demander_retour(self):
        """Marque le livre comme en attente de retour (action utilisateur)."""
        if self.est_emprunte():
            self.statut['etat'] = 'retour_en_attente'
            return True
        return False

    def retourner(self):
        """
        Finalise le retour. Si pas de réservation, devient disponible.
        Sinon, est automatiquement mis en attente pour le prochain.
        Retourne l'ID du prochain utilisateur si une réservation est traitée.
        """
        if self.est_en_attente_de_retour():
            prochain_user_id = self.traiter_prochaine_reservation()
            if prochain_user_id:
                return prochain_user_id
            
            self.statut['etat'] = 'disponible'
            self.statut['par_id'] = None
            return None
        return False


    # --- NOUVELLES MÉTHODES POUR LES RÉSERVATIONS ---

    def est_reserve(self):
        """Vérifie si le livre a des réservations en attente."""
        return len(self.reservations) > 0

    def ajouter_reservation(self, user_id):
        """Ajoute un utilisateur à la file d'attente des réservations."""
        # On peut réserver un livre emprunté ou en attente de retour
        can_reserve = self.est_emprunte() or self.est_en_attente_de_retour()
        if can_reserve and user_id not in self.reservations:
            # Vérifier que l'utilisateur n'est pas celui qui a déjà le livre
            if self.statut.get('par_id') != user_id:
                self.reservations.append(user_id)
                return True
        return False

    def get_prochain_reservataire_id(self):
        """Retourne l'ID du prochain utilisateur dans la file d'attente."""
        return self.reservations[0] if self.est_reserve() else None

    def traiter_prochaine_reservation(self):
        """
        Traite la prochaine réservation en passant le livre en demande d'emprunt
        pour le premier utilisateur de la file d'attente.
        """
        if self.est_reserve():
            prochain_user_id = self.reservations.pop(0)
            self.statut['etat'] = 'demande_emprunt_en_attente'
            self.statut['par_id'] = prochain_user_id
            return prochain_user_id
        return None