# biblio/app.py
# app.py - Version entièrement mise à jour pour SQLAlchemy

import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from functools import wraps
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from biblio.models import db, User, Livre, Historique, Reservation # Media is not directly used but Livre inherits from it
from biblio.forms import LivreForm
from biblio import settings_manager as sm
from biblio import notification_manager # Gardé pour le système de notification basé sur JSON
import pandas as pd
from io import BytesIO 
from sqlalchemy import or_
from collections import Counter



app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

# --- CONFIGURATION DE LA BASE DE DONNÉES SQLALCHEMY ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///biblio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# --- FILTRE JINJA MIS À JOUR ---
@app.template_filter('format_datetime')
def format_datetime_filter(value, format="%d %B %Y à %Hh%M"):
    if not value:
        return "Date non disponible"
    if isinstance(value, str):
        try:
            # Attempt to parse ISO format, handling potential 'Z' for UTC
            if value.endswith('Z'):
                value = value[:-1] # Remove Z
            value_dt = datetime.fromisoformat(value)
        except ValueError:
             # Fallback for other string formats or if parsing fails
            try:
                value_dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f")
            except ValueError:
                try:
                    value_dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    return value # Return original string if all parsing fails
    elif isinstance(value, datetime):
        value_dt = value
    else:
        return value # Return original value if not a string or datetime

    return value_dt.strftime(format)

# --- CONFIGURATION DE FLASK-LOGIN ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- GESTION DES NOTIFICATIONS (conservé tel quel) ---
@app.before_request
def inject_notifications():
    if current_user.is_authenticated:
        notifications = notification_manager.get_and_clear_notifications(current_user.id)
        for notif in notifications:
            flash(notif['message'], notif['category'])

# --- DÉCORATEUR ADMIN (inchangé) ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash("Accès non autorisé. Cette section est réservée aux administrateurs.", "danger")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# ==============================================================================
# --- ROUTES D'AUTHENTIFICATION (mises à jour pour SQLAlchemy) ---
# ==============================================================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash("Ce nom d'utilisateur existe déjà.", "danger")
        else:
            # In a real application, you would hash the password here.
            # For this project, we are keeping it simple as per previous structure.
            new_user = User(username=username, password=password) 
            db.session.add(new_user)
            db.session.commit()
            flash("Inscription réussie ! Vous pouvez maintenant vous connecter.", "success")
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        # Password checking should ideally use a secure method like hashing.
        # Here, it's a direct comparison as per the User model's check_password.
        if user and user.check_password(password):
            login_user(user)
            flash(f"Bienvenue, {user.username} !", "success")
            return redirect(url_for('index'))
        else:
            flash("Nom d'utilisateur ou mot de passe incorrect.", "danger")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Vous avez été déconnecté.", "success")
    return redirect(url_for('index'))

# ==============================================================================
# --- ROUTES PRINCIPALES DE L'APPLICATION (mises à jour pour SQLAlchemy) ---
# ==============================================================================

