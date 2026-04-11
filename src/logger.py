"""
Système de logging centralisé pour TelVid-Vizane
Gestion des logs avec rotation et niveaux multiples
"""

import logging
import logging.handlers
import os
from datetime import datetime
import json

class AppLogger:
    def __init__(self, app_name="TelVid-Vizane"):
        self.app_name = app_name
        app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
        self.log_dir = os.path.join(app_data, 'TelVid-Vizane', 'logs')
        self.ensure_log_directory()
        self.setup_loggers()
    
    def ensure_log_directory(self):
        """Crée le dossier de logs s'il n'existe pas"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def setup_loggers(self):
        """Configure les différents loggers"""
        # Logger principal de l'application
        self.app_logger = self._create_logger(
            "app", 
            os.path.join(self.log_dir, "app.log"),
            logging.INFO
        )
        
        # Logger pour les téléchargements
        self.download_logger = self._create_logger(
            "download",
            os.path.join(self.log_dir, "downloads.log"),
            logging.INFO
        )
        
        # Logger pour les erreurs
        self.error_logger = self._create_logger(
            "error",
            os.path.join(self.log_dir, "errors.log"),
            logging.ERROR
        )
        
        # Logger pour les licences
        self.license_logger = self._create_logger(
            "license",
            os.path.join(self.log_dir, "license.log"),
            logging.INFO
        )
    
    def _create_logger(self, name, log_file, level):
        """Crée un logger avec rotation des fichiers"""
        logger = logging.getLogger(f"{self.app_name}.{name}")
        logger.setLevel(level)
        
        # Éviter la duplication des handlers
        if logger.handlers:
            return logger
        
        # Handler pour fichier avec rotation (max 5MB, 5 fichiers)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, 
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5,
            encoding='utf-8'
        )
        
        # Format des logs
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Handler pour console (seulement erreurs)
        if level >= logging.ERROR:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        logger.addHandler(file_handler)
        return logger
    
    def log_app_event(self, message, level=logging.INFO):
        """Log un événement de l'application"""
        self.app_logger.log(level, message)
    
    def log_download_start(self, url, format_type="unknown"):
        """Log le début d'un téléchargement"""
        message = f"Début téléchargement - URL: {url}, Format: {format_type}"
        self.download_logger.info(message)
    
    def log_download_success(self, url, title, file_path, duration=None):
        """Log un téléchargement réussi"""
        duration_str = f", Durée: {duration}s" if duration else ""
        message = f"Téléchargement réussi - URL: {url}, Titre: {title}, Fichier: {file_path}{duration_str}"
        self.download_logger.info(message)
    
    def log_download_error(self, url, error_message):
        """Log une erreur de téléchargement"""
        message = f"Erreur téléchargement - URL: {url}, Erreur: {error_message}"
        self.download_logger.error(message)
        self.error_logger.error(message)
    
    def log_license_event(self, event_type, details=""):
        """Log un événement lié aux licences"""
        message = f"Licence - {event_type}: {details}"
        self.license_logger.info(message)
    
    def log_error(self, error_message, exception=None):
        """Log une erreur générale"""
        if exception:
            message = f"Erreur: {error_message} - Exception: {str(exception)}"
        else:
            message = f"Erreur: {error_message}"
        self.error_logger.error(message)
    
    def log_settings_change(self, setting_name, old_value, new_value):
        """Log un changement de paramètre"""
        message = f"Paramètre modifié - {setting_name}: {old_value} -> {new_value}"
        self.app_logger.info(message)
    
    def log_update_check(self, result, version=None):
        """Log une vérification de mise à jour"""
        if result:
            message = f"Mise à jour disponible - Version: {version}"
        else:
            message = "Aucune mise à jour disponible"
        self.app_logger.info(message)
    
    def get_recent_logs(self, log_type="app", lines=50):
        """Récupère les logs récents"""
        log_files = {
            "app": os.path.join(self.log_dir, "app.log"),
            "download": os.path.join(self.log_dir, "downloads.log"),
            "error": os.path.join(self.log_dir, "errors.log"),
            "license": os.path.join(self.log_dir, "license.log")
        }
        
        log_file = log_files.get(log_type)
        if not log_file or not os.path.exists(log_file):
            return []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
        except Exception as e:
            self.log_error(f"Erreur lecture logs: {e}")
            return []
    
    def export_logs(self, export_path, log_types=None):
        """Exporte les logs vers un fichier"""
        if log_types is None:
            log_types = ["app", "download", "error", "license"]
        
        try:
            export_data = {
                "export_date": datetime.now().isoformat(),
                "app_name": self.app_name,
                "logs": {}
            }
            
            for log_type in log_types:
                export_data["logs"][log_type] = self.get_recent_logs(log_type, 1000)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.log_app_event(f"Logs exportés vers: {export_path}")
            return True
        except Exception as e:
            self.log_error(f"Erreur export logs: {e}")
            return False
    
    def clear_old_logs(self, days_to_keep=30):
        """Nettoie les anciens logs"""
        try:
            cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 3600)
            
            for file_name in os.listdir(self.log_dir):
                file_path = os.path.join(self.log_dir, file_name)
                if os.path.isfile(file_path) and file_name.endswith('.log'):
                    if os.path.getmtime(file_path) < cutoff_date:
                        os.remove(file_path)
                        self.log_app_event(f"Ancien log supprimé: {file_name}")
        except Exception as e:
            self.log_error(f"Erreur nettoyage logs: {e}")

# Instance globale du logger
_app_logger = None

def get_logger():
    """Récupère l'instance globale du logger"""
    global _app_logger
    if _app_logger is None:
        _app_logger = AppLogger()
    return _app_logger

def log_app_event(message, level=logging.INFO):
    """Fonction raccourci pour logger un événement"""
    get_logger().log_app_event(message, level)

def log_download_start(url, format_type="unknown"):
    """Fonction raccourci pour logger le début d'un téléchargement"""
    get_logger().log_download_start(url, format_type)

def log_download_success(url, title, file_path, duration=None):
    """Fonction raccourci pour logger un téléchargement réussi"""
    get_logger().log_download_success(url, title, file_path, duration)

def log_download_error(url, error_message):
    """Fonction raccourci pour logger une erreur de téléchargement"""
    get_logger().log_download_error(url, error_message)

def log_license_event(event_type, details=""):
    """Fonction raccourci pour logger un événement de licence"""
    get_logger().log_license_event(event_type, details)

def log_error(error_message, exception=None):
    """Fonction raccourci pour logger une erreur"""
    get_logger().log_error(error_message, exception)

def log_settings_change(setting_name, old_value, new_value):
    """Fonction raccourci pour logger un changement de paramètre"""
    get_logger().log_settings_change(setting_name, old_value, new_value)

def log_update_check(result, version=None):
    """Fonction raccourci pour logger une vérification de mise à jour"""
    get_logger().log_update_check(result, version)
