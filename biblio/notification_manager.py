import json
import os
from datetime import datetime

# Chemin vers le fichier de notifications
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NOTIFICATIONS_FILE = os.path.join(BASE_DIR, 'notifications.json')

def _load_notifications():
    """Charge les notifications depuis le fichier JSON."""
    try:
        with open(NOTIFICATIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def _save_notifications(notifications):
    """Sauvegarde la liste des notifications dans le fichier JSON."""
    with open(NOTIFICATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(notifications, f, indent=4, ensure_ascii=False)

def add_notification(user_id, message, category='info'):
    """Ajoute une notification pour un utilisateur spécifique."""
    notifications = _load_notifications()
    notifications.append({
        'user_id': user_id,
        'message': message,
        'category': category,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })
    _save_notifications(notifications)

def get_and_clear_notifications(user_id):
    """
    Récupère les notifications pour un utilisateur et les supprime du fichier
    pour qu'elles ne s'affichent qu'une seule fois.
    """
    all_notifications = _load_notifications()
    user_notifications = []
    other_users_notifications = []

    for notif in all_notifications:
        if notif.get('user_id') == user_id:
            user_notifications.append(notif)
        else:
            other_users_notifications.append(notif)
    
    # Si on a trouvé des notifications pour cet utilisateur, on met à jour le fichier
    # en ne gardant que celles des autres.
    if user_notifications:
        _save_notifications(other_users_notifications)
        
    return user_notifications