@app.route('/')
def index():
    query = request.args.get('recherche', '').strip()
    sort_by = request.args.get('tri', 'note_desc')
    
    # Nouveaux filtres
    show_available_only = request.args.get('disponibilite', 'false') == 'true'
    selected_genres = request.args.getlist('genre_filter') # Récupère une liste de genres

    livres_query = Livre.query

    # 1. Appliquer le filtre de recherche textuelle en premier
    if query:
        search_term = f"%{query.lower()}%"
        livres_query = livres_query.filter(
            db.or_(
                Livre.titre.ilike(search_term),
                Livre.auteur.ilike(search_term),
                Livre.annee.ilike(search_term)
            )
        )

    # 2. Appliquer le filtre de disponibilité
    if show_available_only:
        livres_query = livres_query.filter(Livre.statut_etat == 'disponible')

    # 3. Appliquer le filtre de genre(s)
    if selected_genres:
        livres_query = livres_query.filter(Livre.genre.in_(selected_genres))

    # 4. Appliquer le tri
    if sort_by == 'titre_asc':
        livres_query = livres_query.order_by(Livre.titre.asc())
    elif sort_by == 'auteur_asc':
        livres_query = livres_query.order_by(Livre.auteur.asc())
    elif sort_by == 'annee_desc':
        livres_query = livres_query.order_by(Livre.annee.desc())
    elif sort_by == 'annee_asc':
        livres_query = livres_query.order_by(Livre.annee.asc())
    else:  # 'note_desc' or default
        livres_query = livres_query.order_by(Livre.note.desc(), Livre.titre.asc())


    # Pagination (si vous l'implémentez ou l'utilisez)
    page = request.args.get('page', 1, type=int)
    per_page = 12 # Nombre de livres par page (ajustez selon vos besoins)
    pagination_obj = livres_query.paginate(page=page, per_page=per_page, error_out=False)
    tous_les_livres_pagines = pagination_obj.items
    
    # Pour l'affichage par genre (si vous ne faites pas de recherche ou de filtrage complexe qui casse cette logique)
    # Si une recherche ou un filtre de genre est actif, il est plus simple d'afficher une liste plate.
    livres_par_genre = defaultdict(list)
    if not query and not selected_genres: # Afficher par genre seulement si pas de recherche ou filtre de genre
        for livre in tous_les_livres_pagines: # Utiliser les livres paginés
            livres_par_genre[livre.genre if livre.genre else "Non classé"].append(livre)
    else: # Afficher une liste plate pour les résultats de recherche/filtre
        livres_par_genre["Résultats"] = tous_les_livres_pagines


    total_livres_count = Livre.query.count()
    livres_empruntes_count = Livre.query.filter(Livre.statut_etat.in_(['emprunté', 'retour_en_attente'])).count()

    if query and not tous_les_livres_pagines: # Vérifier sur les livres paginés
        flash(f"Aucun livre ne correspond à votre recherche : '{query}'.", "info")

    # Pour remplir les options de filtre de genre
    all_available_genres = sorted(list(set(g[0] for g in Livre.query.with_entities(Livre.genre).distinct() if g[0])))


    return render_template('index.html',
                           livres_par_genre=dict(livres_par_genre),
                           query=query,
                           livres_empruntes_count=livres_empruntes_count,
                           total_livres=total_livres_count,
                           tri=sort_by,
                           pagination=pagination_obj, # Passer l'objet de pagination
                           show_available_only=show_available_only, # Passer l'état du filtre
                           all_available_genres=all_available_genres, # Passer tous les genres pour le filtre
                           selected_genres=selected_genres) # Passer les genres sélectionnés
# ROUTE POUR LA RECHERCHE EN TEMPS RÉEL
@app.route('/search_realtime')
def search_realtime():
    query = request.args.get('q', '').strip() # Add strip to remove leading/trailing spaces
    if not query or len(query) < 2: # Also check query length here
        return jsonify([])
    
    search_term = f"%{query.lower()}%"
    livres = Livre.query.filter(
        db.or_(
            Livre.titre.ilike(search_term), 
            Livre.auteur.ilike(search_term),
            Livre.annee.ilike(search_term)
            )
    ).limit(10).all() # Limit results for performance

    results = [
        {
            'titre': livre.titre,
            'auteur': livre.auteur,
            'note': livre.note,
            'image_url': livre.image_url or url_for('static', filename='images/default_cover_creative.png'), # Fallback image
            'details_url': url_for('details_livre', titre=livre.titre)
        } for livre in livres
    ]
    return jsonify(results)


