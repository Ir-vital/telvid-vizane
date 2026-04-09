"""
Système de validation des entrées pour TelVid-Vizane
"""
import re
import os
import urllib.parse
from typing import List, Optional, Tuple
from pathlib import Path
from src.utils.error_handler import raise_validation_error
from src.utils.advanced_logger import get_app_logger


class URLValidator:
    """Validateur pour les URLs de vidéos"""
    
    # Patterns pour les plateformes supportées
    SUPPORTED_PATTERNS = {
        'youtube': [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
            r'(?:https?://)?(?:www\.)?youtu\.be/[\w-]+',
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/[\w-]+',
            r'(?:https?://)?(?:www\.)?youtube\.com/v/[\w-]+'
        ],
        'vimeo': [
            r'(?:https?://)?(?:www\.)?vimeo\.com/\d+',
            r'(?:https?://)?player\.vimeo\.com/video/\d+'
        ],
        'dailymotion': [
            r'(?:https?://)?(?:www\.)?dailymotion\.com/video/[\w-]+',
            r'(?:https?://)?dai\.ly/[\w-]+'
        ],
        'twitch': [
            r'(?:https?://)?(?:www\.)?twitch\.tv/videos/\d+',
            r'(?:https?://)?(?:www\.)?twitch\.tv/\w+/clip/[\w-]+'
        ]
    }
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Vérifie si l'URL est valide"""
        if not url or not url.strip():
            return False
        
        # Vérification basique de l'URL
        try:
            result = urllib.parse.urlparse(url)
            if not all([result.scheme, result.netloc]):
                return False
        except Exception:
            return False
        
        return True
    
    @staticmethod
    def is_supported_platform(url: str) -> Tuple[bool, Optional[str]]:
        """Vérifie si la plateforme est supportée"""
        if not URLValidator.is_valid_url(url):
            return False, None
        
        url_lower = url.lower()
        
        for platform, patterns in URLValidator.SUPPORTED_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, url_lower, re.IGNORECASE):
                    return True, platform
        
        return False, None
    
    @staticmethod
    def validate_video_url(url: str) -> str:
        """
        Valide et normalise une URL de vidéo
        
        Args:
            url: URL à valider
            
        Returns:
            URL normalisée
            
        Raises:
            TelVidError: Si l'URL n'est pas valide
        """
        logger = get_app_logger()
        
        if not url or not url.strip():
            raise_validation_error("L'URL ne peut pas être vide")
        
        url = url.strip()
        
        # Ajouter le protocole si manquant
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        if not URLValidator.is_valid_url(url):
            raise_validation_error("Format d'URL invalide")
        
        is_supported, platform = URLValidator.is_supported_platform(url)
        if not is_supported:
            raise_validation_error(
                "Plateforme non supportée. Plateformes supportées: YouTube, Vimeo, Dailymotion, Twitch",
                details=f"URL: {url}"
            )
        
        logger.info(f"URL validée pour la plateforme: {platform}")
        return url


class PathValidator:
    """Validateur pour les chemins de fichiers et dossiers"""
    
    @staticmethod
    def is_valid_directory(path: str) -> bool:
        """Vérifie si le chemin est un répertoire valide"""
        if not path or not path.strip():
            return False
        
        try:
            path_obj = Path(path)
            return path_obj.exists() and path_obj.is_dir()
        except Exception:
            return False
    
    @staticmethod
    def is_writable_directory(path: str) -> bool:
        """Vérifie si le répertoire est accessible en écriture"""
        if not PathValidator.is_valid_directory(path):
            return False
        
        try:
            # Tenter de créer un fichier temporaire
            test_file = Path(path) / '.telvid_write_test'
            test_file.touch()
            test_file.unlink()
            return True
        except Exception:
            return False
    
    @staticmethod
    def validate_output_path(path: str) -> str:
        """
        Valide un chemin de sortie pour les téléchargements
        
        Args:
            path: Chemin à valider
            
        Returns:
            Chemin normalisé et validé
            
        Raises:
            TelVidError: Si le chemin n'est pas valide
        """
        if not path or not path.strip():
            raise_validation_error("Le chemin de sortie ne peut pas être vide")
        
        path = path.strip()
        
        # Expansion des variables d'environnement et du tilde
        path = os.path.expanduser(os.path.expandvars(path))
        
        # Créer le répertoire s'il n'existe pas
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise_validation_error(
                "Impossible de créer le répertoire de sortie",
                details=str(e)
            )
        
        if not PathValidator.is_valid_directory(path):
            raise_validation_error("Le chemin spécifié n'est pas un répertoire valide")
        
        if not PathValidator.is_writable_directory(path):
            raise_validation_error("Permissions insuffisantes pour écrire dans ce répertoire")
        
        return str(Path(path).resolve())
    
    @staticmethod
    def validate_filename(filename: str) -> str:
        """
        Valide et nettoie un nom de fichier
        
        Args:
            filename: Nom de fichier à valider
            
        Returns:
            Nom de fichier nettoyé
        """
        if not filename or not filename.strip():
            raise_validation_error("Le nom de fichier ne peut pas être vide")
        
        # Caractères interdits dans les noms de fichiers Windows
        forbidden_chars = r'<>:"/\|?*'
        
        # Nettoyer le nom de fichier
        clean_name = filename.strip()
        for char in forbidden_chars:
            clean_name = clean_name.replace(char, '_')
        
        # Limiter la longueur
        if len(clean_name) > 200:
            clean_name = clean_name[:200]
        
        # Éviter les noms réservés Windows
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        
        name_without_ext = Path(clean_name).stem.upper()
        if name_without_ext in reserved_names:
            clean_name = f"video_{clean_name}"
        
        return clean_name


