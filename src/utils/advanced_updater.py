"""
Système de mise à jour automatique pour TelVid-Vizane
"""
import os
import json
import requests
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from src.utils.advanced_logger import get_app_logger
from src.utils.config_manager import config_manager
from src.utils.error_handler import handle_errors, ErrorType


class UpdateInfo:
    """Informations sur une mise à jour"""
    
    def __init__(self, version: str, download_url: str, changelog: str, 
                 release_date: str, is_critical: bool = False):
        self.version = version
        self.download_url = download_url
        self.changelog = changelog
        self.release_date = release_date
        self.is_critical = is_critical
    
    def __str__(self):
        return f"Version {self.version} - {self.release_date}"


class AutoUpdater:
    """Gestionnaire de mise à jour automatique"""
    
    def __init__(self):
        self.logger = get_app_logger()
        self.current_version = "1.0.0"  # Version actuelle
        self.update_server_url = "https://api.telvid-vizane.com/updates"
        self.github_api_url = "https://api.github.com/repos/votre-username/telVidVIZANE/releases/latest"
        self.last_check_file = Path("data/last_update_check.json")
        self.update_cache_file = Path("data/update_cache.json")
        
        # Créer le répertoire data s'il n'existe pas
        Path("data").mkdir(exist_ok=True)
    
    @handle_errors(ErrorType.NETWORK_ERROR, show_user=False)
    def check_for_updates(self, force_check: bool = False) -> Optional[UpdateInfo]:
        """
        Vérifie s'il y a des mises à jour disponibles
        
        Args:
            force_check: Force la vérification même si récente
            
        Returns:
            UpdateInfo si une mise à jour est disponible, None sinon
        """
        # Vérifier si on doit faire la vérification
        if not force_check and not self._should_check_updates():
            self.logger.debug("Vérification de mise à jour ignorée (trop récente)")
            return None
        
        self.logger.info("Vérification des mises à jour...")
        
        try:
            # Essayer d'abord le serveur principal
            update_info = self._check_main_server()
            if not update_info:
                # Fallback vers GitHub
                update_info = self._check_github_releases()
            
            # Sauvegarder la date de dernière vérification
            self._save_last_check()
            
            if update_info:
                # Mettre en cache les informations de mise à jour
                self._cache_update_info(update_info)
                
                if self._is_newer_version(update_info.version):
                    self.logger.info(f"Mise à jour disponible: {update_info}")
                    return update_info
                else:
                    self.logger.info("Application à jour")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification des mises à jour: {e}")
            return None
    
    def _should_check_updates(self) -> bool:
        """Détermine si on doit vérifier les mises à jour"""
        if not self.last_check_file.exists():
            return True
        
        try:
            with open(self.last_check_file, 'r') as f:
                data = json.load(f)
            
            last_check = datetime.fromisoformat(data['last_check'])
            check_interval = config_manager.get_int('UPDATES', 'check_interval_hours', 24)
            
            return datetime.now() - last_check > timedelta(hours=check_interval)
            
        except Exception:
            return True
    
    def _check_main_server(self) -> Optional[UpdateInfo]:
        """Vérifie les mises à jour sur le serveur principal"""
        try:
            response = requests.get(
                f"{self.update_server_url}/latest",
                params={'current_version': self.current_version},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return UpdateInfo(
                    version=data['version'],
                    download_url=data['download_url'],
                    changelog=data['changelog'],
                    release_date=data['release_date'],
                    is_critical=data.get('is_critical', False)
                )
            
        except Exception as e:
            self.logger.debug(f"Serveur principal indisponible: {e}")
        
        return None
    
    def _check_github_releases(self) -> Optional[UpdateInfo]:
        """Vérifie les mises à jour sur GitHub"""
        try:
            response = requests.get(self.github_api_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Chercher l'asset Windows
                download_url = None
                for asset in data.get('assets', []):
                    if 'Windows' in asset['name'] and asset['name'].endswith('.zip'):
                        download_url = asset['browser_download_url']
                        break
                
                if download_url:
                    return UpdateInfo(
                        version=data['tag_name'].lstrip('v'),
                        download_url=download_url,
                        changelog=data['body'],
                        release_date=data['published_at'][:10],
                        is_critical=False
                    )
            
        except Exception as e:
            self.logger.debug(f"GitHub API indisponible: {e}")
        
        return None
    
    def _is_newer_version(self, new_version: str) -> bool:
        """Compare les versions pour déterminer si la nouvelle est plus récente"""
        try:
            current_parts = [int(x) for x in self.current_version.split('.')]
            new_parts = [int(x) for x in new_version.split('.')]
            
            # Égaliser les longueurs
            max_len = max(len(current_parts), len(new_parts))
            current_parts.extend([0] * (max_len - len(current_parts)))
            new_parts.extend([0] * (max_len - len(new_parts)))
            
            return new_parts > current_parts
            
        except Exception:
            return False
    
    def _save_last_check(self):
        """Sauvegarde la date de dernière vérification"""
        try:
            data = {'last_check': datetime.now().isoformat()}
            with open(self.last_check_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            self.logger.error(f"Impossible de sauvegarder la date de vérification: {e}")
    
    def _cache_update_info(self, update_info: UpdateInfo):
        """Met en cache les informations de mise à jour"""
        try:
            data = {
                'version': update_info.version,
                'download_url': update_info.download_url,
                'changelog': update_info.changelog,
                'release_date': update_info.release_date,
                'is_critical': update_info.is_critical,
                'cached_at': datetime.now().isoformat()
            }
            with open(self.update_cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Impossible de mettre en cache les infos de mise à jour: {e}")
    
    @handle_errors(ErrorType.NETWORK_ERROR)
    def download_update(self, update_info: UpdateInfo, progress_callback=None) -> Optional[Path]:
        """
        Télécharge une mise à jour
        
        Args:
            update_info: Informations sur la mise à jour
            progress_callback: Callback pour la progression
            
        Returns:
            Chemin vers le fichier téléchargé
        """
        self.logger.info(f"Téléchargement de la mise à jour {update_info.version}...")
        
        try:
            # Créer un fichier temporaire
            temp_file = Path(tempfile.gettempdir()) / f"telvid_update_{update_info.version}.zip"
            
            response = requests.get(update_info.download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            progress_callback(progress)
            
            self.logger.info(f"Mise à jour téléchargée: {temp_file}")
            return temp_file
            
        except Exception as e:
            self.logger.error(f"Erreur lors du téléchargement: {e}")
            return None
    
    @handle_errors(ErrorType.FILE_ERROR)
    def install_update(self, update_file: Path) -> bool:
        """
        Installe une mise à jour
        
        Args:
            update_file: Chemin vers le fichier de mise à jour
            
        Returns:
            True si l'installation a réussi
        """
        self.logger.info("Installation de la mise à jour...")
        
        try:
            # Créer un répertoire temporaire pour l'extraction
            extract_dir = Path(tempfile.gettempdir()) / "telvid_update_extract"
            extract_dir.mkdir(exist_ok=True)
            
            # Extraire l'archive
            with zipfile.ZipFile(update_file, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Créer un script de mise à jour
            update_script = self._create_update_script(extract_dir)
            
            if update_script:
                # Lancer le script de mise à jour et fermer l'application
                subprocess.Popen([update_script], shell=True)
                self.logger.info("Script de mise à jour lancé")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'installation: {e}")
            return False
    
    def _create_update_script(self, extract_dir: Path) -> Optional[Path]:
        """Crée un script de mise à jour"""
        try:
            script_path = Path(tempfile.gettempdir()) / "telvid_update.bat"
            
            current_exe = Path(os.sys.executable if getattr(os.sys, 'frozen', False) else __file__).parent
            new_exe = extract_dir / "TelVid.exe"
            
            script_content = f"""@echo off
echo Mise à jour de TelVid-Vizane...
timeout /t 3 /nobreak >nul

echo Sauvegarde de l'ancienne version...
if exist "{current_exe}.backup" del "{current_exe}.backup"
if exist "{current_exe}" ren "{current_exe}" "{current_exe.name}.backup"

echo Installation de la nouvelle version...
copy "{new_exe}" "{current_exe}"

echo Nettoyage...
rmdir /s /q "{extract_dir}"
del "{script_path}"

echo Redémarrage de l'application...
start "" "{current_exe}"
"""
            
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            return script_path
            
        except Exception as e:
            self.logger.error(f"Impossible de créer le script de mise à jour: {e}")
            return None
    
    def get_cached_update_info(self) -> Optional[UpdateInfo]:
        """Récupère les informations de mise à jour en cache"""
        try:
            if not self.update_cache_file.exists():
                return None
            
            with open(self.update_cache_file, 'r') as f:
                data = json.load(f)
            
            return UpdateInfo(
                version=data['version'],
                download_url=data['download_url'],
                changelog=data['changelog'],
                release_date=data['release_date'],
                is_critical=data.get('is_critical', False)
            )
            
        except Exception:
            return None
    
    def enable_auto_updates(self, enabled: bool):
        """Active ou désactive les mises à jour automatiques"""
        config_manager.set('UPDATES', 'auto_check_updates', str(enabled).lower())
        config_manager.save_config()
        self.logger.info(f"Mises à jour automatiques: {'activées' if enabled else 'désactivées'}")
    
    def is_auto_updates_enabled(self) -> bool:
        """Vérifie si les mises à jour automatiques sont activées"""
        return config_manager.get_bool('UPDATES', 'auto_check_updates', True)


# Instance globale de l'updater
auto_updater = AutoUpdater()