@app.route('/livre/<path:titre>') # Use path converter for titles with slashes
def details_livre(titre):
    livre = Livre.query.filter_by(titre=titre).first_or_404()

    recommandations = []
    if livre:
        recommandations = Livre.query.filter(
            Livre.id != livre.id,
            or_(Livre.genre == livre.genre, Livre.auteur == livre.auteur)
        ).order_by(db.func.random()).limit(4).all() 

    return render_template(
        'details_livre.html', 
        livre=livre, 
        recommandations=recommandations
        )

@app.route('/profil')
@login_required
def profil():
    # Livres que l'utilisateur a actuellement empruntés (état 'emprunté' ou 'retour_en_attente')
    livres_empruntes_obj = Livre.query.filter(
        Livre.emprunte_par_id == current_user.id,
        Livre.statut_etat.in_(['emprunté', 'retour_en_attente'])
    ).all()

    livres_empruntes_actuellement_details = []
    for livre_emprunte in livres_empruntes_obj:
        # Trouver l'entrée d'historique active pour cet emprunt spécifique
        historique_actif = Historique.query.filter_by(
            media_id=livre_emprunte.id,
            user_id=current_user.id,
            date_retour=None # Important: seulement les emprunts actifs
        ).order_by(Historique.date_emprunt.desc()).first()

        date_emprunt = historique_actif.date_emprunt if historique_actif else None
        date_retour_prevue = historique_actif.date_retour_prevue if historique_actif else None
        est_en_retard = date_retour_prevue and date_retour_prevue < datetime.utcnow() if date_retour_prevue else False
        
        # S'assurer que l'objet livre est bien un Livre pour accéder à image_url
        # Normalement, c'est déjà le cas si la relation est bien configurée.
        image_url_livre = livre_emprunte.image_url if hasattr(livre_emprunte, 'image_url') else None


        livres_empruntes_actuellement_details.append({
            'livre': livre_emprunte, 
            'date_emprunt': date_emprunt,
            'date_retour_prevue': date_retour_prevue,
            'est_en_retard': est_en_retard,
            'image_url': image_url_livre # Ajout pour le template
        })
    
    # Historique complet des emprunts de l'utilisateur
    historique_emprunts_complet = Historique.query.filter_by(user_id=current_user.id).order_by(Historique.date_emprunt.desc()).all()
    
    # Réservations de l'utilisateur
    reservations_utilisateur = Reservation.query.filter_by(user_id=current_user.id).order_by(Reservation.date_reservation.asc()).all()
    # livres_reserves contient maintenant des objets Reservation, qui ont une relation .livre et .media
    
    return render_template('profil.html',
                           livres_empruntes_details=livres_empruntes_actuellement_details,
                           historique_emprunts=historique_emprunts_complet, 
                           reservations_utilisateur=reservations_utilisateur, # Passer les objets Reservation
                           now=datetime.utcnow()) # Pour les comparaisons de dates dans le template si besoin
@app.route('/annuler-reservation/<int:reservation_id>', methods=['POST'])
@login_required
def annuler_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    if reservation.user_id != current_user.id:
        flash("Vous n'êtes pas autorisé à annuler cette réservation.", "danger")
        return redirect(url_for('profil'))

    # S'assurer que la relation 'livre' (ou 'media') existe sur l'objet reservation
    # et que cet objet lié a un attribut 'titre'.
    livre_titre = "Titre inconnu" # Valeur par défaut
    if reservation.livre: # 'livre' est la backref de Livre.reservations
        livre_titre = reservation.livre.titre
    elif reservation.media: # Si la relation est nommée 'media'
        livre_titre = reservation.media.titre


    db.session.delete(reservation)
    db.session.commit()
    flash(f"Votre réservation pour le livre '{livre_titre}' a été annulée.", "success")
    return redirect(url_for('profil'))

# ==============================================================================
# --- ROUTES DE GESTION DES LIVRES (mises à jour pour SQLAlchemy) ---
# ==============================================================================

