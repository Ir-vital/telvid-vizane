# TelVid-Vizane 🎥

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)](CHANGELOG.md)

**TelVid-Vizane** est une application desktop moderne et intuitive pour télécharger des vidéos depuis diverses plateformes en ligne. Développée avec Python et CustomTkinter, elle offre une interface utilisateur élégante avec un système de licences premium.

![TelVid-Vizane Interface](docs/images/screenshot.png)

## ✨ Fonctionnalités

### Version Gratuite
- ✅ Téléchargement de vidéos depuis YouTube, Vimeo, et autres plateformes
- ✅ Interface utilisateur moderne avec thème sombre
- ✅ Sélection du dossier de destination
- ✅ Indicateur de progression en temps réel
- ✅ Support des formats vidéo et audio

### Version Premium
- 🚀 Téléchargements illimités
- 🚀 Téléchargements simultanés multiples
- 🚀 Qualité HD/4K
- 🚀 Historique des téléchargements
- 🚀 Support prioritaire

## 🚀 Installation

### Prérequis
- Python 3.8 ou supérieur
- Windows 10/11 (recommandé)

### Installation depuis les sources

1. **Cloner le repository**
```bash
git clone https://github.com/votre-username/telVidVIZANE.git
cd telVidVIZANE
```

2. **Créer un environnement virtuel**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Lancer l'application**
```bash
python run.py
```

### Installation via l'exécutable

1. Téléchargez la dernière version depuis [Releases](https://github.com/votre-username/telVidVIZANE/releases)
2. Exécutez `TelVid.exe`

## 🛠️ Développement

### Structure du projet
```
telVidVIZANE/
├── src/                    # Code source principal
│   ├── core/              # Modules principaux
│   ├── gui/               # Interface utilisateur
│   ├── utils/             # Utilitaires
│   └── config/            # Configuration
├── tests/                 # Tests unitaires
├── docs/                  # Documentation
├── icons/                 # Ressources graphiques
├── logs/                  # Fichiers de logs
├── dist/                  # Builds de distribution
└── requirements.txt       # Dépendances
```

### Lancer les tests
```bash
python -m pytest tests/ -v
```

### Construire l'exécutable
```bash
pyinstaller TelVid-Vizane.spec --clean
```

### Linting et formatage
```bash
# Linting
pylint src/

# Formatage
black src/
```

## 📖 Utilisation

1. **Lancer l'application**
2. **Coller l'URL** de la vidéo dans le champ prévu
3. **Sélectionner le dossier** de destination
4. **Choisir la qualité** (Gratuit: SD, Premium: HD/4K)
5. **Cliquer sur Télécharger**

### Raccourcis clavier
- `Ctrl+V` : Coller l'URL
- `Ctrl+O` : Ouvrir le sélecteur de dossier
- `Enter` : Lancer le téléchargement
- `Esc` : Annuler le téléchargement

## 🔧 Configuration

### Fichiers de configuration
- `config/app_config.ini` : Configuration générale
- `config/logging.conf` : Configuration des logs
- `premium_config.json` : Configuration premium
- `license.json` : Informations de licence

### Variables d'environnement
```bash
TELVID_LOG_LEVEL=INFO
TELVID_DATA_DIR=./data
TELVID_TEMP_DIR=./temp
```

## 🐛 Dépannage

### Problèmes courants

**Erreur de téléchargement**
- Vérifiez votre connexion internet
- Assurez-vous que l'URL est valide
- Vérifiez les permissions du dossier de destination

**Interface ne se lance pas**
- Vérifiez que Python 3.8+ est installé
- Réinstallez les dépendances : `pip install -r requirements.txt --force-reinstall`

**Problèmes de licence**
- Contactez le support : vitalzagabe156@gmail.com
- Vérifiez la date d'expiration dans l'interface

### Logs
Les logs sont disponibles dans le dossier `logs/` :
- `app.log` : Logs généraux
- `download.log` : Logs de téléchargement
- `license.log` : Logs du système de licence

## 🤝 Contribution

Les contributions sont les bienvenues ! Veuillez suivre ces étapes :

1. Fork le projet
2. Créez une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commitez vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

### Standards de code
- Suivez PEP 8
- Ajoutez des docstrings à toutes les fonctions
- Écrivez des tests pour les nouvelles fonctionnalités
- Maintenez une couverture de tests > 80%

## 📄 Licence

Ce projet est sous licence propriétaire. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 👥 Équipe

- **Développeur Principal** : vital zagabe(mailto:vitalzagabe156@gmail.com)
- **Support** : vitalzagabe156@gmail.com

## 🔗 Liens utiles

- [Documentation complète](docs/)
- [Changelog](CHANGELOG.md)
- [Issues](https://github.com/votre-username/telVidVIZANE/issues)
- [Discussions](https://github.com/votre-username/telVidVIZANE/discussions)

## ⭐ Remerciements

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) pour le moteur de téléchargement
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) pour l'interface moderne
- [Pillow](https://python-pillow.org/) pour le traitement d'images

---

**TelVid-Vizane** - Téléchargez vos vidéos préférées en toute simplicité ! 🎬
