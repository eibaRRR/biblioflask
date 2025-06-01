# migrate_to_sqlite.py

import json
from datetime import datetime
from biblio.app import app
from biblio.models import db, User, Livre, Historique, Reservation, Media

def migrate():
    """
    Script de migration finalisé. Utilise db.drop_all() pour garantir que le
    schéma de la base de données est toujours synchronisé avec les modèles.
    """
    with app.app_context():
        # --- CORRECTION DÉFINITIVE ---
        # 1. Supprimer toutes les tables existantes pour effacer l'ancien schéma.
        print("Suppression des anciennes tables (drop_all)...")
        db.drop_all()
        print("Anciennes tables supprimées.")

        # 2. Recréer toutes les tables à partir des modèles à jour.
        print("Création des nouvelles tables (create_all)...")
        db.create_all()
        print("Nouvelles tables créées.")
        
        # La section de vidage des données n'est plus nécessaire car drop_all() a tout supprimé.

        # --- 1. Migration des utilisateurs ---
        try:
            with open('biblio/users.json', 'r', encoding='utf-8') as f:
                users_data = json.load(f)
            for user_data in users_data:
                # Utilisation de db.session.get pour éviter le LegacyAPIWarning
                if not db.session.get(User, user_data['id']):
                    new_user = User(
                        id=user_data['id'],
                        username=user_data['username'],
                        password=user_data['password'],
                        role=user_data['role']
                    )
                    db.session.add(new_user)
            db.session.commit()
            print(f"{len(users_data)} utilisateurs traités.")
        except FileNotFoundError:
            print("users.json non trouvé, migration des utilisateurs sautée.")
        
        # --- 2. Migration des livres et des réservations ---
        try:
            with open('biblio/bibliotheque.json', 'r', encoding='utf-8') as f:
                livres_data = json.load(f)

            print("Migration des livres (insensible à la casse)...")
            
            livres_a_migrer = {}
            titres_traites_minuscules = set()

            for livre_data in livres_data:
                titre = livre_data['titre']
                titre_minuscule = titre.lower()

                if titre_minuscule not in titres_traites_minuscules:
                    titres_traites_minuscules.add(titre_minuscule)
                    livres_a_migrer[titre] = livre_data
                else:
                    print(f"Titre en double (casse ignorée) trouvé dans bibliotheque.json : '{titre}'. Ignoré.")

            for livre_data in livres_a_migrer.values():
                statut = livre_data.get('statut', {})
                new_livre = Livre(
                    titre=livre_data['titre'],
                    auteur=livre_data['auteur'],
                    annee=livre_data['annee'],
                    genre=livre_data['genre'],
                    note=livre_data['note'],
                    description=livre_data.get('description', ''),
                    statut_etat=statut.get('etat', 'disponible'),
                    emprunte_par_id=statut.get('par_id'),
                    image_url=livre_data.get('image_url') # Ajout de l'URL de l'image
                )
                db.session.add(new_livre)
            
            # Pas besoin de flush ici, on peut tout commiter à la fin.
            print(f"{len(livres_a_migrer)} livres uniques ajoutés à la session.")
            
            # Le commit ici va sauvegarder les livres et leur assigner un ID
            db.session.commit()
            print("Livres sauvegardés.")

            # Migration des réservations après la création des livres
            livre_map = {livre.titre: livre for livre in Livre.query.all()}
            print("Migration des réservations...")
            for livre_data in livres_a_migrer.values():
                reservations_data = livre_data.get('reservations', [])
                if reservations_data:
                    livre_obj = livre_map.get(livre_data['titre'])
                    if livre_obj:
                        for user_id in reservations_data:
                            new_reservation = Reservation(user_id=user_id, media_id=livre_obj.id)
                            db.session.add(new_reservation)
            
            db.session.commit()
            print("Réservations sauvegardées.")

        except FileNotFoundError:
            print("bibliotheque.json non trouvé, migration des livres sautée.")
        
        # --- 3. Migration de l'historique ---
        # (le reste du script est inchangé)
        livres_db = Livre.query.all()
        livre_titre_to_id_map = {livre.titre: livre.id for livre in livres_db}
        try:
            with open('biblio/historique_emprunts.json', 'r', encoding='utf-8') as f:
                historique_data = json.load(f)

            for hist_data in historique_data:
                livre_id = livre_titre_to_id_map.get(hist_data['livre_titre'])
                if livre_id:
                    new_hist = Historique(
                    user_id=hist_data['user_id'],
                    media_id=livre_id,
                    date_emprunt=datetime.fromisoformat(hist_data['date_emprunt'].replace('Z', '')),
                    date_retour=datetime.fromisoformat(hist_data['date_retour'].replace('Z', '')) if hist_data.get('date_retour') else None,
                    date_retour_prevue=datetime.fromisoformat(hist_data['date_retour_prevue'].replace('Z', '')) if hist_data.get('date_retour_prevue') else None
                    )
                    db.session.add(new_hist)
            db.session.commit()
            print(f"{len(historique_data)} entrées d'historique traitées.")
        except FileNotFoundError:
            print("historique_emprunts.json non trouvé, migration de l'historique sautée.")

        print("\nMigration terminée avec succès !")

if __name__ == '__main__':
    migrate()