@app.route('/ajouter', methods=['GET', 'POST'])
@admin_required
def ajouter():
    form = LivreForm()
    # Populate genre choices from settings
    form.genre.choices = [(cat, cat) for cat in sm.get_categories()]

    if form.validate_on_submit():
        # Check if a book with the same title already exists
        if Livre.query.filter(db.func.lower(Livre.titre) == db.func.lower(form.titre.data)).first():
            form.titre.errors.append(f"Le livre '{form.titre.data}' existe déjà (casse ignorée).")
        else:
            new_livre = Livre(
                titre=form.titre.data.strip(), # Strip whitespace
                auteur=form.auteur.data.strip(),
                annee=str(form.annee.data), # Ensure it's a string if your model expects that
                genre=form.genre.data,
                note=form.note.data,
                description=form.description.data,
                image_url=form.image_url.data if form.image_url.data else None # Handle empty URL
            )
            db.session.add(new_livre)
            db.session.commit()
            flash(f"Le livre '{new_livre.titre}' a été ajouté.", "success")
            return redirect(url_for('index'))
    elif request.method == 'POST': # If form validation fails
        flash("Erreur dans le formulaire. Veuillez vérifier les champs.", "danger")

    return render_template('ajouter.html', form=form)

@app.route('/modifier/<path:titre>', methods=['GET', 'POST']) # Use path converter
@admin_required
def modifier(titre):
    livre = Livre.query.filter_by(titre=titre).first_or_404()
    form = LivreForm(obj=livre) # Pre-populate form with book data
    form.genre.choices = [(cat, cat) for cat in sm.get_categories()]

    if form.validate_on_submit():
        nouveau_titre = form.titre.data.strip()
        # Check if the new title (if changed) conflicts with another book
        existing_book_with_new_title = Livre.query.filter(db.func.lower(Livre.titre) == db.func.lower(nouveau_titre)).first()
        if nouveau_titre.lower() != livre.titre.lower() and existing_book_with_new_title:
             flash("Ce titre de livre est déjà utilisé par un autre livre (casse ignorée).", "danger")
        else:
            livre.titre = nouveau_titre
            livre.auteur = form.auteur.data.strip()
            livre.annee = str(form.annee.data)
            livre.genre = form.genre.data
            livre.note = form.note.data
            livre.description = form.description.data
            livre.image_url = form.image_url.data if form.image_url.data else None
            db.session.commit()
            flash(f"Livre '{livre.titre}' mis à jour.", "success")
            return redirect(url_for('details_livre', titre=livre.titre))
    elif request.method == 'POST':
        flash("Erreur dans le formulaire. Veuillez vérifier les champs.", "danger")
    
    return render_template('modifier.html', form=form, livre=livre)

@app.route('/supprimer/<path:titre>') # Use path converter
@admin_required
def supprimer(titre):
    livre = Livre.query.filter_by(titre=titre).first()
    if livre:
        # Check if the book is currently involved in any active loan or reservation
        if livre.statut_etat != 'disponible' or Reservation.query.filter_by(media_id=livre.id).first():
            flash("Impossible de supprimer un livre qui est en cours d'emprunt, de retour, ou qui a des réservations.", "danger")
        else:
            # Delete related history entries or handle them as needed (e.g., anonymize)
            # For now, we'll just delete the book. Consider cascading deletes or manual cleanup.
            Historique.query.filter_by(media_id=livre.id).delete() # Example: delete history
            db.session.delete(livre)
            db.session.commit()
            flash(f"Le livre '{titre}' et son historique associé ont été supprimés.", "success")
    else:
        flash("Livre non trouvé.", "danger")
    return redirect(url_for('index'))

# =================================================================================
# --- ROUTES DE GESTION DES EMPRUNTS/RETOURS (mises à jour pour SQLAlchemy) ---
# =================================================================================

