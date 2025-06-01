# biblio/models.py

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from biblio import settings_manager as sm

# Cette instance db sera initialisée dans app.py
db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Classe pour les utilisateurs de la bibliothèque."""
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    
    historique = db.relationship('Historique', backref='user', lazy=True)
    reservations = db.relationship('Reservation', backref='user', lazy=True)
    
    def check_password(self, password_input):
        return self.password == password_input

class Media(db.Model):
    """
    Classe de base pour tous les items de la bibliothèque (Livre, Magazine, etc.).
    Cette classe contient les informations communes à tous les médias.
    """
    __tablename__ = 'media'
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(150), unique=True, nullable=False)
    annee = db.Column(db.String(4), nullable=True)
    description = db.Column(db.Text, nullable=True)
    
    statut_etat = db.Column(db.String(50), default='disponible', nullable=False)
    emprunte_par_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    emprunteur = db.relationship('User', backref='medias_empruntes', foreign_keys=[emprunte_par_id])
    
    # Colonne technique pour gérer l'héritage (polymorphisme)
    type = db.Column(db.String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'media',
        'polymorphic_on': type
    }

class Livre(Media):
    """
    La classe Livre hérite de Media et ajoute ses propres attributs spécifiques.
    """
    __tablename__ = 'livre'
    # La clé primaire est aussi une clé étrangère pointant vers la table parente 'media'
    id = db.Column(db.Integer, db.ForeignKey('media.id'), primary_key=True)
    
    # Attributs spécifiques au livre
    auteur = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(50), nullable=True)
    note = db.Column(db.Integer, nullable=True)

    image_url = db.Column(db.String(255), nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'livre',
    }

    # Les relations qui sont spécifiques aux livres
    reservations = db.relationship('Reservation', backref='livre', lazy=True, cascade="all, delete-orphan")

    @property
    def reservation_user_ids(self):
        return [r.user_id for r in self.reservations]

    def est_disponible(self):
        return self.statut_etat == 'disponible'

    def demander_emprunt(self, user):
        if not self.est_disponible():
            raise ValueError("Ce livre n'est pas disponible.")
        
        max_loans = sm.get_setting('max_loans_per_user')
        if len(user.medias_empruntes) >= max_loans:
            raise ValueError(f"Vous avez atteint la limite de {max_loans} emprunt(s).")
            
        self.statut_etat = 'demande_emprunt_en_attente'
        self.emprunteur = user

    def approuver_emprunt(self):
        if self.statut_etat != 'demande_emprunt_en_attente':
            raise ValueError("Aucune demande d'emprunt à approuver pour ce livre.")
        self.statut_etat = 'emprunté'

    def refuser_emprunt(self):
        if self.statut_etat != 'demande_emprunt_en_attente':
            raise ValueError("Aucune demande à refuser.")
        self.statut_etat = 'disponible'
        self.emprunteur = None
        self.emprunte_par_id = None
def peut_etre_emprunte_par(self, user):
    if not self.est_disponible():
            return False, "Ce livre n'est pas disponible."
    
    max_loans = sm.get_setting('max_loans_per_user', 5)
    current_loans = len([m for m in user.medias_empruntes if m.statut_etat in ['emprunté', 'retour_en_attente']])
    
    if current_loans >= max_loans:
        return False, f"Vous avez atteint la limite de {max_loans} emprunt(s) simultané(s)."
    
    return True, "Emprunt autorisé."
    

class Historique(db.Model):
    """Table pour l'historique des emprunts."""
    __tablename__ = 'historique'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # La clé étrangère pointe vers la table de base 'media'
    # CORRECTION : Rendre la colonne nullable pour conserver l'historique si un livre est supprimé.
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=True) 
    media = db.relationship('Media')

    date_emprunt = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_retour = db.Column(db.DateTime, nullable=True)
    date_retour_prevue = db.Column(db.DateTime)

class Reservation(db.Model):
    """Table pour les réservations."""
    __tablename__ = 'reservation'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # La clé étrangère pointe vers la table de base 'media'
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=False)
    
    date_reservation = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)