# Documentation API - TelVid-Vizane

## Vue d'ensemble

Cette documentation décrit l'API interne de TelVid-Vizane et les modules principaux.

## Modules principaux

### 1. VideoDownloader (`downloader.py`)

#### Classe `VideoDownloader`

Gestionnaire principal pour le téléchargement de vidéos utilisant yt-dlp.

```python
class VideoDownloader:
    def __init__(self):
        """Initialise le downloader avec les options par défaut."""
    
    def download_video(self, url: str, output_path: str, 
                      progress_callback=None, completion_callback=None):
        """
        Télécharge une vidéo depuis l'URL spécifiée.
        
        Args:
            url (str): URL de la vidéo à télécharger
            output_path (str): Chemin de destination
            progress_callback (callable, optional): Callback pour la progression
            completion_callback (callable, optional): Callback de completion
        """
```

### 2. LicenseManager (`license_manager.py`)

#### Classe `LicenseManager`

Gestionnaire du système de licences premium.

```python
class LicenseManager:
    def __init__(self):
        """Initialise le gestionnaire de licences."""
    
    def is_license_valid(self) -> bool:
        """Vérifie si la licence actuelle est valide."""
    
    def activate_license(self, license_key: str) -> bool:
        """Active une licence avec la clé fournie."""
    
    def get_days_remaining(self) -> int:
        """Retourne le nombre de jours restants sur la licence."""
```

#### Classe `PaymentWindow`

Interface de paiement pour l'achat de licences premium.

```python
class PaymentWindow(ctk.CTkToplevel):
    def __init__(self, parent, license_manager, callback=None):
        """Initialise la fenêtre de paiement."""
    
    def process_payment(self, plan_type: str):
        """Traite le paiement pour le plan spécifié."""
```

### 3. VideoDownloaderApp (`main.py`)

#### Classe `IconManager`

Gestionnaire des icônes de l'application.

```python
class IconManager:
    def __init__(self):
        """Initialise le gestionnaire d'icônes."""
    
    def load_icons(self):
        """Charge toutes les icônes depuis le dossier icons/."""
    
    def get(self, name: str) -> Optional[CTkImage]:
        """Récupère une icône par son nom."""
```

#### Classe `VideoDownloaderApp`

Application principale avec interface graphique.

```python
class VideoDownloaderApp(ctk.CTk):
    def __init__(self):
        """Initialise l'application principale."""
    
    def start_download(self):
        """Démarre le téléchargement de la vidéo."""
    
    def browse_folder(self):
        """Ouvre le sélecteur de dossier."""
    
    def validate_url(self, url: str) -> bool:
        """Valide l'URL fournie."""
    
    def update_progress(self, progress_data: dict):
        """Met à jour la barre de progression."""
    
    def download_complete(self, success: bool, message: str):
        """Callback appelé à la fin du téléchargement."""
```

## Utilitaires

### Logger (`src/utils/logger.py`)

#### Classe `TelVidLogger`

Système de logging centralisé.

```python
class TelVidLogger:
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Obtient un logger avec le nom spécifié."""
    
    @staticmethod
    def log_exception(logger: logging.Logger, message: str, exc_info: bool = True):
        """Log une exception avec le contexte complet."""
    
    @staticmethod
    def log_performance(logger: logging.Logger, operation: str, duration: float):
        """Log les métriques de performance."""
```

#### Fonctions utilitaires

```python
def get_app_logger() -> logging.Logger:
    """Obtient le logger principal de l'application."""

def get_download_logger() -> logging.Logger:
    """Obtient le logger pour les téléchargements."""

def get_license_logger() -> logging.Logger:
    """Obtient le logger pour les licences."""
```

#### Décorateurs

```python
@log_function_call(logger=None)
def ma_fonction():
    """Décorateur pour logger automatiquement les appels de fonction."""

@log_performance(logger=None)
def ma_fonction_lente():
    """Décorateur pour logger les performances."""
```

### ConfigManager (`src/utils/config_manager.py`)