@app.route('/demander-emprunt/<path:titre>') # Use path converter
@login_required
def demander_emprunt(titre):
    livre = Livre.query.filter_by(titre=titre).first_or_404()
    
    try:
        # The `demander_emprunt` method in the Livre model should handle checks
        livre.demander_emprunt(current_user) # Pass the User object
        db.session.commit()
        flash(f"Votre demande d'emprunt pour '{titre}' a été enregistrée.", "success")
    except ValueError as e: # Catch specific errors from the model
        flash(str(e), "warning")
        
    return redirect(request.referrer or url_for('index'))

@app.route('/approuver-emprunt/<path:titre>') # Use path converter
@admin_required
def approuver_emprunt_route(titre):
    livre = Livre.query.filter_by(titre=titre, statut_etat='demande_emprunt_en_attente').first_or_404()
    
    demandeur_id = livre.emprunte_par_id
    if not demandeur_id: # Should not happen if statut_etat is 'demande_emprunt_en_attente'
        flash("Erreur: Demandeur non trouvé pour cette demande.", "danger")
        return redirect(request.referrer or url_for('admin_dashboard'))

    demandeur = User.query.get(demandeur_id)
    if not demandeur:
        flash(f"Erreur: Utilisateur avec ID {demandeur_id} non trouvé.", "danger")
        return redirect(request.referrer or url_for('admin_dashboard'))

    # Call the model's method to approve
    try:
        livre.approuver_emprunt() # This should set statut_etat to 'emprunté'
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(request.referrer or url_for('admin_dashboard'))

    # Get loan duration from settings, with a fallback
    loan_duration_days = sm.get_setting('loan_duration_days', 14) # Corrected call
    
    date_retour_prevue = datetime.utcnow() + timedelta(days=loan_duration_days)
    
    nouvel_historique = Historique(
        user_id=demandeur_id,
        media_id=livre.id,
        date_emprunt=datetime.utcnow(),
        date_retour_prevue=date_retour_prevue
    )
    db.session.add(nouvel_historique)
    db.session.commit()
    
    flash(f"L'emprunt de '{titre}' par {demandeur.username} a été approuvé.", "success")
    template = sm.get_notification_template('loan_approved')
    message = template.format(livre_titre=titre)
    notification_manager.add_notification(demandeur_id, message, 'success')

    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/refuser-emprunt/<path:titre>') # Use path converter
@admin_required
def refuser_emprunt_route(titre):
    livre = Livre.query.filter_by(titre=titre, statut_etat='demande_emprunt_en_attente').first_or_404()
    demandeur_id = livre.emprunte_par_id
    
    try:
        livre.refuser_emprunt() # Model method handles state change
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(request.referrer or url_for('admin_dashboard'))

    db.session.commit()
    
    flash(f"La demande d'emprunt pour '{titre}' a été refusée.", "info")
    if demandeur_id: # Send notification only if a demander was associated
        template = sm.get_notification_template('loan_refused')
        message = template.format(livre_titre=titre)
        notification_manager.add_notification(demandeur_id, message, 'warning')
    
    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/demander-retour/<path:titre>') # Use path converter
@login_required
def demander_retour(titre):
    livre = Livre.query.filter_by(
        titre=titre, 
        emprunte_par_id=current_user.id, 
        statut_etat='emprunté'
    ).first_or_404("Livre non trouvé ou non emprunté par vous.")
    
    livre.statut_etat = 'retour_en_attente' # User requests return
    db.session.commit()
    flash(f"Votre demande de retour pour '{titre}' a été envoyée.", "success")
    return redirect(request.referrer or url_for('profil'))

