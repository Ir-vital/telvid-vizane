"""
Système de logging avancé pour TelVid-Vizane - VERSION ALTERNATIVE
Ce fichier est renommé pour éviter les conflits avec logger.py racine
Utilisé uniquement par les modules src/utils/
"""
import os
import sys
import logging
import logging.handlers
import logging.config
from pathlib import Path
from datetime import datetime
from typing import Optional


class TelVidLogger:
    """Gestionnaire de logs centralisé pour TelVid-Vizane"""
    
    def __init__(self):
        # Le pattern Singleton via l'instanciation au niveau du module
        # garantit que __init__ n'est appelé qu'une fois.
        self.setup_logging()
    
    def setup_logging(self):
        """Configure le système de logging"""
        # Créer le répertoire de logs s'il n'existe pas
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configuration du logging
        config_file = Path("config/logging.conf")
        if config_file.exists():
            try:
                logging.config.fileConfig(config_file)
            except Exception as e:
                # Fallback vers la configuration par défaut
                self._setup_default_logging()
                logging.error(f"Erreur lors du chargement de la config logging: {e}")
        else:
            self._setup_default_logging()
    
    def _setup_default_logging(self):
        """Configuration de logging par défaut"""
        # Format des logs
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler pour la console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Handler pour le fichier principal
        file_handler = logging.handlers.RotatingFileHandler(
            'logs/app.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        
        # Configuration du logger racine
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Obtient un logger avec le nom spécifié"""
        return logging.getLogger(name)
    
    @staticmethod
    def log_exception(logger: logging.Logger, message: str, exc_info: bool = True):
        """Log une exception avec le contexte complet"""
        logger.error(message, exc_info=exc_info)
    
    @staticmethod
    def log_performance(logger: logging.Logger, operation: str, duration: float):
        """Log les métriques de performance"""
        logger.info(f"Performance - {operation}: {duration:.2f}s")
    
    @staticmethod
    def log_user_action(logger: logging.Logger, action: str, details: Optional[str] = None):
        """Log les actions utilisateur"""
        message = f"Action utilisateur - {action}"
        if details:
            message += f": {details}"
        logger.info(message)
    
    @staticmethod
    def log_download_event(logger: logging.Logger, event: str, url: str, details: Optional[str] = None):
        """Log les événements de téléchargement"""
        message = f"Téléchargement - {event} - URL: {url}"
        if details:
            message += f" - {details}"
        logger.info(message)
    
    @staticmethod
    def log_license_event(logger: logging.Logger, event: str, license_type: str, details: Optional[str] = None):
        """Log les événements de licence"""
        message = f"Licence - {event} - Type: {license_type}"
        if details:
            message += f" - {details}"
        logger.info(message)


# Fonctions utilitaires pour faciliter l'utilisation
def get_app_logger() -> logging.Logger:
    """Obtient le logger principal de l'application"""
    TelVidLogger()  # Assure l'initialisation
    return TelVidLogger.get_logger('app')


def get_download_logger() -> logging.Logger:
    """Obtient le logger pour les téléchargements"""
    TelVidLogger()  # Assure l'initialisation
    return TelVidLogger.get_logger('downloader')


def get_license_logger() -> logging.Logger:
    """Obtient le logger pour les licences"""
    TelVidLogger()  # Assure l'initialisation
    return TelVidLogger.get_logger('license')


def get_gui_logger() -> logging.Logger:
    """Obtient le logger pour l'interface utilisateur"""
    TelVidLogger()  # Assure l'initialisation
    return TelVidLogger.get_logger('gui')


# Décorateurs pour le logging automatique
def log_function_call(logger: Optional[logging.Logger] = None):
    """Décorateur pour logger automatiquement les appels de fonction"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_app_logger()
            
            func_name = func.__name__
            logger.debug(f"Appel de fonction: {func_name}")
            
            try:
                start_time = datetime.now()
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                
                logger.debug(f"Fonction {func_name} terminée en {duration:.2f}s")
                return result
            except Exception as e:
                logger.error(f"Erreur dans {func_name}: {str(e)}", exc_info=True)
                raise
        
        return wrapper
    return decorator


def log_performance(logger: Optional[logging.Logger] = None):
    """Décorateur pour logger les performances"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_app_logger()
            
            start_time = datetime.now()
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                TelVidLogger.log_performance(logger, func.__name__, duration)
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(f"Erreur dans {func.__name__} après {duration:.2f}s: {str(e)}")
                raise
        
        return wrapper
    return decorator


# Initialisation automatique du système de logging
_logger_instance = TelVidLogger()
