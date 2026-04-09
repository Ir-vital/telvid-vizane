"""
Gestionnaire de configuration centralisé pour TelVid-Vizane
"""
import os
import configparser
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union
from src.utils.advanced_logger import get_app_logger


class ConfigManager:
    """Gestionnaire centralisé de configuration"""
    
    def __init__(self):
        self.logger = get_app_logger()
        self.config_file = Path("config/app_config.ini")
        self._config = None
        self.load_config()
    
    def load_config(self):
        """Charge la configuration depuis le fichier"""
        self._config = configparser.ConfigParser()
        
        try:
            if self.config_file.exists():
                self._config.read(self.config_file, encoding='utf-8')
                self.logger.info(f"Configuration chargée depuis {self.config_file}")
            else:
                self.logger.warning(f"Fichier de configuration non trouvé: {self.config_file}")
                self._create_default_config()
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement de la configuration: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """Crée une configuration par défaut"""
        self._config = configparser.ConfigParser()
        
        # Configuration par défaut
        default_config = {
            'APPLICATION': {
                'name': 'TelVid-Vizane',
                'version': '1.0.0',
                'debug': 'false',
                'log_level': 'INFO'
            },
            'GUI': {
                'theme': 'dark',
                'window_width': '900',
                'window_height': '750'
            },
            'DOWNLOAD': {
                'default_output_path': '~/Downloads',
                'max_retries': '3',
                'timeout': '30'
            }
        }
        
        for section, options in default_config.items():
            self._config.add_section(section)
            for key, value in options.items():
                self._config.set(section, key, value)
        
        self.save_config()
    
    def save_config(self):
        """Sauvegarde la configuration"""
        try:
            # Créer le répertoire config s'il n'existe pas
            self.config_file.parent.mkdir(exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self._config.write(f)
            
            self.logger.info("Configuration sauvegardée")
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde: {e}")
    
    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        """Récupère une valeur de configuration"""
        try:
            return self._config.get(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            self.logger.warning(f"Configuration manquante: [{section}] {key}")
            return fallback
    
    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """Récupère une valeur entière"""
        try:
            return self._config.getint(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback
    
    def get_float(self, section: str, key: str, fallback: float = 0.0) -> float:
        """Récupère une valeur flottante"""
        try:
            return self._config.getfloat(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback
    
    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        """Récupère une valeur booléenne"""
        try:
            return self._config.getboolean(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback
    
    def set(self, section: str, key: str, value: Any):
        """Définit une valeur de configuration"""
        try:
            if not self._config.has_section(section):
                self._config.add_section(section)
            
            self._config.set(section, key, str(value))
            self.logger.debug(f"Configuration mise à jour: [{section}] {key} = {value}")
        except Exception as e:
            self.logger.error(f"Erreur lors de la définition de [{section}] {key}: {e}")
    
    def get_section(self, section: str) -> Dict[str, str]:
        """Récupère toute une section de configuration"""
        try:
            return dict(self._config.items(section))
        except configparser.NoSectionError:
            self.logger.warning(f"Section non trouvée: {section}")
            return {}
    
    def has_section(self, section: str) -> bool:
        """Vérifie si une section existe"""
        return self._config.has_section(section)
    
    def has_option(self, section: str, key: str) -> bool:
        """Vérifie si une option existe"""
        return self._config.has_option(section, key)
    
    def remove_option(self, section: str, key: str) -> bool:
        """Supprime une option"""
        try:
            result = self._config.remove_option(section, key)
            if result:
                self.logger.info(f"Option supprimée: [{section}] {key}")
            return result
        except configparser.NoSectionError:
            return False
    
    def remove_section(self, section: str) -> bool:
        """Supprime une section"""
        try:
            result = self._config.remove_section(section)
            if result:
                self.logger.info(f"Section supprimée: {section}")
            return result
        except Exception as e:
            self.logger.error(f"Erreur lors de la suppression de la section {section}: {e}")
            return False
    
    def reload(self):
        """Recharge la configuration depuis le fichier"""
        self.load_config()
        self.logger.info("Configuration rechargée")
    
    def get_app_config(self) -> Dict[str, Any]:
        """Récupère la configuration de l'application"""
        return {
            'name': self.get('APPLICATION', 'name', 'TelVid-Vizane'),
            'version': self.get('APPLICATION', 'version', '1.0.0'),
            'debug': self.get_bool('APPLICATION', 'debug', False),
            'log_level': self.get('APPLICATION', 'log_level', 'INFO'),
            'data_dir': self.get('APPLICATION', 'data_dir', './data'),
            'temp_dir': self.get('APPLICATION', 'temp_dir', './temp'),
            'max_concurrent_downloads': self.get_int('APPLICATION', 'max_concurrent_downloads', 3)
        }
    
    def get_gui_config(self) -> Dict[str, Any]:
        """Récupère la configuration de l'interface"""
        return {
            'theme': self.get('GUI', 'theme', 'dark'),
            'color_theme': self.get('GUI', 'color_theme', 'dark-blue'),
            'window_width': self.get_int('GUI', 'window_width', 900),
            'window_height': self.get_int('GUI', 'window_height', 750),
            'min_width': self.get_int('GUI', 'min_width', 800),
            'min_height': self.get_int('GUI', 'min_height', 650),
            'icon_size': self.get_int('GUI', 'icon_size', 28),
            'font_family': self.get('GUI', 'font_family', 'Segoe UI'),
            'font_size': self.get_int('GUI', 'font_size', 12)
        }
    
    def get_download_config(self) -> Dict[str, Any]:
        """Récupère la configuration de téléchargement"""
        return {
            'default_output_path': self.get('DOWNLOAD', 'default_output_path', '~/Downloads'),
            'max_retries': self.get_int('DOWNLOAD', 'max_retries', 3),
            'timeout': self.get_int('DOWNLOAD', 'timeout', 30),
            'chunk_size': self.get_int('DOWNLOAD', 'chunk_size', 1024),
            'user_agent': self.get('DOWNLOAD', 'user_agent', 'TelVid-Vizane/1.0.0'),
            'max_file_size_mb': self.get_int('DOWNLOAD', 'max_file_size_mb', 2048),
            'supported_formats': self.get('DOWNLOAD', 'supported_formats', 'mp4,mkv,avi,mov,webm,mp3,m4a,wav,flac').split(',')
        }
    
    def get_premium_config(self) -> Dict[str, Any]:
        """Récupère la configuration premium"""
        return {
            'trial_period_days': self.get_int('PREMIUM', 'trial_period_days', 7),
            'max_free_downloads': self.get_int('PREMIUM', 'max_free_downloads', 10),
            'license_check_interval': self.get_int('PREMIUM', 'license_check_interval', 3600),
            'payment_timeout': self.get_int('PREMIUM', 'payment_timeout', 300),
            'supported_payment_methods': self.get('PREMIUM', 'supported_payment_methods', 'lumicash,mobile_money,paypal').split(',')
        }


# Instance unique (Singleton) du gestionnaire de configuration, exportée pour être utilisée dans l'application.
config_manager = ConfigManager()