#### Classe `ConfigManager`

Gestionnaire centralisé de configuration.

```python
class ConfigManager:
    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        """Récupère une valeur de configuration."""
    
    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """Récupère une valeur entière."""
    
    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        """Récupère une valeur booléenne."""
    
    def set(self, section: str, key: str, value: Any):
        """Définit une valeur de configuration."""
    
    def get_app_config(self) -> Dict[str, Any]:
        """Récupère la configuration de l'application."""
    
    def get_gui_config(self) -> Dict[str, Any]:
        """Récupère la configuration de l'interface."""
    
    def get_download_config(self) -> Dict[str, Any]:
        """Récupère la configuration de téléchargement."""
```

## Configuration

### Fichiers de configuration

- `config/app_config.ini` : Configuration principale
- `config/logging.conf` : Configuration des logs
- `premium_config.json` : Configuration premium
- `license.json` : Informations de licence

### Sections de configuration

#### [APPLICATION]
- `name` : Nom de l'application
- `version` : Version actuelle
- `debug` : Mode debug (true/false)
- `log_level` : Niveau de log (DEBUG, INFO, WARNING, ERROR)

#### [GUI]
- `theme` : Thème de l'interface (dark/light)
- `window_width` : Largeur de la fenêtre
- `window_height` : Hauteur de la fenêtre

#### [DOWNLOAD]
- `default_output_path` : Dossier de téléchargement par défaut
- `max_retries` : Nombre maximum de tentatives
- `timeout` : Timeout en secondes

#### [PREMIUM]
- `trial_period_days` : Durée de la période d'essai
- `max_free_downloads` : Nombre max de téléchargements gratuits

## Événements et Callbacks

### Callbacks de téléchargement

```python
def progress_callback(progress_data: dict):
    """
    Appelé pendant le téléchargement pour mettre à jour la progression.
    
    Args:
        progress_data (dict): Données de progression de yt-dlp
    """

def completion_callback(success: bool, message: str):
    """
    Appelé à la fin du téléchargement.
    
    Args:
        success (bool): True si le téléchargement a réussi
        message (str): Message de résultat ou d'erreur
    """
```

### Événements de licence

```python
def license_callback(success: bool):
    """
    Appelé après l'activation d'une licence.
    
    Args:
        success (bool): True si l'activation a réussi
    """
```

## Gestion d'erreurs

### Exceptions personnalisées

L'application utilise les exceptions Python standard avec un logging approprié :

- `ValueError` : Pour les paramètres invalides
- `FileNotFoundError` : Pour les fichiers manquants
- `PermissionError` : Pour les problèmes de permissions
- `ConnectionError` : Pour les problèmes réseau

### Logging des erreurs

Toutes les erreurs sont loggées avec le contexte complet :

```python
try:
    # Code pouvant lever une exception
    pass
except Exception as e:
    logger.error(f"Erreur dans l'opération: {str(e)}", exc_info=True)
```

## Tests

### Structure des tests

```
tests/
├── __init__.py
├── conftest.py          # Configuration des tests
├── test_downloader.py   # Tests du downloader
├── test_license_manager.py  # Tests du gestionnaire de licences
└── test_main.py         # Tests de l'interface
```

### Exécution des tests

```bash
# Tous les tests
pytest tests/ -v

# Tests avec couverture
pytest tests/ -v --cov=. --cov-report=html

# Tests spécifiques
pytest tests/test_downloader.py -v
```

## Build et Distribution

### Création de l'exécutable

```bash
python build.py
```

### Structure de build

```
dist/
├── TelVid.exe          # Exécutable principal
└── _internal/          # Dépendances internes
```

## Contribution

### Standards de code

- Suivre PEP 8
- Docstrings pour toutes les fonctions publiques
- Tests unitaires pour les nouvelles fonctionnalités
- Logging approprié pour toutes les opérations

### Workflow de développement

1. Fork du repository
2. Création d'une branche feature
3. Développement avec tests
4. Pull Request avec description détaillée
