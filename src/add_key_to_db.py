import sqlite3
import sys
import os

# S'assure que le chemin vers la base de données est toujours correct,
# peu importe d'où le script est lancé.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_FILE = os.path.join(SCRIPT_DIR, '..', 'licenses.db')  # Racine du projet

def add_key(key, license_type):
    """Ajoute une nouvelle clé à la base de données."""
    if not key or not license_type:
        print("Erreur: La clé et le type de licence sont requis.")
        return

    # Ajout d'une validation pour le type de licence
    valid_types = ["monthly", "yearly", "lifetime"]
    if license_type not in valid_types:
        print(f"Erreur: Type de licence '{license_type}' invalide.")
        print(f"Les types valides sont : {', '.join(valid_types)}")
        return

    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # INSERT OR IGNORE pour ne rien faire si la clé existe déjà
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
        print("Exemple: python add_key_to_db.py YEARLY-PREMIUM-12345 yearly")
        sys.exit(1)
        
    license_key_to_add = sys.argv[1]
    key_type = sys.argv[2]
    add_key(license_key_to_add, key_type)