@app.route('/approuver-retour/<path:titre>') # Use path converter
@admin_required
def approuver_retour(titre):
    livre = Livre.query.filter_by(titre=titre, statut_etat='retour_en_attente').first_or_404(
        "Livre non trouvé ou pas en attente de retour."
    )
    
    # Find the active loan in history to mark it as returned
    historique_entry = Historique.query.filter_by(
        media_id=livre.id, 
        user_id=livre.emprunte_par_id, # The user who had it
        date_retour=None # Ensure it's an active loan
    ).order_by(Historique.date_emprunt.desc()).first() # Get the latest one if multiple (should not happen for active)

    if historique_entry:
        historique_entry.date_retour = datetime.utcnow()
    else:
        flash(f"Avertissement: Entrée d'historique active non trouvée pour '{titre}'. Le retour est quand même traité.", "warning")

    # Check for next reservation
    prochaine_reservation = Reservation.query.filter_by(media_id=livre.id).order_by(Reservation.date_reservation.asc()).first()
    
    if prochaine_reservation:
        next_user = User.query.get(prochaine_reservation.user_id)
        if next_user:
            livre.statut_etat = 'demande_emprunt_en_attente' # Set for next user
            livre.emprunte_par_id = prochaine_reservation.user_id
            db.session.delete(prochaine_reservation) # Remove the fulfilled reservation
            flash(f"Livre '{titre}' retourné et automatiquement mis en attente d'emprunt pour {next_user.username}.", "success")
            # Optionally, notify the next user
            # notification_manager.add_notification(next_user.id, f"Le livre '{titre}' que vous aviez réservé est maintenant en attente de votre demande d'emprunt.", "info")
        else: # Should not happen if reservation is valid
            livre.statut_etat = 'disponible'
            livre.emprunte_par_id = None
            flash(f"Livre '{titre}' retourné. Prochain réservataire non trouvé, livre disponible.", "warning")
            db.session.delete(prochaine_reservation) # Clean up invalid reservation
    else:
        livre.statut_etat = 'disponible'
        livre.emprunte_par_id = None
        flash(f"Le retour du livre '{titre}' a été approuvé. Il est maintenant disponible.", "success")
        
    db.session.commit()
    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/reserver/<path:titre>') # Use path converter
@login_required
def reserver(titre):
    livre = Livre.query.filter_by(titre=titre).first_or_404()

    # Conditions for reservation
    if livre.statut_etat not in ['emprunté', 'retour_en_attente']:
        flash("Vous ne pouvez réserver qu'un livre déjà emprunté ou en attente de retour.", "warning")
        return redirect(request.referrer or url_for('details_livre', titre=titre))
    
    if livre.emprunte_par_id == current_user.id:
        flash("Vous ne pouvez pas réserver un livre que vous avez déjà emprunté.", "warning")
        return redirect(request.referrer or url_for('details_livre', titre=titre))

    if Reservation.query.filter_by(media_id=livre.id, user_id=current_user.id).first():
        flash("Vous avez déjà réservé ce livre.", "info")
        return redirect(request.referrer or url_for('details_livre', titre=titre))
    
    # Check if user is already in the reservation queue (should be covered by above, but good for robustness)
    if current_user.id in [res.user_id for res in livre.reservations]:
        flash("Vous êtes déjà dans la file d'attente pour ce livre.", "info")
        return redirect(request.referrer or url_for('details_livre', titre=titre))


    new_reservation = Reservation(user_id=current_user.id, media_id=livre.id)
    db.session.add(new_reservation)
    db.session.commit()
    flash(f"Votre réservation pour '{titre}' a été enregistrée. Vous êtes en position {len(livre.reservations)}.", "success")
    return redirect(request.referrer or url_for('details_livre', titre=titre))

