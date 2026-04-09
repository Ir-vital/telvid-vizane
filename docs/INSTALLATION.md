# Guide d'installation - TelVid-Vizane

## Installation pour les utilisateurs finaux

### Option 1: Exécutable Windows (Recommandé)

1. **Télécharger la dernière version**
   - Rendez-vous sur [Releases](https://github.com/ir-vizane/telVidVIZANE/releases)
   - Téléchargez `TelVid-v1.0.0-Windows.zip`

2. **Installation**
   ```
   1. Extraire l'archive dans un dossier de votre choix
   2. Lancer TelVid.exe
   3. L'application se configure automatiquement
   ```

3. **Première utilisation**
   - L'application créera automatiquement les dossiers nécessaires
   - Les paramètres par défaut sont optimisés pour la plupart des utilisateurs
   - Un tutoriel de première utilisation s'affichera

### Option 2: Installation depuis les sources

#### Prérequis
- Python 3.8 ou supérieur
- Git (optionnel)
- Windows 10/11 (recommandé)

#### Installation étape par étape

1. **Cloner ou télécharger le projet**
   ```bash
   git clone https://github.com/votre-username/telVidVIZANE.git
   cd telVidVIZANE
   ```

2. **Créer un environnement virtuel**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

4. **Lancer l'application**
   ```bash
   python run.py
   ```

## Installation pour les développeurs

### Configuration de l'environnement de développement

1. **Cloner le repository**
   ```bash
   git clone https://github.com/votre-username/telVidVIZANE.git
   cd telVidVIZANE
   ```

2. **Créer l'environnement virtuel**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Installer les dépendances de développement**
   ```bash
   pip install -e .[dev]
   ```

4. **Configurer les hooks pre-commit**
   ```bash
   pre-commit install
   ```

5. **Vérifier l'installation**
   ```bash
   python -m pytest tests/ -v
   pylint main.py downloader.py license_manager.py
   black --check .
   ```

### Structure de développement

```
telVidVIZANE/
├── src/                    # Code source organisé
│   ├── __init__.py
│   └── utils/             # Utilitaires
│       ├── __init__.py
│       ├── logger.py      # Système de logging
│       ├── config_manager.py  # Gestion de configuration
│       ├── error_handler.py   # Gestion d'erreurs
│       ├── validators.py      # Validation des entrées
│       ├── updater.py         # Mise à jour automatique
│       ├── download_history.py # Historique
│       └── settings_manager.py # Paramètres persistants
├── tests/                 # Tests unitaires
├── docs/                  # Documentation
├── config/               # Fichiers de configuration
├── icons/                # Ressources graphiques
├── logs/                 # Fichiers de logs (créé automatiquement)
├── data/                 # Données utilisateur (créé automatiquement)
└── dist/                 # Builds (créé par PyInstaller)
```

## Configuration post-installation

### Paramètres recommandés

1. **Dossier de téléchargement**
   - Par défaut: `%USERPROFILE%\Downloads`
   - Recommandé: Créer un dossier dédié comme `D:\Videos\TelVid`

2. **Qualité de téléchargement**
   - Version gratuite: 720p maximum
   - Version premium: Jusqu'à 4K

3. **Paramètres réseau**
   - Timeout: 30 secondes (par défaut)
   - Tentatives: 3 (par défaut)
   - Proxy: Configurer si nécessaire

### Dépannage courant

#### L'application ne se lance pas
```bash
# Vérifier Python
python --version

# Réinstaller les dépendances
pip install -r requirements.txt --force-reinstall

# Vérifier les logs
type logs\app.log
```

#### Erreurs de téléchargement
1. Vérifier la connexion internet
2. Tester l'URL dans un navigateur
3. Vérifier les permissions du dossier de destination
4. Consulter `logs\download.log`

#### Problèmes de licence
1. Vérifier le format de la clé: `TELVID-PREMIUM-YYYY-XXXXXXXX`
2. Consulter `logs\license.log`
3. Contacter le support: support@telvid-vizane.com

## Mise à jour

### Mise à jour automatique (Recommandé)
- L'application vérifie automatiquement les mises à jour
- Notification en cas de nouvelle version
- Installation en un clic

### Mise à jour manuelle
1. Sauvegarder vos paramètres (Menu > Paramètres > Exporter)
2. Télécharger la nouvelle version
3. Remplacer l'ancienne installation
4. Restaurer vos paramètres si nécessaire

## Désinstallation

### Exécutable Windows
1. Supprimer le dossier d'installation
2. Supprimer les données utilisateur (optionnel):
   - `%APPDATA%\TelVid-Vizane`
   - Dossier `data\` dans l'installation

### Installation Python
```bash
# Désactiver l'environnement virtuel
deactivate

# Supprimer le dossier du projet
rmdir /s telVidVIZANE
```

## Support

### Ressources d'aide
- **Documentation**: [docs/](docs/)
- **FAQ**: [docs/FAQ.md](docs/FAQ.md)
- **Issues GitHub**: [Issues](https://github.com/votre-username/telVidVIZANE/issues)

### Contact
- **Email**: support@telvid-vizane.com
- **Discord**: [Serveur TelVid](https://discord.gg/telvid)
- **Telegram**: [@TelVidSupport](https://t.me/TelVidSupport)

### Logs utiles pour le support
Lors d'une demande de support, joignez:
- `logs/app.log` (logs généraux)
- `logs/download.log` (problèmes de téléchargement)
- `logs/license.log` (problèmes de licence)
- Votre configuration système (Windows, Python, etc.)

## Contribution

Voir [CONTRIBUTING.md](CONTRIBUTING.md) pour les détails sur la contribution au projet.

---

**TelVid-Vizane** - Installation simple, utilisation intuitive ! 🚀