class LicenseValidator:
    """Validateur pour les clés de licence"""
    
    # Format attendu: TELVID-PREMIUM-YYYY-XXXXXXXX
    LICENSE_PATTERN = r'^TELVID-(PREMIUM|TRIAL)-\d{4}-[A-Z0-9]{8}$'
    
    @staticmethod
    def is_valid_format(license_key: str) -> bool:
        """Vérifie le format de la clé de licence"""
        if not license_key or not license_key.strip():
            return False
        
        return bool(re.match(LicenseValidator.LICENSE_PATTERN, license_key.strip().upper()))
    
    @staticmethod
    def validate_license_key(license_key: str) -> str:
        """
        Valide une clé de licence
        
        Args:
            license_key: Clé de licence à valider
            
        Returns:
            Clé de licence normalisée
            
        Raises:
            TelVidError: Si la clé n'est pas valide
        """
        if not license_key or not license_key.strip():
            raise_validation_error("La clé de licence ne peut pas être vide")
        
        license_key = license_key.strip().upper()
        
        if not LicenseValidator.is_valid_format(license_key):
            raise_validation_error(
                "Format de clé de licence invalide",
                details="Format attendu: TELVID-PREMIUM-YYYY-XXXXXXXX"
            )
        
        return license_key


class ConfigValidator:
    """Validateur pour les valeurs de configuration"""
    
    @staticmethod
    def validate_positive_int(value: str, name: str) -> int:
        """Valide un entier positif"""
        try:
            int_value = int(value)
            if int_value <= 0:
                raise_validation_error(f"{name} doit être un nombre positif")
            return int_value
        except ValueError:
            raise_validation_error(f"{name} doit être un nombre entier valide")
    
    @staticmethod
    def validate_range_int(value: str, name: str, min_val: int, max_val: int) -> int:
        """Valide un entier dans une plage"""
        try:
            int_value = int(value)
            if not (min_val <= int_value <= max_val):
                raise_validation_error(
                    f"{name} doit être entre {min_val} et {max_val}"
                )
            return int_value
        except ValueError:
            raise_validation_error(f"{name} doit être un nombre entier valide")
    
    @staticmethod
    def validate_choice(value: str, name: str, choices: List[str]) -> str:
        """Valide qu'une valeur fait partie des choix autorisés"""
        if value not in choices:
            raise_validation_error(
                f"{name} doit être l'une des valeurs suivantes: {', '.join(choices)}"
            )
        return value
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Valide une adresse email"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not email or not email.strip():
            raise_validation_error("L'adresse email ne peut pas être vide")
        
        email = email.strip().lower()
        
        if not re.match(email_pattern, email):
            raise_validation_error("Format d'adresse email invalide")
        
        return email


class InputSanitizer:
    """Utilitaires pour nettoyer les entrées utilisateur"""
    
    @staticmethod
    def sanitize_string(text: str, max_length: int = 1000) -> str:
        """Nettoie une chaîne de caractères"""
        if not text:
            return ""
        
        # Supprimer les caractères de contrôle
        sanitized = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        # Limiter la longueur
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Nettoie un nom de fichier"""
        return PathValidator.validate_filename(filename)
    
    @staticmethod
    def sanitize_url(url: str) -> str:
        """Nettoie une URL"""
        if not url:
            return ""
        
        # Supprimer les espaces et caractères de contrôle
        url = InputSanitizer.sanitize_string(url)
        
        # Encoder les caractères spéciaux si nécessaire
        try:
            # Vérifier si l'URL est déjà encodée
            decoded = urllib.parse.unquote(url)
            if decoded != url:
                return url  # Déjà encodée
            
            # Parser et reconstruire l'URL pour la normaliser
            parsed = urllib.parse.urlparse(url)
            return urllib.parse.urlunparse(parsed)
        except Exception:
            return url


# Fonctions utilitaires globales
def validate_and_sanitize_input(input_data: dict) -> dict:
    """
    Valide et nettoie un dictionnaire d'entrées utilisateur
    
    Args:
        input_data: Dictionnaire des données à valider
        
    Returns:
        Dictionnaire des données validées et nettoyées
    """
    sanitized = {}
    
    for key, value in input_data.items():
        if isinstance(value, str):
            sanitized[key] = InputSanitizer.sanitize_string(value)
        else:
            sanitized[key] = value
    
    return sanitized