# ==============================================================================
# --- ROUTES ADMIN (mises à jour pour SQLAlchemy) ---
# ==============================================================================

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    demandes_emprunt = Livre.query.filter_by(statut_etat='demande_emprunt_en_attente').all()
    demandes_retour = Livre.query.filter_by(statut_etat='retour_en_attente').all()
    
    # Livres actuellement empruntés (état 'emprunté' uniquement)
    livres_actuellement_empruntes = Historique.query.join(Livre, Livre.id == Historique.media_id).filter(
        Livre.statut_etat == 'emprunté', # Only 'emprunté'
        Historique.date_retour == None # Active loan
    ).order_by(Historique.date_emprunt.asc()).all() # Oldest loans first
    
    # Livres en retard (date de retour prévue dépassée et non retourné)
    livres_en_retard = Historique.query.filter(
        Historique.date_retour == None, 
        Historique.date_retour_prevue < datetime.utcnow() # Check against current time
    ).order_by(Historique.date_retour_prevue.asc()).all() # Most overdue first

    return render_template('admin_dashboard.html', 
                           livres_en_demande_emprunt=demandes_emprunt, 
                           livres_en_attente_retour=demandes_retour,
                           livres_actuellement_empruntes=livres_actuellement_empruntes,
                           livres_en_retard=livres_en_retard,
                           now=datetime.utcnow()) # Pass current time for calculations in template if needed

# --- Les routes pour 'settings' sont conservées car elles utilisent settings_manager (JSON) ---
@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'save_main_settings':
            try:
                max_loans = int(request.form.get('max_loans_per_user', 5))
                loan_duration = int(request.form.get('loan_duration_days', 14))
                
                sm.update_setting('max_loans_per_user', max_loans)
                sm.update_setting('loan_duration_days', loan_duration)
                
                templates = sm.get_setting('notification_templates', {}) # Ensure templates is a dict
                templates['loan_approved'] = request.form.get('loan_approved', templates.get('loan_approved', ''))
                templates['loan_refused'] = request.form.get('loan_refused', templates.get('loan_refused', ''))
                sm.update_setting('notification_templates', templates)
                
                flash("Paramètres principaux enregistrés.", "success")
            except ValueError:
                flash("Veuillez entrer des nombres valides pour les paramètres.", "danger")
        # Removed category actions from here as they have their own routes
    current_settings = sm.load_settings()
    return render_template('settings.html', settings=current_settings)

@app.route('/admin/category/add', methods=['POST'])
@admin_required
def add_category():
    category_name = request.form.get('category_name', '').strip()
    if category_name:
        categories = sm.get_categories() # Returns a list
        if category_name not in categories:
            categories.append(category_name)
            sm.update_setting('categories', sorted(list(set(categories)))) # Ensure unique and sorted
            flash(f"La catégorie '{category_name}' a été ajoutée.", "success")
        else:
            flash(f"La catégorie '{category_name}' existe déjà.", "info")
    else:
        flash("Le nom de la catégorie ne peut pas être vide.", "warning")
    return redirect(url_for('settings'))

@app.route('/admin/category/delete/<category_name>')
@admin_required
def delete_category(category_name):
    categories = sm.get_categories()
    if category_name in categories:
        # Check if any book uses this category before deleting
        if Livre.query.filter_by(genre=category_name).first():
            flash(f"Impossible de supprimer la catégorie '{category_name}', elle est utilisée par des livres.", "danger")
        else:
            categories.remove(category_name)
            sm.update_setting('categories', categories)
            flash(f"La catégorie '{category_name}' a été supprimée.", "success")
    else:
        flash(f"Catégorie '{category_name}' non trouvée.", "warning")
    return redirect(url_for('settings'))

