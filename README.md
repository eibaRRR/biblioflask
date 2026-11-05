# 📚 BiblioTech — biblioflask

A complete library management web application built with **Flask**: a modern, intuitive interface for members and a powerful dashboard for administrators.

> 🇫🇷 **Français :** BiblioTech est une application web complète pour la gestion de bibliothèques, développée avec Flask. Elle offre une interface moderne et intuitive pour les utilisateurs et un tableau de bord puissant pour les administrateurs.

## Features

- **Authentication & roles** — Flask-Login with member/admin separation; a default admin account is created on first run
- **Book catalog** — add, edit, and search books (SQLAlchemy models)
- **Borrowing workflow** — loan tracking with due dates and borrowing history
- **Reservations** — book reservation system
- **Notifications** — notification system for members
- **Statistics dashboard** — borrowing insights and report generation
- **Excel export** — one-click report export (`.xlsx` via pandas)

## Stack

| Layer | Technology |
|---|---|
| Backend | Flask |
| ORM / DB | SQLAlchemy (SQLite) |
| Auth | Flask-Login |
| Forms | Flask-WTF |
| Reports | pandas + openpyxl |

## Run

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install flask flask-login flask-sqlalchemy flask-wtf pandas openpyxl
python biblio/app.py
```

Then open http://127.0.0.1:5000. On first run the app creates the SQLite database and a default `admin` user — change that password before any real deployment.

## License

[MIT](LICENSE)
