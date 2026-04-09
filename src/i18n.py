"""
Système d'internationalisation (i18n) pour TelVid-Vizane
Support pour français et anglais avec possibilité d'extension
"""

import json
import os

class I18nManager:
    def __init__(self, default_language="fr"):
        self.current_language = default_language
        self.translations = {}
        # Chercher locales/ d'abord à la racine du projet, puis dans src/
        base_dir = os.path.dirname(os.path.abspath(__file__))  # src/
        root_dir = os.path.dirname(base_dir)                   # racine projet
        
        # Priorité : racine du projet, puis src/locales (fallback)
        if os.path.exists(os.path.join(root_dir, 'locales')):
            self.locales_dir = os.path.join(root_dir, 'locales')
        else:
            self.locales_dir = os.path.join(base_dir, 'locales')
        
        self._load_translations()
    
    def _load_translations(self):
        """Charge toutes les traductions disponibles depuis les fichiers JSON."""
        if not os.path.exists(self.locales_dir):
            print(f"Error: Locales directory not found at {self.locales_dir}")
            return

        available_languages = [f.split('.')[0] for f in os.listdir(self.locales_dir) if f.endswith('.json')]
        for lang in available_languages:
            try:
                with open(os.path.join(self.locales_dir, f'{lang}.json'), 'r', encoding='utf-8') as f:
                    self.translations[lang] = json.load(f)
            except (IOError, json.JSONDecodeError) as e:
                print(f"Warning: Could not load language file for '{lang}': {e}")
        
        if not self.translations:
            print("Error: No language files found or loaded. The application may not display text correctly.")
    
    def set_language(self, language_code):
        """Change la langue active"""
        if language_code in self.translations:
            self.current_language = language_code
            return True
        return False
    
    def get(self, key, **kwargs):
        """Récupère une traduction avec formatage optionnel"""
        translation = self.translations.get(self.current_language, {}).get(key, key)
        
        # Formatage des paramètres si fournis
        if kwargs:
            try:
                return translation.format(**kwargs)
            except (KeyError, ValueError):
                return translation
        
        return translation
    
    def get_available_languages(self):
        """Retourne la liste des langues disponibles"""
        return list(self.translations.keys())
    
    def get_language_name(self, code):
        """Retourne le nom complet de la langue"""
        names = {
            "fr": "Français",
            "en": "English"
        }
        return names.get(code, code)

# Instance globale du gestionnaire i18n
_i18n_manager = I18nManager()

def t(key, **kwargs):
    """Fonction raccourci pour les traductions"""
    return _i18n_manager.get(key, **kwargs)

def set_language(language_code):
    """Change la langue globale"""
    return _i18n_manager.set_language(language_code)

def get_current_language():
    """Retourne la langue actuelle"""
    return _i18n_manager.current_language

def get_available_languages():
    """Retourne les langues disponibles"""
    return _i18n_manager.get_available_languages()

def get_language_name(code):
    """Retourne le nom de la langue"""
    return _i18n_manager.get_language_name(code)
