"""
Gestionnaire d'erreurs centralisé pour TelVid-Vizane
"""
import sys
import traceback
import tkinter as tk
from tkinter import messagebox
from typing import Optional, Callable, Any
from enum import Enum
from src.utils.advanced_logger import get_app_logger


class ErrorType(Enum):
    """Types d'erreurs de l'application"""
    NETWORK_ERROR = "network"
    FILE_ERROR = "file"
    PERMISSION_ERROR = "permission"
    VALIDATION_ERROR = "validation"
    LICENSE_ERROR = "license"
    DOWNLOAD_ERROR = "download"
    GUI_ERROR = "gui"
    UNKNOWN_ERROR = "unknown"


class ErrorSeverity(Enum):
    """Niveaux de gravité des erreurs"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TelVidError(Exception):
    """Exception personnalisée pour TelVid-Vizane"""
    
    def __init__(self, message: str, error_type: ErrorType = ErrorType.UNKNOWN_ERROR, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM, details: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.severity = severity
        self.details = details
        self.timestamp = None
    
    def __str__(self):
        return f"[{self.error_type.value.upper()}] {self.message}"


class ErrorHandler:
    """Gestionnaire centralisé d'erreurs"""
    
    def __init__(self):
        self.logger = get_app_logger()
        self.error_callbacks = {}
        self.setup_exception_handler()
    
    def setup_exception_handler(self):
        """Configure le gestionnaire d'exceptions global"""
        sys.excepthook = self.handle_uncaught_exception
    
    def handle_uncaught_exception(self, exc_type, exc_value, exc_traceback):
        """Gestionnaire pour les exceptions non capturées"""
        if issubclass(exc_type, KeyboardInterrupt):
            # Permettre l'interruption par Ctrl+C
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_msg = f"Exception non gérée: {exc_type.__name__}: {exc_value}"
        tb_str = ''.join(traceback.format_tb(exc_traceback))
        
        self.logger.critical(f"{error_msg}\n{tb_str}")
        
        # Afficher un message d'erreur à l'utilisateur
        try:
            messagebox.showerror(
                "Erreur critique",
                f"Une erreur inattendue s'est produite:\n\n{exc_value}\n\n"
                "L'application va se fermer. Consultez les logs pour plus de détails."
            )
        except:
            # Si même l'affichage du message échoue
            print(f"ERREUR CRITIQUE: {error_msg}")
    
    def handle_error(self, error: Exception, context: str = "", 
                    show_user: bool = True, error_type: ErrorType = ErrorType.UNKNOWN_ERROR):
        """
        Gère une erreur de manière centralisée
        
        Args:
            error: L'exception à gérer
            context: Contexte où l'erreur s'est produite
            show_user: Si True, affiche un message à l'utilisateur
            error_type: Type d'erreur pour la catégorisation
        """
        if isinstance(error, TelVidError):
            severity = error.severity
            error_type = error.error_type
            message = error.message
            details = error.details
        else:
            severity = ErrorSeverity.MEDIUM
            message = str(error)
            details = None
        
        # Log l'erreur
        log_message = f"Erreur dans {context}: {message}"
        if details:
            log_message += f" - Détails: {details}"
        
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message, exc_info=True)
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(log_message, exc_info=True)
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        # Notifier les callbacks enregistrés
        if error_type in self.error_callbacks:
            try:
                self.error_callbacks[error_type](error, context)
            except Exception as callback_error:
                self.logger.error(f"Erreur dans le callback d'erreur: {callback_error}")
        
        # Afficher à l'utilisateur si demandé
        if show_user:
            self._show_user_error(error_type, message, severity)
    
    def _show_user_error(self, error_type: ErrorType, message: str, severity: ErrorSeverity):
        """Affiche un message d'erreur approprié à l'utilisateur"""
        try:
            title, user_message = self._get_user_friendly_message(error_type, message, severity)
            
            if severity == ErrorSeverity.CRITICAL:
                messagebox.showerror(title, user_message)
            elif severity == ErrorSeverity.HIGH:
                messagebox.showerror(title, user_message)
            elif severity == ErrorSeverity.MEDIUM:
                messagebox.showwarning(title, user_message)
            else:
                messagebox.showinfo(title, user_message)
        
        except Exception as e:
            self.logger.error(f"Impossible d'afficher le message d'erreur: {e}")
    
    def _get_user_friendly_message(self, error_type: ErrorType, message: str, severity: ErrorSeverity):
        """Génère un message d'erreur convivial pour l'utilisateur"""
        error_messages = {
            ErrorType.NETWORK_ERROR: {
                "title": "Erreur de connexion",
                "message": "Problème de connexion réseau. Vérifiez votre connexion internet et réessayez."
            },
            ErrorType.FILE_ERROR: {
                "title": "Erreur de fichier",
                "message": "Problème avec un fichier. Vérifiez les permissions et l'espace disque disponible."
            },
            ErrorType.PERMISSION_ERROR: {
                "title": "Erreur de permissions",
                "message": "Permissions insuffisantes. Essayez de lancer l'application en tant qu'administrateur."
            },
            ErrorType.VALIDATION_ERROR: {
                "title": "Données invalides",
                "message": "Les données saisies ne sont pas valides. Vérifiez votre saisie."
            },
            ErrorType.LICENSE_ERROR: {
                "title": "Erreur de licence",
                "message": "Problème avec votre licence. Contactez le support si le problème persiste."
            },
            ErrorType.DOWNLOAD_ERROR: {
                "title": "Erreur de téléchargement",
                "message": "Impossible de télécharger la vidéo. Vérifiez l'URL et votre connexion."
            },
            ErrorType.GUI_ERROR: {
                "title": "Erreur d'interface",
                "message": "Problème avec l'interface utilisateur. Redémarrez l'application."
            },
            ErrorType.UNKNOWN_ERROR: {
                "title": "Erreur inconnue",
                "message": "Une erreur inattendue s'est produite."
            }
        }
        
        error_info = error_messages.get(error_type, error_messages[ErrorType.UNKNOWN_ERROR])
        title = error_info["title"]
        base_message = error_info["message"]
        
        # Ajouter le message technique si nécessaire
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            user_message = f"{base_message}\n\nDétails techniques: {message}"
        else:
            user_message = base_message
        
        return title, user_message
    
    def register_error_callback(self, error_type: ErrorType, callback: Callable):
        """Enregistre un callback pour un type d'erreur spécifique"""
        self.error_callbacks[error_type] = callback
        self.logger.debug(f"Callback enregistré pour {error_type.value}")
    
    def create_error(self, message: str, error_type: ErrorType = ErrorType.UNKNOWN_ERROR,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM, details: Optional[str] = None) -> TelVidError:
        """Crée une nouvelle erreur TelVid"""
        return TelVidError(message, error_type, severity, details)


