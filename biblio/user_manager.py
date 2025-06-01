import json
import os
# La ligne suivante est supprimée car nous n'utilisons plus le hachage
# from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(BASE_DIR, 'users.json')

def load_all_users():
    """Charge tous les utilisateurs depuis le fichier JSON."""
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_all_users(users):
    """Sauvegarde la liste complète des utilisateurs dans le fichier JSON."""
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

class User(UserMixin):
    """Classe utilisateur compatible avec Flask-Login."""
    # Le paramètre 'password_hash' est renommé 'password' pour plus de clarté
    def __init__(self, id, username, password, role='user'):
        self.id = id
        self.username = username
        self.password = password # Le mot de passe est maintenant en clair
        self.role = role

    @staticmethod
    def get(user_id):
        """Récupère un utilisateur par son ID."""
        users = load_all_users()
        for user_data in users:
            if user_data.get('id') == int(user_id):
                # On passe le mot de passe directement
                return User(id=user_data['id'], username=user_data['username'], password=user_data['password'], role=user_data['role'])
        return None

    @staticmethod
    def find_by_username(username):
        """Récupère un utilisateur par son nom d'utilisateur."""
        users = load_all_users()
        for user_data in users:
            if user_data.get('username') == username:
                # On passe le mot de passe directement
                return User(id=user_data['id'], username=user_data['username'], password=user_data['password'], role=user_data['role'])
        return None

    @staticmethod
    def create(username, password, role='user'):
        """Crée un nouvel utilisateur et le sauvegarde."""
        if User.find_by_username(username):
            return None

        users = load_all_users()
        new_id = max([u['id'] for u in users] or [0]) + 1

        new_user = {
            "id": new_id,
            "username": username,
            # MODIFICATION : On stocke le mot de passe en clair, sans hachage
            "password": password,
            "role": role
        }
        users.append(new_user)
        save_all_users(users)
        return User(id=new_id, username=username, password=new_user['password'], role=role)

    def check_password(self, password_input):
        """MODIFICATION : Vérifie si le mot de passe fourni correspond à celui stocké."""
        # On fait une simple comparaison de chaînes de caractères
        return self.password == password_input