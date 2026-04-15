import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import sys
import shutil
import customtkinter as ctk
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import json
import logging
from datetime import datetime
from src.downloader import VideoDownloader
from src.license_manager import LicenseManager
from src.auto_updater import check_for_updates_background, AutoUpdater, show_update_dialog
from src.gui.payment_window import PaymentWindow
from src.i18n import t, set_language, get_current_language, get_available_languages, get_language_name
from src.logger import get_logger, log_app_event, log_download_start, log_download_success, log_download_error, log_settings_change, log_error


class Tooltip:
    """Tooltip simple qui s'affiche au survol d'un widget."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tip_window:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)  # Pas de bordure de fenêtre
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw, text=self.text, justify="left",
            background="#1e293b", foreground="#f8fafc",
            relief="flat", borderwidth=1,
            font=("Segoe UI", 10), padx=8, pady=5,
            wraplength=260
        )
        label.pack()

    def hide(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

def resource_path(relative_path):
    """
    Obtient le chemin absolu vers une ressource, fonctionne pour le dev et pour PyInstaller.
    """
    try:
        # PyInstaller crée un dossier temporaire et y stocke le chemin dans _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Si l'application n'est pas "gelée", le chemin de base est le dossier du script
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# Système de paramètres simple mais fonctionnel
class SettingsManager:
    def __init__(self):
        from src.license_manager import get_app_data_dir
        self.settings_file = os.path.join(get_app_data_dir(), "app_settings.json")
        self.default_settings = {
            "theme": "dark",
            "language": "fr",
            "auto_update": True,
            "download_path": os.path.expanduser("~/Downloads"),
            "max_downloads": 3,
            "quality_preference": "sd",
            "notifications": True,
            "history_enabled": True,
            "auto_retry": True,
            "window_geometry": "1100x780"
        }
        self.settings = self.load_settings()
    
    def load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                # Fusionner avec les paramètres par défaut
                settings = self.default_settings.copy()
                settings.update(loaded)
                return settings
        except Exception as e:
            print(f"Erreur chargement paramètres: {e}")
        return self.default_settings.copy()
    
    def save_settings(self):
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erreur sauvegarde paramètres: {e}")
            return False
    
    def get(self, key, default=None):
        return self.settings.get(key, default)
    
    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()

# Historique des téléchargements simple mais fonctionnel
class DownloadHistory:
    def __init__(self):
        from src.license_manager import get_app_data_dir
        self.history_file = os.path.join(get_app_data_dir(), "download_history.json")
        self.history = self.load_history()
    
    def load_history(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Erreur chargement historique: {e}")
        return []
    
    def save_history(self):
        try:
            # Garder seulement les 100 derniers
            self.history = self.history[-100:]
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur sauvegarde historique: {e}")
    
    def add_download(self, url, title, success, file_path=None, error=None):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "title": title,
            "success": success,
            "file_path": file_path,
            "error": error
        }
        self.history.append(entry)
        self.save_history()
    
    def get_recent(self, count=10):
        return self.history[-count:] if self.history else []
    
    def clear_history(self):
        self.history = []
        self.save_history()

# Fenêtre de paramètres fonctionnelle
class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent, settings_manager):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.title(t("settings_title"))
        self.geometry("600x500")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.create_widgets()
        self.load_current_settings()
    
    def create_widgets(self):
        # Notebook pour les onglets
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Onglet Général
        general_frame = ctk.CTkFrame(notebook)
        notebook.add(general_frame, text=t("general"))
        
        # Thème
        ctk.CTkLabel(general_frame, text=t("theme"), font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10,5))
        self.theme_var = ctk.StringVar(value=self.settings_manager.get("theme", "dark"))
        theme_frame = ctk.CTkFrame(general_frame)
        theme_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkRadioButton(theme_frame, text=t("dark"), variable=self.theme_var, value="dark").pack(side="left", padx=10, pady=5)
        ctk.CTkRadioButton(theme_frame, text=t("light"), variable=self.theme_var, value="light").pack(side="left", padx=10, pady=5)
        
        # Langue
        ctk.CTkLabel(general_frame, text=t("language"), font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10,5))
        self.language_var = ctk.StringVar(value=self.settings_manager.get("language", "fr"))
        # Créer une liste avec les noms complets des langues
        lang_options = [f"{code} - {get_language_name(code)}" for code in get_available_languages()]
        current_lang = self.settings_manager.get("language", "fr")
        current_display = f"{current_lang} - {get_language_name(current_lang)}"
        self.language_display_var = ctk.StringVar(value=current_display)
        lang_combo = ctk.CTkComboBox(general_frame, values=lang_options, variable=self.language_display_var, command=self.on_language_change)
        lang_combo.pack(anchor="w", padx=10, pady=5)
        
        # Notifications
        self.notifications_var = ctk.BooleanVar(value=self.settings_manager.get("notifications", True))
        ctk.CTkCheckBox(general_frame, text="Activer les notifications", variable=self.notifications_var).pack(anchor="w", padx=10, pady=5)
        
        # Mise à jour auto
        self.auto_update_var = ctk.BooleanVar(value=self.settings_manager.get("auto_update", True))
        ctk.CTkCheckBox(general_frame, text="Vérification automatique des mises à jour", variable=self.auto_update_var).pack(anchor="w", padx=10, pady=5)
        
        # Bouton pour vérifier manuellement les mises à jour
        update_button = ctk.CTkButton(general_frame, text="Vérifier les mises à jour maintenant", command=self.check_updates_manually)
        update_button.pack(anchor="w", padx=10, pady=5)
        
        # Onglet Téléchargements
        download_frame = ctk.CTkFrame(notebook)
        notebook.add(download_frame, text="Téléchargements")
        
        # Dossier par défaut
        ctk.CTkLabel(download_frame, text="Dossier de téléchargement par défaut:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10,5))
        path_frame = ctk.CTkFrame(download_frame)
        path_frame.pack(fill="x", padx=10, pady=5)
        self.download_path_var = ctk.StringVar(value=self.settings_manager.get("download_path", ""))
        path_entry = ctk.CTkEntry(path_frame, textvariable=self.download_path_var, width=400)
        path_entry.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        ctk.CTkButton(path_frame, text="Parcourir", command=self.browse_download_path, width=80).pack(side="right", padx=5, pady=5)
        
        # Téléchargements simultanés
        ctk.CTkLabel(download_frame, text="Téléchargements simultanés max:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10,5))
        self.max_downloads_var = ctk.IntVar(value=self.settings_manager.get("max_downloads", 3))
        max_downloads_slider = ctk.CTkSlider(download_frame, from_=1, to=5, variable=self.max_downloads_var, number_of_steps=4)
        max_downloads_slider.pack(anchor="w", padx=10, pady=5, fill="x")
        self.max_downloads_label = ctk.CTkLabel(download_frame, text=f"Valeur: {self.max_downloads_var.get()}")
        self.max_downloads_label.pack(anchor="w", padx=10)
        max_downloads_slider.configure(command=self.update_max_downloads_label)
        
        # Qualité préférée
        ctk.CTkLabel(download_frame, text="Qualité préférée:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10,5))
        self.quality_var = ctk.StringVar(value=self.settings_manager.get("quality_preference", "sd"))
        quality_frame = ctk.CTkFrame(download_frame)
        quality_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkRadioButton(quality_frame, text="SD (480p)", variable=self.quality_var, value="sd").pack(side="left", padx=10, pady=5)
        ctk.CTkRadioButton(quality_frame, text="HD (720p+)", variable=self.quality_var, value="hd").pack(side="left", padx=10, pady=5)
        
        # Retry automatique
        self.auto_retry_var = ctk.BooleanVar(value=self.settings_manager.get("auto_retry", True))
        ctk.CTkCheckBox(download_frame, text="Réessayer automatiquement en cas d'échec", variable=self.auto_retry_var).pack(anchor="w", padx=10, pady=5)
        
        # Onglet Historique
        history_frame = ctk.CTkFrame(notebook)
        notebook.add(history_frame, text="Historique")
        
        # Activer l'historique
        self.history_enabled_var = ctk.BooleanVar(value=self.settings_manager.get("history_enabled", True))
        ctk.CTkCheckBox(history_frame, text="Conserver l'historique des téléchargements", variable=self.history_enabled_var).pack(anchor="w", padx=10, pady=10)
        
        # Boutons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(button_frame, text="Annuler", command=self.destroy).pack(side="right", padx=5)
        ctk.CTkButton(button_frame, text="Appliquer", command=self.apply_settings).pack(side="right", padx=5)
        ctk.CTkButton(button_frame, text="OK", command=self.ok_clicked).pack(side="right", padx=5)
        ctk.CTkButton(button_frame, text="Réinitialiser", command=self.reset_settings).pack(side="left", padx=5)
    
    def update_max_downloads_label(self, value):
        self.max_downloads_label.configure(text=f"Valeur: {int(value)}")
    
    def browse_download_path(self):
        path = filedialog.askdirectory(initialdir=self.download_path_var.get())
        if path:
            self.download_path_var.set(path)
    
    def load_current_settings(self):
        # Les variables sont déjà initialisées avec les valeurs actuelles
        pass
    
    def apply_settings(self):
        # Sauvegarder tous les paramètres
        self.settings_manager.set("theme", self.theme_var.get())
        self.settings_manager.set("language", self.language_var.get())
        self.settings_manager.set("notifications", self.notifications_var.get())
        self.settings_manager.set("auto_update", self.auto_update_var.get())
        self.settings_manager.set("download_path", self.download_path_var.get())
        self.settings_manager.set("max_downloads", int(self.max_downloads_var.get()))
        self.settings_manager.set("quality_preference", self.quality_var.get())
        self.settings_manager.set("auto_retry", self.auto_retry_var.get())
        self.settings_manager.set("history_enabled", self.history_enabled_var.get())

        # Appliquer le thème immédiatement
        new_theme = self.theme_var.get()
        ctk.set_appearance_mode(new_theme)

        messagebox.showinfo("Paramètres", "Paramètres sauvegardés avec succès!\nCertains éléments nécessitent un redémarrage pour être mis à jour.")
    
    def ok_clicked(self):
        self.apply_settings()
        self.destroy()
    
    def reset_settings(self):
        if messagebox.askyesno("Réinitialiser", "Voulez-vous vraiment réinitialiser tous les paramètres?"):
            # Réinitialiser aux valeurs par défaut
            self.theme_var.set("dark")
            self.language_var.set("fr")
            self.notifications_var.set(True)
            self.auto_update_var.set(True)
            self.download_path_var.set(os.path.expanduser("~/Downloads"))
            self.max_downloads_var.set(3)
            self.quality_var.set("sd")
            self.auto_retry_var.set(True)
            self.history_enabled_var.set(True)
    
    def check_updates_manually(self):
        """Vérifie manuellement les mises à jour"""
        try:
            # Afficher un message de vérification
            checking_dialog = ctk.CTkToplevel(self)
            checking_dialog.title("Vérification...")
            checking_dialog.geometry("300x100")
            checking_dialog.transient(self)
            checking_dialog.grab_set()
            
            label = ctk.CTkLabel(checking_dialog, text="Vérification des mises à jour...")
            label.pack(expand=True)
            
            def check_in_thread():
                updater = AutoUpdater()
                update_info = updater.check_for_updates(silent=False)
                
                # Fermer le dialogue de vérification
                checking_dialog.after(0, checking_dialog.destroy)
                
                if update_info.get("available"):
                    # Afficher la boîte de dialogue de mise à jour
                    self.after(100, lambda: show_update_dialog(self.master, update_info))
                else:
                    # Aucune mise à jour disponible
                    self.after(100, lambda: messagebox.showinfo(
                        "Mises à jour", 
                        "Vous utilisez déjà la dernière version de TelVid-Vizane!"
                    ))
            
            # Lancer la vérification dans un thread séparé
            import threading
            thread = threading.Thread(target=check_in_thread, daemon=True)
            thread.start()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la vérification: {e}")
    
    def on_language_change(self, selected_value):
        """Gestionnaire pour le changement de langue"""
        try:
            # Extraire le code de langue depuis la sélection "fr - Français"
            language_code = selected_value.split(" - ")[0]
            self.language_var.set(language_code)
            
            # Appliquer immédiatement la nouvelle langue
            set_language(language_code)
            
            # Informer l'utilisateur qu'un redémarrage peut être nécessaire
            messagebox.showinfo(
                t("language"), 
                "La langue a été changée. Certains éléments peuvent nécessiter un redémarrage de l'application pour être mis à jour."
            )
        except Exception as e:
            print(f"Erreur changement de langue: {e}")

# Fenêtre d'historique fonctionnelle
class HistoryWindow(ctk.CTkToplevel):
    def __init__(self, parent, history_manager):
        super().__init__(parent)
        self.history_manager = history_manager
        self.title("Historique des téléchargements")
        self.geometry("800x600")

        # Cacher la fenêtre pour éviter le flash blanc
        self.withdraw()

        self.transient(parent)
        
        self.create_widgets()
        self.refresh_history()

        # Forcer la mise à jour de l'interface
        self.update_idletasks()

        # Afficher la fenêtre et la rendre modale
        self.deiconify()
        self.grab_set()
    
    def create_widgets(self):
        # Barre d'outils
        toolbar = ctk.CTkFrame(self)
        toolbar.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(toolbar, text="Actualiser", command=self.refresh_history).pack(side="left", padx=5)
        ctk.CTkButton(toolbar, text="Effacer tout", command=self.clear_history).pack(side="left", padx=5)
        ctk.CTkButton(toolbar, text="Exporter", command=self.export_history).pack(side="left", padx=5)
        
        # Liste de l'historique
        self.history_text = ctk.CTkTextbox(self, height=400)
        self.history_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Bouton fermer
        ctk.CTkButton(self, text="Fermer", command=self.destroy).pack(pady=10)
    
    def refresh_history(self):
        self.history_text.delete("1.0", tk.END)
        history = self.history_manager.get_recent(50)  # 50 derniers
        
        if not history:
            self.history_text.insert(tk.END, "Aucun téléchargement dans l'historique.\n")
            return
        
        for entry in reversed(history):
            timestamp = datetime.fromisoformat(entry["timestamp"]).strftime("%d/%m/%Y %H:%M:%S")
            status = "✅" if entry["success"] else "❌"
            title = entry["title"] or "Titre inconnu"
            
            line = f"[{timestamp}] {status} {title}\n"
            if not entry["success"] and entry.get("error"):
                line += f"    Erreur: {entry['error']}\n"
            elif entry["success"] and entry.get("file_path"):
                line += f"    Fichier: {entry['file_path']}\n"
            line += "\n"
            
            self.history_text.insert(tk.END, line)
    
    def clear_history(self):
        if messagebox.askyesno("Effacer l'historique", "Voulez-vous vraiment effacer tout l'historique?"):
            self.history_manager.clear_history()
            self.refresh_history()
            messagebox.showinfo("Historique", "Historique effacé avec succès!")
    
    def export_history(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.history_manager.history, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Export", f"Historique exporté vers {file_path}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'export: {e}")

class IconManager:
    def __init__(self):
        self.icons = {}
        self.icon_size = (28, 28)
        # Le dictionnaire des fichiers d'icônes est maintenant une carte de configuration.
        # Les icônes ne sont plus chargées au démarrage.
        self.icon_files = {
            'logo': 'logo-telvid.png',
            'download': 'icone-download.png',
            'video_hd': 'icon-video-hd.png',
            'video_sd': 'icon-video-sd.png',
            'audio': 'icon-audio.png',
        }

    def get(self, name):
        """
        Récupère une icône. La charge et la met en cache si c'est le premier appel.
        C'est le principe du "Lazy Loading".
        """
        # Si l'icône est déjà chargée, la retourner directement.
        if name in self.icons:
            return self.icons.get(name)

        # Sinon, charger l'icône maintenant.
        file = self.icon_files.get(name)
        if not file:
            return None # Nom d'icône inconnu

        path = resource_path(os.path.join('icons', file))
        if os.path.exists(path):
            # Charger, créer l'objet CTkImage et le mettre en cache.
            self.icons[name] = ctk.CTkImage(Image.open(path), size=self.icon_size)
        else:
            # Mettre None en cache pour ne pas réessayer de charger un fichier manquant.
            self.icons[name] = None
        
        return self.icons.get(name)

# La classe PremiumManager est remplacée par LicenseManager importé depuis license_manager.py

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class VideoDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Initialisation des gestionnaires AVANT tout
        self.settings_manager = SettingsManager()
        self.history_manager = DownloadHistory()
        self.downloader = VideoDownloader()
        self.license_manager = LicenseManager()

        # Initialisation du convertisseur local
        try:
            from src.converter import LocalConverter
            self.converter = LocalConverter()
        except ImportError as e:
            self.converter = None
            print(f"AVERTISSEMENT: Le module de conversion n'a pas pu être chargé. {e}")
        
        # --- Gestion de la concurrence des téléchargements ---
        max_concurrent = self.settings_manager.get("max_downloads", 3)
        self.download_executor = ThreadPoolExecutor(max_workers=max_concurrent)
        
        # Configuration de la fenêtre avec paramètres sauvegardés
        self.title(t("app_title"))
        saved_geometry = self.settings_manager.get("window_geometry", "1100x780")
        self.geometry(saved_geometry)
        self.resizable(True, True)
        self.minsize(900, 650)  # Taille minimale pour que tout soit visible

        # Centrer la fenêtre à l'écran au premier lancement
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        
        # Icône de la fenêtre et de la barre des tâches
        try:
            icon_path = resource_path(os.path.join("icons", "logo-telvid.ico"))
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            log_error(f"Impossible de charger l'icône: {e}")
        
        # Appliquer le thème sauvegardé
        theme = self.settings_manager.get("theme", "dark")
        ctk.set_appearance_mode(theme)
        
        # Appliquer la langue sauvegardée
        saved_language = self.settings_manager.get("language", "fr")
        set_language(saved_language)
        
        # Variables d'interface
        self.url_var = tk.StringVar()
        self.conversion_input_file = tk.StringVar()
        default_path = self.settings_manager.get("download_path", os.path.expanduser("~/Downloads"))
        self.output_path_var = tk.StringVar(value=default_path)
        self.output_path = default_path  # Variable pour compatibilité
        self.format_var = ctk.StringVar(value="video_sd")  # Variable pour le format
        
        # Gestionnaire d'icônes
        self.icon_manager = IconManager()
        
        # Gestion des tâches de téléchargement
        self.job_id_counter = 0
        self.download_jobs = {} # Dictionnaire pour stocker les widgets UI de chaque tâche
        
        # Interface utilisateur
        self.create_widgets()
        self.update_download_button_state()
        
        # Vérification de la licence au démarrage
        self.check_license_status()
        
        # Sauvegarder la géométrie à la fermeture
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Les boutons seront ajoutés dans create_widgets()
        
        # Vérifier les mises à jour en arrière-plan si activé
        if self.settings_manager.get("auto_update", True):
            self.after(3000, lambda: check_for_updates_background(self, self.settings_manager))
        
        # Logger le démarrage de l'application
        log_app_event(f"Application démarrée - Langue: {get_current_language()}, Thème: {theme}")
        log_app_event(f"Mode: {'Premium' if self.license_manager.is_premium else 'Gratuit'}")

        # Animation de démarrage — fondu d'entrée
        from src.gui.animations import fade_in
        fade_in(self, duration=400)
        
    def create_widgets(self):
        # Conteneur principal pour les deux panneaux
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Panneau de Gauche : Téléchargeur ---
        downloader_frame = ctk.CTkFrame(content_frame)
        downloader_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self._create_downloader_widgets(downloader_frame)

        # --- Panneau de Droite : onglets Convertisseur + Vidéos téléchargées ---
        right_panel = ctk.CTkFrame(content_frame, width=340)
        right_panel.pack(side="right", fill="y")
        right_panel.pack_propagate(False)

        # Onglets
        right_tabs = ctk.CTkTabview(right_panel)
        right_tabs.pack(fill="both", expand=True, padx=4, pady=4)

        # Onglet Convertisseur
        conv_tab = right_tabs.add("🔄 Convertir")
        if self.converter:
            self._create_converter_widgets(conv_tab)
        else:
            ctk.CTkLabel(conv_tab, text="Convertisseur non disponible.\nInstallez moviepy.",
                         text_color="#64748b", font=("Segoe UI", 11, "italic")).pack(pady=30)

        # Onglet Vidéos téléchargées
        from src.gui.downloads_panel import DownloadsPanel
        videos_tab = right_tabs.add("🎬 Vidéos")
        self.downloads_panel = DownloadsPanel(videos_tab, fg_color="transparent")
        self.downloads_panel.pack(fill="both", expand=True)

        # Recharger les vidéos de l'historique au démarrage
        self.after(1000, self._restore_downloads_panel)

    def _create_downloader_widgets(self, parent_frame):
        """Crée tous les widgets pour la partie téléchargement."""
        # Logo
        logo_img = self.icon_manager.get('logo')
        if logo_img:
            logo_label = ctk.CTkLabel(parent_frame, image=logo_img, text="")
            logo_label.pack(pady=(10, 5))
        # Titre
        title_label = ctk.CTkLabel(parent_frame, text="TelVid-Vizane", font=("Helvetica", 28, "bold"))
        title_label.pack(pady=(0, 10))
        # Bannière explicative
        # Bannière explicative — couleur adaptative selon le thème
        mode = ctk.get_appearance_mode()
        banner_bg = "#1e293b" if mode == "Dark" else "#e2e8f0"
        self.banner = ctk.CTkFrame(parent_frame, fg_color=banner_bg)
        self.banner.pack(pady=10, padx=10, fill="x")
        banner_text = (
            "\nPLAN GRATUIT : 1 téléchargement à la fois, Vidéo SD (480p), Audio MP3 128kbps.\n"
            "PLAN PREMIUM : Téléchargements simultanés illimités, Vidéo HD (1080p+), Audio MP3 320kbps, Support prioritaire.\n"
        )
        self.banner_label = ctk.CTkLabel(self.banner, text=banner_text, font=("Helvetica", 14), text_color="#fff")
        self.banner_label.pack(side="left", padx=10, pady=5)
        
        # Ajouter le bouton de mise à niveau si nécessaire
        self.update_premium_banner()
        # URL
        url_frame = ctk.CTkFrame(parent_frame)
        url_frame.pack(pady=10, fill="x")
        url_label = ctk.CTkLabel(url_frame, text="URL de la vidéo :", font=("Helvetica", 13))
        url_label.pack(side="left", padx=10)
        url_entry = ctk.CTkEntry(url_frame, textvariable=self.url_var, width=400,
                                 placeholder_text="Collez l'URL ici (YouTube, TikTok, Instagram...)")
        url_entry.pack(side="left", padx=10, fill="x", expand=True)
        # Formats avec icônes
        format_frame = ctk.CTkFrame(parent_frame)
        format_frame.pack(pady=10, fill="x")
        format_label = ctk.CTkLabel(format_frame, text="Format :", font=("Helvetica", 13))
        format_label.pack(side="left", padx=10)
        # HD
        hd_icon = self.icon_manager.get('video_hd')
        if hd_icon:
            ctk.CTkLabel(format_frame, image=hd_icon, text="").pack(side="left")
        hd_radio = ctk.CTkRadioButton(
            format_frame, text="Vidéo HD", variable=self.format_var, value="video_hd",
            state="normal" if self.license_manager.is_premium else "disabled"
        )
        hd_radio.pack(side="left", padx=10)
        # Tooltip HD
        if self.license_manager.is_premium:
            Tooltip(hd_radio, "Vidéo HD (720p et plus)\nDisponible avec votre abonnement Premium.")
        else:
            Tooltip(hd_radio, "🔒 Format Premium requis\nPassez au plan Premium pour débloquer la qualité HD (720p+), l'audio 320kbps et les téléchargements illimités.")
        # SD
        sd_icon = self.icon_manager.get('video_sd')
        if sd_icon:
            ctk.CTkLabel(format_frame, image=sd_icon, text="").pack(side="left")
        sd_radio = ctk.CTkRadioButton(
            format_frame, text="Vidéo SD", variable=self.format_var, value="video_sd"
        )
        sd_radio.pack(side="left", padx=10)
        Tooltip(sd_radio, "Vidéo SD (jusqu'à 480p)\nDisponible gratuitement.")
        # Audio
        audio_icon = self.icon_manager.get('audio')
        if audio_icon:
            ctk.CTkLabel(format_frame, image=audio_icon, text="").pack(side="left")
        audio_radio = ctk.CTkRadioButton(
            format_frame, text="Audio (MP3)", variable=self.format_var, value="audio"
        )
        audio_radio.pack(side="left", padx=10)
        Tooltip(audio_radio, "Audio MP3\nGratuit : 128kbps\nPremium : 320kbps haute qualité.")
        # Explication audio
        audio_hint = ctk.CTkLabel(format_frame, text="Astuce : Choisissez 'Audio (MP3)' pour extraire la piste sonore.", font=("Helvetica", 11, "italic"), text_color="#a3e635")
        audio_hint.pack(side="left", padx=20)
        if not self.license_manager.is_premium:
            self.format_var.set("video_sd")
        # Dossier de destination
        path_frame = ctk.CTkFrame(parent_frame)
        path_frame.pack(pady=10, fill="x")
        path_label = ctk.CTkLabel(path_frame, text=f"Dossier de destination : {self.output_path}", font=("Helvetica", 12))
        path_label.pack(side="left", padx=10)
        path_button = ctk.CTkButton(path_frame, text="Changer", command=self.choose_output_path)
        path_button.pack(side="right", padx=10)
        # Bouton de téléchargement
        self.main_download_button = ctk.CTkButton(
            parent_frame, text="⬇  Télécharger",
            command=self.start_download,
            height=45, font=("Helvetica", 16, "bold"),
            fg_color="#2563eb", hover_color="#1d4ed8"
        )
        self.main_download_button.pack(pady=(20, 5))

        # Label d'aide contextuel sous le bouton
        self.download_hint_label = ctk.CTkLabel(
            parent_frame, text="", font=("Helvetica", 11, "italic"), text_color="#94a3b8"
        )
        self.download_hint_label.pack(pady=(0, 10))

        self.update_download_button_state()

        # Plateformes supportées
        platforms_label = ctk.CTkLabel(parent_frame, text="Plateformes supportées : YouTube, Facebook, Instagram, Twitter, TikTok et plus encore", font=("Helvetica", 11, "italic"), text_color="#38bdf8")
        platforms_label.pack(pady=5)

        # Boutons pour paramètres, historique et à propos
        buttons_frame = ctk.CTkFrame(parent_frame)
        buttons_frame.pack(pady=5, fill="x")

        settings_button = ctk.CTkButton(
            buttons_frame,
            text="⚙ " + t("settings"),
            command=self.open_settings_window,
            width=150, fg_color="#374151", hover_color="#4b5563"
        )
        settings_button.pack(side="left", padx=10)

        history_button = ctk.CTkButton(
            buttons_frame,
            text="🕐 " + t("history"),
            command=self.open_history_window,
            width=150, fg_color="#374151", hover_color="#4b5563"
        )
        history_button.pack(side="left", padx=10)

        about_button = ctk.CTkButton(
            buttons_frame,
            text="ℹ  À propos / Licence",
            command=self.open_about_window,
            width=170, fg_color="#374151", hover_color="#4b5563"
        )
        about_button.pack(side="left", padx=10)

        # File d'attente des téléchargements — en bas, expand pour remplir l'espace restant
        self.downloads_list_frame = ctk.CTkScrollableFrame(parent_frame, label_text="File d'attente")
        self.downloads_list_frame.pack(pady=10, fill="both", expand=True)

        # Label initial si la liste est vide
        self.empty_list_label = ctk.CTkLabel(self.downloads_list_frame, text="Aucun téléchargement en cours.", text_color="gray")
        self.empty_list_label.pack(pady=20)

    def _create_converter_widgets(self, parent_frame):
        """Crée les widgets pour le panneau de conversion local."""
        title = ctk.CTkLabel(parent_frame, text="Convertisseur Local", font=("Helvetica", 18, "bold"))
        title.pack(pady=20, padx=10)

        desc = ctk.CTkLabel(parent_frame, text="Convertissez une vidéo de votre ordinateur en fichier audio MP3.", wraplength=260, font=("Helvetica", 12))
        desc.pack(pady=10, padx=10)

        select_button = ctk.CTkButton(parent_frame, text="Sélectionner une vidéo", command=self.select_video_for_conversion)
        select_button.pack(pady=20, padx=10, fill="x")

        self.conversion_file_label = ctk.CTkLabel(parent_frame, text="Aucun fichier sélectionné", wraplength=260, font=("Helvetica", 11, "italic"), text_color="gray")
        self.conversion_file_label.pack(pady=5, padx=10)

        self.convert_button = ctk.CTkButton(parent_frame, text="Convertir en MP3", command=self.start_conversion, state="disabled")
        self.convert_button.pack(pady=20, padx=10, fill="x")

        self.conversion_progress = ctk.CTkProgressBar(parent_frame)
        self.conversion_progress.pack(pady=10, padx=10, fill="x")
        self.conversion_progress.set(0)
        self.conversion_progress.pack_forget()  # Cacher initialement

        self.conversion_status_label = ctk.CTkLabel(parent_frame, text="", wraplength=260)
        self.conversion_status_label.pack(pady=10, padx=10)

    def _create_job_widget(self, job_id, url):
        """Crée les widgets UI pour une nouvelle tâche de téléchargement."""
        if hasattr(self, 'empty_list_label') and self.empty_list_label:
            self.empty_list_label.destroy()
            self.empty_list_label = None

        job_frame = ctk.CTkFrame(self.downloads_list_frame)
        job_frame.pack(fill="x", padx=5, pady=5)

        # Header avec URL
        header_frame = ctk.CTkFrame(job_frame)
        header_frame.pack(fill="x", padx=5, pady=5)

        title_label = ctk.CTkLabel(
            header_frame,
            text=f"En attente: {url[:45]}...",
            anchor="w"
        )
        title_label.pack(side="left", fill="x", expand=True, padx=5)

        # Barre de progression
        progress_bar = ctk.CTkProgressBar(job_frame)
        progress_bar.pack(fill="x", padx=10, pady=5)
        progress_bar.set(0)

        # Statut
        status_label = ctk.CTkLabel(
            job_frame, text="En attente...",
            anchor="w", font=("Segoe UI", 11), text_color="gray"
        )
        status_label.pack(fill="x", padx=10, pady=(0, 4))

        # Boutons de contrôle
        ctrl_frame = ctk.CTkFrame(job_frame, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=10, pady=(0, 6))

        btn_pause = ctk.CTkButton(
            ctrl_frame, text="⏸ Pause",
            width=80, height=26, fg_color="#374151", hover_color="#4b5563",
            font=("Segoe UI", 11), corner_radius=6,
            command=lambda: self._pause_download(job_id)
        )
        btn_pause.pack(side="left", padx=(0, 4))

        btn_resume = ctk.CTkButton(
            ctrl_frame, text="▶ Continuer",
            width=90, height=26, fg_color="#374151", hover_color="#4b5563",
            font=("Segoe UI", 11), corner_radius=6,
            state="disabled",
            command=lambda: self._resume_download(job_id)
        )
        btn_resume.pack(side="left", padx=(0, 4))

        btn_cancel = ctk.CTkButton(
            ctrl_frame, text="✕ Annuler",
            width=80, height=26, fg_color="#7f1d1d", hover_color="#991b1b",
            font=("Segoe UI", 11), corner_radius=6,
            command=lambda: self._cancel_download(job_id)
        )
        btn_cancel.pack(side="left")

        # Events pour pause et annulation
        import threading
        pause_event  = threading.Event()
        cancel_event = threading.Event()
        pause_event.set()  # Démarrer en mode "non pausé"

        self.download_jobs[job_id] = {
            "frame":        job_frame,
            "header_frame": header_frame,
            "title_label":  title_label,
            "progress_bar": progress_bar,
            "status_label": status_label,
            "btn_pause":    btn_pause,
            "btn_resume":   btn_resume,
            "btn_cancel":   btn_cancel,
            "url":          url,
            "cancelled":    False,
            "completed":    False,
            "paused":       False,
            "pause_event":  pause_event,
            "cancel_event": cancel_event,
        }

        # Barre indéterminée pendant l'extraction des infos
        from src.gui.animations import IndeterminateProgress
        indet = IndeterminateProgress(progress_bar, speed=25)
        indet.start()
        self.download_jobs[job_id]["indet_progress"] = indet

    def _pause_download(self, job_id):
        """Met en pause un téléchargement en cours."""
        if job_id not in self.download_jobs:
            return
        widgets = self.download_jobs[job_id]
        if widgets.get("paused") or widgets.get("completed"):
            return
        widgets["pause_event"].clear()  # Bloque le thread
        widgets["paused"] = True
        widgets["status_label"].configure(text="⏸ En pause", text_color="orange")
        widgets["btn_pause"].configure(state="disabled")
        widgets["btn_resume"].configure(state="normal")
        log_app_event(f"Téléchargement mis en pause - Job ID: {job_id}")

    def _resume_download(self, job_id):
        """Reprend un téléchargement en pause."""
        if job_id not in self.download_jobs:
            return
        widgets = self.download_jobs[job_id]
        if not widgets.get("paused"):
            return
        widgets["pause_event"].set()  # Débloque le thread
        widgets["paused"] = False
        widgets["status_label"].configure(text="▶ Reprise...", text_color="gray")
        widgets["btn_pause"].configure(state="normal")
        widgets["btn_resume"].configure(state="disabled")
        log_app_event(f"Téléchargement repris - Job ID: {job_id}")

    def _cancel_download(self, job_id):
        """Annule un téléchargement avec confirmation."""
        if job_id not in self.download_jobs:
            return
        widgets = self.download_jobs[job_id]
        if widgets.get("completed"):
            return

        from tkinter import messagebox as _mb
        if not _mb.askyesno(
            "Annuler le téléchargement",
            "Voulez-vous vraiment annuler ce téléchargement ?"
        ):
            return

        # Débloquer la pause si en pause, puis signaler l'annulation
        widgets["pause_event"].set()
        widgets["cancel_event"].set()
        widgets["cancelled"] = True
        widgets["status_label"].configure(text="❌ Annulé", text_color="#ef4444")
        widgets["btn_pause"].configure(state="disabled")
        widgets["btn_resume"].configure(state="disabled")
        widgets["btn_cancel"].configure(state="disabled")
        log_app_event(f"Téléchargement annulé - Job ID: {job_id}")

    def upgrade_to_premium(self):
        """Ouvre la fenêtre de mise à niveau vers Premium"""
        try:
            payment_window = PaymentWindow(self, self.license_manager, callback=self.refresh_after_upgrade)
            payment_window.focus()
        except Exception as e:
            log_error(f"Erreur ouverture fenêtre premium: {e}")
            messagebox.showerror("Erreur", f"Impossible d'ouvrir la fenêtre de mise à niveau: {e}")

    def update_job_progress(self, job_id, progress_info):
        """Met à jour l'UI pour une tâche de téléchargement spécifique."""
        if job_id not in self.download_jobs:
            return

        widgets = self.download_jobs[job_id]
        
        try:
            if progress_info['status'] == 'downloading':
                # Arrêter la barre indéterminée dès que le vrai progress commence
                if "indet_progress" in widgets:
                    widgets["indet_progress"].stop()
                    del widgets["indet_progress"]

                # Mettre à jour le titre si on l'obtient
                if 'info_dict' in progress_info and widgets["title_label"].cget("text").startswith("En attente"):
                    title = progress_info['info_dict'].get('title', 'Titre inconnu')
                    widgets["title_label"].configure(text=title)

                total_bytes = progress_info.get('total_bytes') or progress_info.get('total_bytes_estimate', 0)
                downloaded_bytes = progress_info.get('downloaded_bytes', 0)

                if total_bytes and total_bytes > 0:
                    percentage = downloaded_bytes / total_bytes
                    widgets["progress_bar"].set(percentage)

                    speed = progress_info.get('speed', 0)
                    speed_str = f"{speed / 1024 / 1024:.2f} MB/s" if speed else "Calcul en cours..."
                    eta = progress_info.get('eta')
                    eta_str = f"{int(eta)}s" if eta is not None else "..."
                    
                    status = f"{percentage * 100:.1f}% de {total_bytes / 1024 / 1024:.2f} MB @ {speed_str} (ETA: {eta_str})"
                    widgets["status_label"].configure(text=status)
                else:
                    status = f"{downloaded_bytes / 1024 / 1024:.2f} MB téléchargés"
                    widgets["status_label"].configure(text=status)

            elif progress_info['status'] == 'finished':
                widgets["status_label"].configure(text="Finalisation (conversion MP3...)", text_color="#a3e635")
                widgets["progress_bar"].set(1.0)

        except Exception as e:
            widgets["status_label"].configure(text=f"Erreur de mise à jour: {e}", text_color="orange")

    def update_download_button_state(self):
        """Met à jour l'état et le texte du bouton de téléchargement principal."""
        if self.license_manager.is_premium:
            self.main_download_button.configure(
                text="⬇ Ajouter un téléchargement",
                state="normal",
                fg_color="#007eff"
            )
            active = len(self.download_jobs)
            if active > 0:
                self.download_hint_label.configure(
                    text=f"✅ {active} téléchargement(s) en cours — collez une nouvelle URL et recliquez pour en ajouter un autre."
                )
            else:
                self.download_hint_label.configure(
                    text="Collez une URL et cliquez sur le bouton pour démarrer."
                )
        else:
            # Compter seulement les jobs actifs (pas encore terminés)
            active_jobs = any(
                not job.get("completed", False)
                for job in self.download_jobs.values()
            )
            if active_jobs:
                self.main_download_button.configure(text="Téléchargement en cours...", state="disabled")
                self.download_hint_label.configure(
                    text="⏳ Attendez la fin avant de lancer un nouveau téléchargement."
                )
            else:
                self.main_download_button.configure(text="Télécharger", state="normal", fg_color="#2563eb")
                self.download_hint_label.configure(text="")

    def start_download(self):
        try:
            url = self.url_var.get().strip()
            if not url:
                messagebox.showerror("Erreur", "Veuillez entrer une URL valide")
                return

            # Vérifier si l'utilisateur peut télécharger (limite atteinte pour les utilisateurs gratuits)
            if not self.license_manager.is_premium:
                # Pour les utilisateurs gratuits, un seul téléchargement à la fois
                if len(self.download_jobs) > 0:
                    messagebox.showwarning("Limite atteinte", "Veuillez attendre la fin du téléchargement en cours pour en lancer un nouveau. Passez Premium pour les téléchargements simultanés.")
                    return
            
            # Vérifier si l'utilisateur peut télécharger en HD
            if self.format_var.get() == "video_hd" and not self.license_manager.is_premium:
                response = messagebox.askyesno(
                    "Format Premium requis",
                    "La qualité HD est réservée aux utilisateurs Premium.\n\nVoulez-vous passer à la version Premium maintenant?"
                )
                if response:
                    self.upgrade_to_premium()
                return
            
            # Vérifier et créer le dossier de destination
            if not os.path.exists(self.output_path):
                try:
                    os.makedirs(self.output_path, exist_ok=True)
                except PermissionError:
                    messagebox.showerror("Erreur", "Permissions insuffisantes pour créer le dossier de destination. Essayez de lancer l'application en tant qu'administrateur.")
                    return
                except Exception as e:
                    messagebox.showerror("Erreur", f"Impossible d'accéder au dossier de destination: {str(e)}")
                    return

            # Vérifier l'espace disque disponible
            try:
                free_space = shutil.disk_usage(self.output_path).free
                if free_space < 100 * 1024 * 1024:  # Moins de 100MB
                    response = messagebox.askyesno(
                        "Espace disque faible",
                        f"Il ne reste que {free_space // (1024*1024)} MB d'espace libre.\nVoulez-vous continuer ?"
                    )
                    if not response:
                        return
            except Exception as e:
                log_error(f"Erreur vérification espace disque: {e}")

            self.job_id_counter += 1
            job_id = self.job_id_counter
            format_option = self.format_var.get()
            is_premium = self.license_manager.is_premium

            # Animation pulse sur le bouton
            from src.gui.animations import pulse_button
            pulse_button(self.main_download_button, "#2563eb", "#1d4ed8", interval=150, repeat=2)

            # Créer le widget UI pour cette tâche
            self._create_job_widget(job_id, url)

            # Soumettre la tâche au pool de threads
            self.download_executor.submit(
                self._download_worker,
                job_id,
                url,
                self.output_path,
                format_option,
                is_premium
            )

            self.url_var.set("") # Vider le champ URL
            self.update_download_button_state()
            
            log_app_event(f"Téléchargement démarré - Job ID: {job_id}, URL: {url[:50]}...")

        except Exception as e:
            log_error(f"Erreur dans start_download: {e}")
            messagebox.showerror("Erreur", f"Erreur lors du lancement du téléchargement: {str(e)}")
            self.update_download_button_state()

    def select_video_for_conversion(self):
        """Ouvre une boîte de dialogue pour sélectionner un fichier vidéo à convertir."""
        file_path = filedialog.askopenfilename(
            title="Sélectionner un fichier vidéo",
            filetypes=[("Fichiers vidéo", "*.mp4 *.mkv *.avi *.mov *.webm"), ("Tous les fichiers", "*.*")]
        )
        if file_path:
            self.conversion_input_file.set(file_path)
            filename = os.path.basename(file_path)
            self.conversion_file_label.configure(text=filename, text_color="white")
            self.convert_button.configure(state="normal")
            self.conversion_status_label.configure(text="")

    def start_conversion(self):
        """Lance le processus de conversion du fichier sélectionné."""
        input_file = self.conversion_input_file.get()
        if not input_file:
            messagebox.showerror("Erreur", "Veuillez d'abord sélectionner un fichier.")
            return

        self.convert_button.configure(state="disabled")
        self.conversion_status_label.configure(text="Conversion en cours...", text_color="white")
        self.conversion_progress.pack(pady=10, padx=10, fill="x")  # Afficher la barre de progression
        self.conversion_progress.start()  # Mode indéterminé

        self.converter.convert_to_audio(
            input_path=input_file,
            completion_callback=self.conversion_complete
        )

    def conversion_complete(self, success, message, output_path):
        """Callback appelé à la fin de la conversion locale."""
        self.conversion_progress.stop()
        self.conversion_progress.pack_forget()  # Cacher à nouveau
        self.convert_button.configure(state="normal")

        if success:
            self.conversion_status_label.configure(text=f"Succès !\nFichier sauvegardé ici :\n{output_path}", text_color="green")
            messagebox.showinfo("Conversion terminée", message)
        else:
            self.conversion_status_label.configure(text=f"Échec :\n{message}", text_color="red")
            messagebox.showerror("Erreur de conversion", message)

    def _download_worker(self, job_id, url, output_path, format_option, is_premium):
        """Cette fonction est exécutée par le ThreadPoolExecutor."""

        def progress_callback_wrapper(d):
            self.after(0, self.update_job_progress, job_id, d)

        def completion_callback_wrapper(success, message, file_path=None):
            self.after(0, self.job_complete, job_id, success, message, file_path)

        # Récupérer les events du job
        widgets = self.download_jobs.get(job_id, {})
        pause_event  = widgets.get("pause_event")
        cancel_event = widgets.get("cancel_event")

        self.downloader.download_video(
            url, output_path, format_option, is_premium,
            progress_callback_wrapper, completion_callback_wrapper,
            pause_event=pause_event, cancel_event=cancel_event
        )

    def _restore_downloads_panel(self):
        """Recharge les vidéos téléchargées depuis l'historique au démarrage."""
        try:
            history = self.history_manager.get_recent(50)
            for entry in reversed(history):
                if entry.get("success") and entry.get("file_path"):
                    path = entry["file_path"]
                    # Vérifier que le fichier existe encore sur le disque
                    if os.path.exists(path):
                        # Accepter seulement les fichiers vidéo/audio
                        ext = os.path.splitext(path)[1].lower()
                        if ext in ('.mp4', '.mkv', '.avi', '.mov', '.webm', '.mp3', '.m4a'):
                            self.downloads_panel.add_video(path, self._open_video_player)
        except Exception as e:
            log_error(f"Erreur restauration panneau vidéos: {e}")

    def _open_video_player(self, video_path: str):
        """Ouvre le lecteur vidéo intégré TelVid Player."""
        try:
            from src.gui.video_player import VideoPlayer
            player = VideoPlayer(self, video_path)
            player.focus()
        except Exception as e:
            log_error(f"Erreur ouverture lecteur: {e}")
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le lecteur:\n{e}")

    def open_settings_window(self):
        """Ouvre la fenêtre des paramètres"""
        try:
            settings_window = SettingsWindow(self, self.settings_manager)
            settings_window.focus()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir les paramètres: {e}")

    def open_history_window(self):
        """Ouvre la fenêtre de l'historique"""
        try:
            history_window = HistoryWindow(self, self.history_manager)
            history_window.focus()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir l'historique: {e}")

    def on_closing(self):
        """Gestionnaire de fermeture de l'application"""
        try:
            # Sauvegarder la géométrie de la fenêtre
            geometry = self.geometry()
            self.settings_manager.set("window_geometry", geometry)
            
            # Sauvegarder le chemin de téléchargement actuel
            current_path = self.output_path_var.get()
            if current_path:
                self.settings_manager.set("download_path", current_path)
            
            # Arrêter proprement le pool de threads
            self.download_executor.shutdown(wait=False, cancel_futures=True)
            
            log_app_event("Application fermée proprement")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde: {e}")
        finally:
            self.destroy()

    def job_complete(self, job_id, success, message, file_path=None):
        """Callback appelé à la fin d'une tâche de téléchargement."""
        if job_id not in self.download_jobs:
            return

        widgets = self.download_jobs[job_id]

        try:
            # Historique
            if self.settings_manager.get("history_enabled", True):
                url = widgets.get("url", "URL inconnue")
                title = message if success else "Échec du téléchargement"
                error_msg = message if not success else None
                self.history_manager.add_download(url, title, success, file_path, error_msg)

            # Désactiver tous les boutons de contrôle
            for btn in ("btn_pause", "btn_resume", "btn_cancel"):
                try:
                    widgets[btn].configure(state="disabled")
                except Exception:
                    pass

            # Arrêter la barre indéterminée si encore active
            if "indet_progress" in widgets:
                widgets["indet_progress"].stop()
                del widgets["indet_progress"]

            if success:
                fname = os.path.basename(file_path) if file_path else "Fichier téléchargé"
                widgets["status_label"].configure(text=f"✅ Terminé: {fname}", text_color="green")
                widgets["progress_bar"].set(1.0)

                # Toast de notification
                from src.gui.animations import show_toast
                show_toast(self, f"✅ Téléchargement terminé : {fname[:40]}", color="#166534", duration=3000)

                # Ajouter au panneau vidéos
                if file_path and os.path.exists(file_path):
                    self.after(500, lambda p=file_path: self.downloads_panel.add_video(
                        p, self._open_video_player
                    ))

                # Bouton ouvrir dossier
                def open_folder():
                    try:
                        folder = os.path.dirname(file_path) if file_path else self.output_path
                        if os.path.exists(folder):
                            os.startfile(folder)
                    except Exception as e:
                        log_error(f"Erreur ouverture dossier: {e}")

                open_button = ctk.CTkButton(
                    widgets["frame"],
                    text="📁 Ouvrir dossier",
                    command=open_folder,
                    width=120, height=26, corner_radius=6
                )
                open_button.pack(side="right", padx=5, pady=2)

            else:
                widgets["status_label"].configure(text=f"❌ Échec: {message}", text_color="red")
                widgets["progress_bar"].set(0)

            # Supprimer le widget après 8 secondes
            def remove_job():
                try:
                    if job_id in self.download_jobs:
                        widgets["frame"].destroy()
                        self.download_jobs.pop(job_id, None)
                        if len(self.download_jobs) == 0:
                            self.empty_list_label = ctk.CTkLabel(
                                self.downloads_list_frame,
                                text="Aucun téléchargement en cours.",
                                text_color="gray"
                            )
                            self.empty_list_label.pack(pady=20)
                        self.update_download_button_state()
                except Exception as e:
                    log_error(f"Erreur suppression job: {e}")

            self.after(8000, remove_job)

            # Débloquer le bouton immédiatement
            widgets["completed"] = True
            if not self.license_manager.is_premium:
                self.main_download_button.configure(
                    text="Télécharger", state="normal", fg_color="#2563eb"
                )
                self.download_hint_label.configure(text="")
            else:
                self.update_download_button_state()

            log_app_event(f"Téléchargement terminé - Job ID: {job_id}, Succès: {success}")

        except Exception as e:
            log_error(f"Erreur dans job_complete: {e}")
            print(f"Erreur dans job_complete: {e}")

    def check_license_status(self):
        """Vérifie et met à jour le statut de la licence"""
        try:
            # Cette méthode est appelée au démarrage pour vérifier la licence
            self.license_manager.load_license()
            self.update_download_button_state()
            log_app_event(f"Statut licence vérifié: {'Premium' if self.license_manager.is_premium else 'Gratuit'}")
        except Exception as e:
            log_error(f"Erreur vérification licence: {e}")
            print(f"Erreur lors de la vérification de la licence: {e}")
    
    def upgrade_to_premium(self):
        """Ouvre la fenêtre de mise à niveau vers Premium"""
        try:
            payment_window = PaymentWindow(self, self.license_manager, callback=self.refresh_after_upgrade)
            payment_window.focus()
        except Exception as e:
            log_error(f"Erreur ouverture fenêtre premium: {e}")
            messagebox.showerror("Erreur", f"Impossible d'ouvrir la fenêtre de mise à niveau: {e}")
    
    def update_premium_banner(self):
        """Met à jour la bannière premium"""
        try:
            # Supprimer les anciens widgets du bouton upgrade s'ils existent
            for widget in self.banner.winfo_children():
                if isinstance(widget, ctk.CTkButton):
                    widget.destroy()

            if not self.license_manager.is_premium:
                # Afficher la bannière avec le bouton "Passer Premium"
                self.banner.pack(pady=10, padx=10, fill="x")
                # Cacher le badge premium s'il existe
                if hasattr(self, '_premium_badge'):
                    try:
                        self._premium_badge.pack_forget()
                    except Exception:
                        pass
                upgrade_btn = ctk.CTkButton(
                    self.banner, text="Passer Premium", command=self.upgrade_to_premium,
                    fg_color="#FFD700", text_color="black", hover_color="#FFC000"
                )
                upgrade_btn.pack(side="right", padx=10)
            else:
                # Cacher complètement la bannière en Premium
                self.banner.pack_forget()

                # Afficher un petit badge discret si licence non lifetime
                if self.license_manager.license_type != "lifetime" and self.license_manager.expiry_date:
                    expiry_date = self.license_manager.expiry_date.strftime("%d/%m/%Y")
                    if not hasattr(self, '_premium_badge') or not self._premium_badge.winfo_exists():
                        self._premium_badge = ctk.CTkLabel(
                            self.banner.master,
                            text=f"✦ Premium actif jusqu'au {expiry_date}",
                            font=("Helvetica", 11, "bold"),
                            text_color="#4ade80",
                            fg_color="transparent"
                        )
                        self._premium_badge.pack(pady=(0, 4))
        except Exception as e:
            log_error(f"Erreur mise à jour bannière: {e}")
    
    def refresh_after_upgrade(self):
        """Met à jour l'interface après l'activation du premium"""
        try:
            self.update_download_button_state()
            self.update_premium_banner()
            
            # Mettre à jour l'état des boutons radio pour la qualité HD
            for widget in self.winfo_children():
                if isinstance(widget, ctk.CTkFrame):
                    for child in widget.winfo_children():
                        if isinstance(child, ctk.CTkFrame):
                            for grandchild in child.winfo_children():
                                if isinstance(grandchild, ctk.CTkRadioButton) and grandchild.cget("text") == "Vidéo HD":
                                    grandchild.configure(state="normal" if self.license_manager.is_premium else "disabled")
            
            # Mettre à jour le format sélectionné si nécessaire
            if not self.license_manager.is_premium and self.format_var.get() == "video_hd":
                self.format_var.set("video_sd")
                
            log_app_event("Interface mise à jour après upgrade premium")
        except Exception as e:
            log_error(f"Erreur refresh après upgrade: {e}")
    
    def choose_output_path(self):
        """Permet de choisir le dossier de destination"""
        try:
            path = filedialog.askdirectory(initialdir=self.output_path)
            if path:
                self.output_path = path
                self.output_path_var.set(path)
                # Sauvegarder le nouveau chemin
                self.settings_manager.set("download_path", path)
                log_settings_change("download_path", self.output_path, path)
                
                # Mettre à jour l'affichage
                for widget in self.winfo_children():
                    if isinstance(widget, ctk.CTkFrame):
                        for child in widget.winfo_children():
                            if isinstance(child, ctk.CTkFrame):
                                for grandchild in child.winfo_children():
                                    if isinstance(grandchild, ctk.CTkLabel) and grandchild.cget("text").startswith("Dossier de destination"):
                                        grandchild.configure(text=f"Dossier de destination : {self.output_path}")
        except Exception as e:
            log_error(f"Erreur choix dossier: {e}")
            messagebox.showerror("Erreur", f"Erreur lors du choix du dossier: {e}")

    def open_about_window(self):
        """Ouvre la fenêtre À propos avec la licence"""
        try:
            win = ctk.CTkToplevel(self)
            win.title("À propos de TelVid-Vizane")
            win.geometry("700x600")
            win.resizable(True, True)
            win.transient(self)

            win.withdraw()
            win.update_idletasks()

            # En-tête
            mode = ctk.get_appearance_mode()
            header_bg = "#1e293b" if mode == "Dark" else "#e2e8f0"
            header = ctk.CTkFrame(win, fg_color=header_bg)
            header.pack(fill="x", padx=0, pady=0)

            ctk.CTkLabel(
                header, text="TelVid-Vizane",
                font=("Helvetica", 22, "bold"), text_color="#60a5fa"
            ).pack(pady=(15, 2))
            ctk.CTkLabel(
                header, text="Version 1.1.0  —  © 2026 Vital Zagabe Néophite (VIZANE)",
                font=("Helvetica", 11), text_color="#94a3b8"
            ).pack(pady=(0, 15))

            # Onglets
            tab_frame = ctk.CTkFrame(win, fg_color="transparent")
            tab_frame.pack(fill="x", padx=15, pady=(10, 0))

            content_box = ctk.CTkTextbox(win, font=("Consolas", 11), wrap="word")
            content_box.pack(fill="both", expand=True, padx=15, pady=10)

            def show_license():
                content_box.configure(state="normal")
                content_box.delete("1.0", "end")
                try:
                    license_path = resource_path("LICENSE.txt")
                    with open(license_path, "r", encoding="utf-8") as f:
                        content_box.insert("1.0", f.read())
                except Exception:
                    content_box.insert("1.0", "Fichier de licence introuvable.")
                content_box.configure(state="disabled")

            def show_about():
                content_box.configure(state="normal")
                content_box.delete("1.0", "end")
                about_text = (
                    "TelVid-Vizane — Téléchargeur de Vidéos\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "Développeur   : Vital Zagabe Néophite\n"
                    "Marque        : VIZANE\n"
                    "Version       : 1.1.0\n"
                    "Plateforme    : Windows\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "Contact & Support\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "Email         : vitalzagabe156@gmail.com\n"
                    "WhatsApp      : +243 827 788 173\n"
                    "Site web      : vizane.pythonanywhere.com\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "Plateformes supportées\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "YouTube, Facebook, Instagram, TikTok,\n"
                    "Twitter/X, Vimeo, Dailymotion et plus encore.\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "Technologies utilisées\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "Python 3.13 · CustomTkinter · yt-dlp\n"
                    "MoviePy · Pillow · Requests · Cryptography\n"
                )
                content_box.insert("1.0", about_text)
                content_box.configure(state="disabled")

            ctk.CTkButton(
                tab_frame, text="ℹ  À propos", command=show_about,
                width=140, fg_color="#2563eb", hover_color="#1d4ed8"
            ).pack(side="left", padx=(0, 8))

            ctk.CTkButton(
                tab_frame, text="📄  Licence (CLUF)", command=show_license,
                width=170, fg_color="#374151", hover_color="#4b5563"
            ).pack(side="left")

            # Bouton fermer
            ctk.CTkButton(
                win, text="Fermer", command=win.destroy,
                width=120, fg_color="#374151", hover_color="#4b5563"
            ).pack(pady=(0, 15))

            # Afficher "À propos" par défaut
            show_about()

            win.deiconify()
            win.grab_set()

            # Animation fondu
            from src.gui.animations import fade_in
            fade_in(win, duration=250)

        except Exception as e:
            log_error(f"Erreur ouverture fenêtre À propos: {e}")
            messagebox.showerror("Erreur", f"Impossible d'ouvrir la fenêtre: {e}")


def main():
    """Fonction principale pour lancer l'application."""
    app = VideoDownloaderApp()
    app.mainloop()

if __name__ == "__main__":
    main()