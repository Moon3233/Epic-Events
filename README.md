# Epic Events

CRM en ligne de commande pour gérer les collaborateurs, clients, contrats et événements d’Epic Events.

## Technologies

Python 3.9+, PostgreSQL, SQLAlchemy, Click, Rich, Argon2, JWT, Sentry

## Installation

```bash
git clone https://github.com/Moon3233/Epic-Events.git
cd Epic-Events
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Renseigne dans `.env` : connexion PostgreSQL, `JWT_SECRET`, et optionnellement `SENTRY_DSN`.

## Base de données

Créer un utilisateur PostgreSQL non privilégié et une base, puis :

```bash
python epicevents.py init-db
python epicevents.py seed-admin
```

(`scripts/init_db.py` fait la même chose que `init-db`.)

## Utilisation

```bash
python epicevents.py login
python epicevents.py whoami
python epicevents.py clients list
python epicevents.py contracts list
python epicevents.py events list
python epicevents.py employees list
python epicevents.py --help
```

## Rôles

- **gestion** : collaborateurs, tous les contrats, assignation du support
- **commercial** : ses clients / contrats, création d’événement si contrat signé
- **support** : ses événements

Tout le monde peut lire clients, contrats et événements une fois connecté.

## Sécurité

Secrets uniquement dans `.env` (jamais commité). Mots de passe hashés (Argon2), accès via ORM, permissions par département.

Sentry journalise les exceptions inattendues, les créations/modifications de collaborateurs et les signatures de contrats.
