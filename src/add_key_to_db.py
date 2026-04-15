import sqlite3
import sys
import os

# Cherche licenses.db dans plusieurs emplacements possibles
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
POSSIBLE_PATHS = [
    os.path.join(SCRIPT_DIR, '..', 'licenses.db'),   # Racine projet local
    os.path.join(os.path.expanduser('~'), 'licenses.db'),  # /home/vizane/licenses.db sur PythonAnywhere
    os.path.join(SCRIPT_DIR, 'licenses.db'),           # src/licenses.db fallback
]

DATABASE_FILE = None
for path in POSSIBLE_PATHS:
    if os.path.exists(os.path.normpath(path)):
        DATABASE_FILE = os.path.normpath(path)
        break

if DATABASE_FILE is None:
    # Si aucun fichier trouvé, utiliser la racine home par défaut
    DATABASE_FILE = os.path.join(os.path.expanduser('~'), 'licenses.db')


def add_key(key, license_type):
    """Ajoute une nouvelle clé à la base de données."""
    if not key or not license_type:
        print("Erreur: La clé et le type de licence sont requis.")
        return

    valid_types = ["monthly", "yearly", "lifetime"]
    if license_type not in valid_types:
        print(f"Erreur: Type de licence '{license_type}' invalide.")
        print(f"Les types valides sont : {', '.join(valid_types)}")
        return

    print(f"Base de données utilisée : {DATABASE_FILE}")

    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        cursor.execute("INSERT OR IGNORE INTO licenses (key, type) VALUES (?, ?)", (key, license_type))
        conn.commit()

        if cursor.rowcount > 0:
            print(f"✅ Clé '{key}' de type '{license_type}' ajoutée avec succès.")
        else:
            print(f"⚠️ La clé '{key}' existait déjà dans la base de données.")

    except sqlite3.Error as e:
        print(f"❌ Erreur de base de données: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python add_key_to_db.py <CLE_DE_LICENCE> <TYPE>")
        print("Exemple: python add_key_to_db.py MONTHLY-A3F2-B891-C4D7 monthly")
        sys.exit(1)

    license_key_to_add = sys.argv[1]
    key_type = sys.argv[2]
    add_key(license_key_to_add, key_type)
