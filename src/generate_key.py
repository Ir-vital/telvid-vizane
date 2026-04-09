import hashlib
import time
import sqlite3
import os
from datetime import datetime, timedelta

# Chemin vers la base de données à la racine du projet
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_FILE = os.path.join(SCRIPT_DIR, '..', 'licenses.db')


def generate_unique_key(plan_type):
    """Génère une clé de licence unique et aléatoire."""
    unique_id = hashlib.sha256(f"{time.time()}-{os.urandom(16)}".encode()).hexdigest()[:12].upper()
    prefix = {"monthly": "MONTHLY", "yearly": "YEARLY", "lifetime": "LIFETIME"}.get(plan_type, "PLAN")
    return f"{prefix}-{unique_id[:4]}-{unique_id[4:8]}-{unique_id[8:12]}"


def insert_key_into_db(license_key, plan_type):
    """Insère la clé générée dans la base de données SQLite."""
    if not os.path.exists(DATABASE_FILE):
        print(f"ERREUR: Base de données introuvable à '{DATABASE_FILE}'.")
        print("Assurez-vous que le serveur de licence a été lancé au moins une fois pour créer la DB.")
        return False

    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO licenses (key, type) VALUES (?, ?)", (license_key, plan_type))
        conn.commit()
        inserted = cursor.rowcount > 0
        conn.close()
        return inserted
    except sqlite3.Error as e:
        print(f"ERREUR base de données: {e}")
        return False


def generate_key():
    """
    Outil en ligne de commande pour générer et enregistrer une clé de licence pour un client.
    """
    print("--- Générateur de Clés de Licence TelVid-Vizane ---")

    # Demander le type de plan
    print("\nChoisissez le type de plan :")
    print("1: Mensuel (monthly)")
    print("2: Annuel (yearly)")
    print("3: À vie (lifetime)")
    plan_choice = input("Votre choix (1, 2, ou 3) : ").strip()

    plan_map = {"1": "monthly", "2": "yearly", "3": "lifetime"}
    plan_type = plan_map.get(plan_choice)

    if not plan_type:
        print("Erreur : Choix de plan invalide.")
        return

    # Générer la clé
    license_key = generate_unique_key(plan_type)

    # Insérer dans la base de données
    success = insert_key_into_db(license_key, plan_type)

    print("\n--- Clé de Licence Générée ---")
    print(f"Plan    : {plan_type}")
    print(f"Clé     : {license_key}")

    if success:
        print("Statut  : ✅ Enregistrée dans la base de données")
    else:
        print("Statut  : ⚠️  Clé déjà existante ou erreur DB (clé toujours valide)")

    print("---------------------------------")
    print("Copiez cette clé et envoyez-la à votre client.")


if __name__ == "__main__":
    generate_key()