# Décorateurs pour la gestion d'erreurs
def handle_errors(error_type: ErrorType = ErrorType.UNKNOWN_ERROR, 
                 show_user: bool = True, context: str = ""):
    """Décorateur pour gérer automatiquement les erreurs d'une fonction"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler.handle_error(
                    e, 
                    context=context or func.__name__, 
                    show_user=show_user, 
                    error_type=error_type
                )
                return None
        return wrapper
    return decorator


def safe_execute(func: Callable, *args, default_return: Any = None, 
                error_type: ErrorType = ErrorType.UNKNOWN_ERROR, **kwargs) -> Any:
    """Exécute une fonction de manière sécurisée avec gestion d'erreurs"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_handler.handle_error(e, context=func.__name__, error_type=error_type)
        return default_return


# Instance globale du gestionnaire d'erreurs
error_handler = ErrorHandler()


# Fonctions utilitaires
def raise_network_error(message: str, details: Optional[str] = None):
    """Lève une erreur réseau"""
    raise TelVidError(message, ErrorType.NETWORK_ERROR, ErrorSeverity.HIGH, details)


def raise_file_error(message: str, details: Optional[str] = None):
    """Lève une erreur de fichier"""
    raise TelVidError(message, ErrorType.FILE_ERROR, ErrorSeverity.MEDIUM, details)


def raise_validation_error(message: str, details: Optional[str] = None):
    """Lève une erreur de validation"""
    raise TelVidError(message, ErrorType.VALIDATION_ERROR, ErrorSeverity.LOW, details)


def raise_license_error(message: str, details: Optional[str] = None):
    """Lève une erreur de licence"""
    raise TelVidError(message, ErrorType.LICENSE_ERROR, ErrorSeverity.HIGH, details)


def raise_download_error(message: str, details: Optional[str] = None):
    """Lève une erreur de téléchargement"""
    raise TelVidError(message, ErrorType.DOWNLOAD_ERROR, ErrorSeverity.MEDIUM, details)
