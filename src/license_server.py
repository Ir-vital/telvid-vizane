import sqlite3
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import os
import logging

# --- Configuration ---
DATABASE_FILE = 'licenses.db'

# Initialise l'application Flask
app = Flask(__name__)

# Configuration du logging pour Flask
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_db_connection():
    """Crée une connexion à la base de données."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row # Permet d'accéder aux colonnes par nom
    return conn

def init_db():
    """Initialise la base de données et la table si elles n'existent pas."""
    if os.path.exists(DATABASE_FILE):
        return # La base de données existe déjà

    app.logger.info("Création de la base de données 'licenses.db'...")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE licenses (
            key TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            user_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Ajout de quelques clés pour le test
    keys_to_add = [
        ("YEARLY-PREMIUM-12345", "yearly"),
        ("MONTHLY-TRIAL-67890", "monthly"),
        ("LIFETIME-SPECIAL-ABCDE", "lifetime"),
        ("ALREADY-USED-KEY-XYZ", "yearly"), # On l'associera à un user_id pour le test
    ]
    cursor.executemany('INSERT INTO licenses (key, type) VALUES (?, ?)', keys_to_add)
    # Simuler une clé déjà utilisée
    cursor.execute("UPDATE licenses SET user_id = 'un-autre-user-id-deja-enregistre' WHERE key = 'ALREADY-USED-KEY-XYZ'")
    
    conn.commit()
    conn.close()
    app.logger.info("Base de données initialisée avec des clés de test.")


@app.route('/validate', methods=['POST'])
def validate_license():
    """
    Endpoint de validation de licence qui utilise maintenant une base de données SQLite.
    """
    data = request.get_json()
    if not data or 'license_key' not in data or 'user_id' not in data:
        return jsonify({"status": "error", "message": "Requête invalide, champs manquants."}), 400

    license_key = data['license_key']
    user_id = data['user_id']

    app.logger.info(f"Tentative de validation pour la clé '{license_key}' et l'utilisateur '{user_id}'")
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. La clé existe-t-elle ?
    cursor.execute('SELECT * FROM licenses WHERE key = ?', (license_key,))
    key_info = cursor.fetchone()

    if key_info is None:
        conn.close()
        app.logger.warning(f"Échec de validation: Clé '{license_key}' non trouvée dans la base de données.")
        return jsonify({"status": "error", "message": "Clé de licence invalide."}), 404

    # 2. La clé est-elle déjà utilisée par un autre utilisateur ?
    if key_info["user_id"] is not None and key_info["user_id"] != user_id:
        conn.close()
        app.logger.warning(f"Échec de validation: Clé '{license_key}' déjà utilisée par l'utilisateur '{key_info['user_id']}'.")
        return jsonify({"status": "error", "message": "Cette clé de licence est déjà associée à un autre compte."}), 409

    # 3. La clé est valide, on la met à jour et on prépare la réponse
    app.logger.info(f"SUCCÈS: Clé '{license_key}' validée pour l'utilisateur '{user_id}'.")
    
    # On associe la clé à l'utilisateur
    cursor.execute('UPDATE licenses SET user_id = ? WHERE key = ?', (user_id, license_key))
    conn.commit()
    conn.close()

    license_type = key_info['type']
    
    # On calcule la date d'expiration
    days = {'monthly': 30, 'yearly': 365, 'lifetime': 36500}.get(license_type, 0)
    expiry_date = datetime.now() + timedelta(days=days)

    response_data = {
        "status": "success",
        "type": license_type,
        "expiry": expiry_date.isoformat()
    }
    
    return jsonify(response_data), 200

if __name__ == '__main__':
    init_db() # S'assure que la base de données est prête au lancement
    # Lance le serveur en mode debug. Il sera accessible sur http://127.0.0.1:5000
    app.run(host='0.0.0.0', port=5000, debug=True)