@app.route('/admin/statistics')
@admin_required
def statistics():
    stats_data = {
        'total_books': Livre.query.count(),
        'total_users': User.query.count(),
        'total_loans': Historique.query.count(), 
        'current_loans': Livre.query.filter(Livre.statut_etat.in_(['emprunté', 'retour_en_attente'])).count()
    }
    
    # Nombre de livres en retard
    overdue_books_count = Historique.query.filter(
        Historique.date_retour == None, 
        Historique.date_retour_prevue < datetime.utcnow()
    ).count()
    stats_data['overdue_books'] = overdue_books_count # Ajout aux stats générales

    # Données pour le graphique des livres populaires
    popular_books_query = db.session.query(
            Livre.titre, 
            db.func.count(Historique.id).label('loan_count')
        ).join(Historique, Livre.id == Historique.media_id) \
        .group_by(Livre.titre) \
        .order_by(db.desc('loan_count')) \
        .limit(7).all() # On peut prendre un peu plus pour le graphique

    popular_books_chart_labels = [item[0] for item in popular_books_query]
    popular_books_chart_data = [item[1] for item in popular_books_query]

    # Données pour le graphique des lecteurs actifs
    active_readers_query = db.session.query(
            User.username,
            db.func.count(Historique.id).label('loan_count')
        ).join(Historique, User.id == Historique.user_id) \
        .group_by(User.username) \
        .order_by(db.desc('loan_count')) \
        .limit(7).all()

    active_readers_chart_labels = [item[0] for item in active_readers_query]
    active_readers_chart_data = [item[1] for item in active_readers_query]
    
    # Pour les listes affichées en plus des graphiques (Top 5)
    top_5_popular_books = popular_books_query[:5]
    top_5_active_readers = active_readers_query[:5]


    return render_template(
        'statistics.html', 
        stats=stats_data, 
        popular_books_chart_labels=popular_books_chart_labels,
        popular_books_chart_data=popular_books_chart_data,
        active_readers_chart_labels=active_readers_chart_labels,
        active_readers_chart_data=active_readers_chart_data,
        top_5_popular_books=top_5_popular_books, # Pour l'export ou affichage liste si besoin
        top_5_active_readers=top_5_active_readers # Pour l'export ou affichage liste si besoin
    )

@app.route('/admin/export/<report_type>')
@admin_required
def export_report(report_type):
    df = None
    if report_type == 'popular_books':
        data_query = db.session.query(
                Livre.titre, 
                Livre.auteur,
                db.func.count(Historique.id).label('nombre_emprunts')
            ).outerjoin(Historique, Livre.id == Historique.media_id) \
            .group_by(Livre.id, Livre.titre, Livre.auteur) \
            .order_by(db.desc('nombre_emprunts')).all()
        df = pd.DataFrame(data_query, columns=['Livre', 'Auteur', 'Nombre d\'emprunts'])

    elif report_type == 'active_readers':
        data_query = db.session.query(
                User.username,
                db.func.count(Historique.id).label('nombre_emprunts')
            ).outerjoin(Historique, User.id == Historique.user_id) \
            .group_by(User.id, User.username) \
            .order_by(db.desc('nombre_emprunts')).all()
        df = pd.DataFrame(data_query, columns=['Lecteur', 'Nombre d\'emprunts'])
        
    else:
        flash("Type de rapport non valide.", "danger")
        return redirect(url_for('statistics'))

    if df is None or df.empty:
        flash(f"Aucune donnée à exporter pour le rapport '{report_type}'.", "info")
        return redirect(url_for('statistics'))

    output = BytesIO()
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Rapport')
        output.seek(0)
        
        return send_file(
            output, 
            download_name=f'rapport_{report_type}_{datetime.now().strftime("%Y%m%d")}.xlsx', 
            as_attachment=True, 
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        app.logger.error(f"Erreur lors de la génération du fichier Excel : {e}")
        flash("Une erreur s'est produite lors de la génération du rapport Excel.", "danger")
        return redirect(url_for('statistics'))


# Command to create database tables if they don't exist
# This should be run once, or use Flask-Migrate for more complex migrations.
@app.cli.command("init-db")
def init_db_command():
    """Initialise la base de données."""
    db.create_all()
    print("Base de données initialisée.")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables are created when running directly
        # Check if admin user exists, if not create one (for initial setup)
        if not User.query.filter_by(username="admin").first():
            admin_user = User(username="admin", password="admin", role="admin") # Set a secure password in production
            db.session.add(admin_user)
            db.session.commit()
            print("Utilisateur admin par défaut créé.")
    app.run(debug=True, port=5000)
# --- FIN DU FICHIER ---
