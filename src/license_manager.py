import os
import json
import uuid
import hashlib
import time
from datetime import datetime, timedelta
import requests


def get_app_data_dir():
    """Retourne le dossier AppData pour stocker les fichiers de l'app."""
    app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
    app_dir = os.path.join(app_data, 'TelVid-Vizane')
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


class LicenseManager:
    def __init__(self):
        app_dir = get_app_data_dir()
        self.config_file = os.path.join(app_dir, 'premium_config.json')
        self.license_file = os.path.join(app_dir, 'license.json')
        self.is_premium = False
        self.license_key = ""
        self.license_type = "free"
        self.expiry_date = None
        self.user_id = self._get_or_create_user_id()
        self.load_license()

    def _get_or_create_user_id(self):
        """Génère ou récupère un ID utilisateur unique"""
        user_id_file = os.path.join(get_app_data_dir(), 'user_id.txt')
        if os.path.exists(user_id_file):
            with open(user_id_file, 'r') as f:
                return f.read().strip()
        else:
            user_id = str(uuid.uuid4())
            with open(user_id_file, 'w') as f:
                f.write(user_id)
            return user_id
    
    def load_license(self):
        """Charge les informations de licence depuis le fichier"""
        try:
            if os.path.exists(self.license_file):
                with open(self.license_file, 'r') as f:
                    data = json.load(f)
                    self.license_key = data.get('license_key', "")
                    self.license_type = data.get('license_type', "free")
                    expiry_str = data.get('expiry_date')
                    self.expiry_date = datetime.fromisoformat(expiry_str) if expiry_str else None
                    
                # Vérifier si la licence est valide
                if self.is_license_valid():
                    self.is_premium = True
        except Exception as e:
            print(f"Erreur lors du chargement de la licence: {e}")
            self.reset_license()
    
    def save_license(self):
        """Enregistre les informations de licence dans le fichier"""
        data = {
            'license_key': self.license_key,
            'license_type': self.license_type,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'user_id': self.user_id
        }
        with open(self.license_file, 'w') as f:
            json.dump(data, f)
    
    def reset_license(self):
        """Réinitialise la licence au mode gratuit"""
        self.license_key = ""
        self.license_type = "free"
        self.expiry_date = None
        self.is_premium = False
        self.save_license()

    def is_license_valid(self):
        """
        Vérifie si la licence locale est valide (activée et non expirée).
        La validation de la clé elle-même a déjà été faite par le serveur lors de l'activation.
        """
        if not self.is_premium or self.license_type == "free":
            return False

        # Pour les licences à vie, c'est toujours valide si activé.
        if self.license_type == "lifetime":
            return True

        # Pour les autres, vérifier la date d'expiration.
        if self.expiry_date and datetime.now() > self.expiry_date:
            # La licence a expiré, on la réinitialise.
            print("Licence expirée. Réinitialisation au mode gratuit.")
            self.reset_license()
            return False

        return True

    def _generate_license_hash(self, user_id, license_type):
        """Génère un hash pour la validation de licence"""
        # Dans une application réelle, utilisez une clé secrète et un algorithme plus robuste
        seed = f"{user_id}:{license_type}:TelVidVIZANE-Secret-Key"
        return hashlib.sha256(seed.encode()).hexdigest()
    
    def _validate_license_on_server(self, license_key):
        """
        Valide la clé de licence via une API serveur.
        """
        # Code réel pour l'appel au serveur
        API_URL = "https://vizane.pythonanywhere.com/validate"
        
        try:
            response = requests.post(API_URL, json={
                'license_key': license_key,
                'user_id': self.user_id
            }, timeout=15, headers={
                'User-Agent': 'TelVid-Vizane/1.0.0',
                'Content-Type': 'application/json'
            })
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return True, data
                else:
                    return False, data.get('message', 'Clé invalide')
            elif response.status_code == 404:
                return False, "Service de validation temporairement indisponible"
            else:
                return False, f"Erreur serveur: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, "Timeout de connexion au serveur de validation"
        except requests.exceptions.ConnectionError:
            return False, "Impossible de se connecter au serveur de validation"
        except requests.RequestException as e:
            return False, f"Erreur de connexion: {str(e)}"
        except Exception as e:
            return False, f"Erreur inattendue: {str(e)}"

    def activate_license(self, license_key):
        """Active une licence en la validant exclusivement auprès d'un serveur distant."""
        if not license_key or not license_key.strip():
            return False, "La clé de licence ne peut pas être vide."

        # 1. Valider la clé auprès du serveur. C'est maintenant la seule méthode de validation.
        is_valid_on_server, server_response = self._validate_license_on_server(license_key)

        if not is_valid_on_server:
            # Le serveur a refusé la clé, on arrête tout.
            error_message = server_response if isinstance(server_response, str) else "Clé invalide ou déjà utilisée."
            return False, error_message

        # 2. Le serveur a validé la clé. On traite sa réponse pour activer la licence localement.
        try:
            license_type = server_response.get('type')
            expiry_str = server_response.get('expiry')

            if not license_type or not expiry_str:
                return False, "Réponse du serveur de licence invalide (champs manquants)."

            expiry_date = datetime.fromisoformat(expiry_str)

            # 3. Tout est bon, on active la licence localement.
            self.license_key = license_key
            self.license_type = license_type
            self.expiry_date = expiry_date
            self.is_premium = True
            self.save_license()

            return True, f"Licence {license_type} activée avec succès jusqu'au {expiry_date.strftime('%d/%m/%Y')}"

        except (ValueError, TypeError) as e:
            # Erreur si la date n'est pas au format ISO ou si la réponse est malformée
            print(f"Erreur lors du traitement de la réponse du serveur: {e}")
            return False, f"Réponse du serveur de licence invalide: {e}"