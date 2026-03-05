"""
Connexion à l'instance Odoo via l'API XML-RPC.
URL    : https://st.digital
API Key: configurée via la variable ODOO_API_KEY ou directement dans ce fichier
"""

import xmlrpc.client
import os
import sys

# ── Configuration ─────────────────────────────────────────────────────────────
ODOO_URL     = "https://st.digital"
ODOO_DB      = None          # sera détecté automatiquement si None
ODOO_API_KEY = os.environ.get("ODOO_API_KEY", "54fc70d2823c6e2a5b50716d66bac4f95a25309d")
# Avec une clé API Odoo, le login est "api" et le mot de passe est la clé elle-même
ODOO_LOGIN   = "api"
# ──────────────────────────────────────────────────────────────────────────────


def get_database(url: str) -> str:
    """Récupère le premier nom de base de données disponible sur le serveur."""
    db_service = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/db")
    databases = db_service.list()
    if not databases:
        raise RuntimeError("Aucune base de données trouvée sur le serveur.")
    return databases[0]


def authenticate(url: str, db: str, login: str, api_key: str) -> int:
    """Authentifie l'utilisateur et retourne son uid."""
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    version_info = common.version()
    print(f"[INFO] Serveur Odoo  : {version_info.get('server_version', 'inconnu')}")
    print(f"[INFO] Base de données : {db}")

    uid = common.authenticate(db, login, api_key, {})
    if not uid:
        raise PermissionError(
            "Authentification échouée. Vérifiez la clé API, le login et la base de données."
        )
    print(f"[INFO] Authentifié avec succès (uid={uid})")
    return uid


def get_models(url: str, db: str, uid: int, api_key: str) -> xmlrpc.client.ServerProxy:
    """Retourne le proxy du service 'object' (models)."""
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
    return models


def execute(models, db: str, uid: int, api_key: str, model: str, method: str, *args, **kwargs):
    """Raccourci pour appeler execute_kw."""
    return models.execute_kw(db, uid, api_key, model, method, list(args), kwargs)


def main():
    url     = ODOO_URL
    api_key = ODOO_API_KEY

    # 1. Déterminer la base de données
    db = ODOO_DB
    if not db:
        print("[INFO] Détection automatique de la base de données…")
        try:
            db = get_database(url)
        except Exception as exc:
            print(f"[ERREUR] Impossible de lister les bases : {exc}")
            print("[INFO] Essai avec 'st_digital' comme nom de base par défaut.")
            db = "st_digital"

    # 2. Authentification
    try:
        uid = authenticate(url, db, ODOO_LOGIN, api_key)
    except Exception as exc:
        print(f"[ERREUR] {exc}")
        sys.exit(1)

    # 3. Proxy modèles
    models = get_models(url, db, uid, api_key)

    # 4. Exemple : lister les 5 premiers partenaires
    print("\n[INFO] Récupération des 5 premiers partenaires (res.partner)…")
    try:
        partners = execute(
            models, db, uid, api_key,
            "res.partner", "search_read",
            [],
            fields=["id", "name", "email"],
            limit=5,
        )
        for p in partners:
            no_email = "pas d'email"
            print(f"  • [{p['id']}] {p['name']} — {p.get('email') or no_email}")
    except Exception as exc:
        print(f"[ERREUR] Impossible de récupérer les partenaires : {exc}")

    print("\n[OK] Connexion Odoo établie et opérationnelle.")
    return uid, db, models, api_key


if __name__ == "__main__":
    main()
