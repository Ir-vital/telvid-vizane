"""
Système de mise à jour automatique pour TelVid-Vizane
Vérifie les nouvelles versions et gère les mises à jour
"""

import os
import json
import requests
import threading
import tempfile
import zipfile
import shutil
import subprocess
from datetime import datetime, timedelta
from tkinter import messagebox
import customtkinter as ctk

class AutoUpdater:
    def __init__(self, current_version="1.0.0"):
        self.current_version = current_version
        self.update_url = "https://api.github.com/repos/Ir-vital/telvid-vizane/releases/latest"
        self.fallback_url = "https://httpbin.org/status/404"
        app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
        app_dir = os.path.join(app_data, 'TelVid-Vizane')
        os.makedirs(app_dir, exist_ok=True)
        self.update_check_file = os.path.join(app_dir, "last_update_check.json")
        self.app_name = "TelVid-Vizane"
        
    def check_for_updates(self, silent=False):
        """Vérifie s'il y a des mises à jour disponibles"""
        try:
            # Vérifier si on a déjà vérifié récemment (moins de 24h)
            if not silent and self._should_skip_check():
                return {"available": False, "skipped": True}
            
            # Tentative de vérification avec gestion d'erreur réseau
            try:
                response = requests.get(self.update_url, timeout=10)
                if response.status_code == 200:
                    release_data = response.json()
                    latest_version = release_data.get("tag_name", "").replace("v", "")
                    
                    if self._is_newer_version(latest_version):
                        if not silent:
                            self._save_update_check()
                        return {
                            "available": True,
                            "version": latest_version,
                            "download_url": self._get_download_url(release_data),
                            "changelog": release_data.get("body", "Aucune information disponible"),
                            "release_date": release_data.get("published_at", "")
                        }
                elif response.status_code == 404:
                    # Repository n'existe pas encore - normal pour une démo
                    if not silent:
                        print("Repository de mise à jour non configuré (normal en mode démo)")
                else:
                    print(f"Erreur HTTP {response.status_code} lors de la vérification des mises à jour")
            except requests.exceptions.RequestException as e:
                if not silent:
                    print(f"Erreur réseau lors de la vérification des mises à jour: {e}")
                return {"available": False, "error": f"Erreur réseau: {e}"}
            
            if not silent:
                self._save_update_check()
            return {"available": False}
            
        except Exception as e:
            print(f"Erreur lors de la vérification des mises à jour: {e}")
            return {"available": False, "error": str(e)}
    
    def _should_skip_check(self):
        """Vérifie si on doit ignorer la vérification (déjà fait récemment)"""
        try:
            if os.path.exists(self.update_check_file):
                with open(self.update_check_file, 'r') as f:
                    data = json.load(f)
                    last_check = datetime.fromisoformat(data.get("last_check", ""))
                    return datetime.now() - last_check < timedelta(hours=24)
        except:
            pass
        return False
    
    def _save_update_check(self):
        """Sauvegarde la date de dernière vérification"""
        try:
            data = {"last_check": datetime.now().isoformat()}
            with open(self.update_check_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Erreur sauvegarde vérification: {e}")
    
    def _is_newer_version(self, latest_version):
        """Compare les versions pour voir si une mise à jour est disponible"""
        try:
            current_parts = [int(x) for x in self.current_version.split('.')]
            latest_parts = [int(x) for x in latest_version.split('.')]
            
            # Égaliser la longueur des listes
            max_len = max(len(current_parts), len(latest_parts))
            current_parts.extend([0] * (max_len - len(current_parts)))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            
            return latest_parts > current_parts
        except:
            return False
    
    def _get_download_url(self, release_data):
        """Extrait l'URL de téléchargement depuis les données de release"""
        assets = release_data.get("assets", [])
        for asset in assets:
            name = asset.get("name", "").lower()
            if name.endswith(".zip") or name.endswith(".exe"):
                return asset.get("browser_download_url")
        return release_data.get("zipball_url")  # Fallback
    
    def download_and_install_update(self, download_url, progress_callback=None):
        """Télécharge et installe la mise à jour"""
        try:
            # Créer un dossier temporaire
            temp_dir = tempfile.mkdtemp()
            
            # Télécharger le fichier
            if progress_callback:
                progress_callback(0, "Téléchargement en cours...")
            
            response = requests.get(download_url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            
            temp_file = os.path.join(temp_dir, "update.zip")
            downloaded = 0
            
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            progress = (downloaded / total_size) * 50  # 50% pour le téléchargement
                            progress_callback(progress, f"Téléchargement: {downloaded//1024}KB/{total_size//1024}KB")
            
            if progress_callback:
                progress_callback(50, "Extraction en cours...")
            
            # Extraire le fichier
            extract_dir = os.path.join(temp_dir, "extracted")
            with zipfile.ZipFile(temp_file, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            if progress_callback:
                progress_callback(75, "Installation en cours...")
            
            # Installer la mise à jour
            self._install_update(extract_dir)
            
            if progress_callback:
                progress_callback(100, "Mise à jour terminée!")
            
            return True
            
        except Exception as e:
            print(f"Erreur lors de la mise à jour: {e}")
            return False
        finally:
            # Nettoyer les fichiers temporaires
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
    
    def _install_update(self, extract_dir):
        """Installe les fichiers mis à jour"""
        # Trouver le dossier principal dans l'archive
        main_folder = None
        for item in os.listdir(extract_dir):
            item_path = os.path.join(extract_dir, item)
            if os.path.isdir(item_path):
                main_folder = item_path
                break
        
        if not main_folder:
            main_folder = extract_dir
        
        # Copier les nouveaux fichiers
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        for item in os.listdir(main_folder):
            src = os.path.join(main_folder, item)
            dst = os.path.join(current_dir, item)
            
            if os.path.isfile(src):
                # Sauvegarder l'ancien fichier
                if os.path.exists(dst):
                    backup = dst + ".backup"
                    if os.path.exists(backup):
                        os.remove(backup)
                    os.rename(dst, backup)
                
                # Copier le nouveau fichier
                shutil.copy2(src, dst)
            elif os.path.isdir(src) and item not in ['__pycache__', '.git']:
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)

class UpdateDialog(ctk.CTkToplevel):
    def __init__(self, parent, update_info):
        super().__init__(parent)
        self.update_info = update_info
        self.result = None
        
        self.title("Mise à jour disponible")
        self.geometry("500x400")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.create_widgets()
    
    def create_widgets(self):
        # Titre
        title_label = ctk.CTkLabel(
            self, 
            text=f"Nouvelle version disponible: {self.update_info['version']}", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=20)
        
        # Informations de la version
        info_frame = ctk.CTkFrame(self)
        info_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Date de sortie
        if self.update_info.get("release_date"):
            try:
                release_date = datetime.fromisoformat(self.update_info["release_date"].replace("Z", "+00:00"))
                date_str = release_date.strftime("%d/%m/%Y")
                date_label = ctk.CTkLabel(info_frame, text=f"Date de sortie: {date_str}")
                date_label.pack(pady=5)
            except:
                pass
        
        # Changelog
        changelog_label = ctk.CTkLabel(info_frame, text="Nouveautés:", font=("Arial", 12, "bold"))
        changelog_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        changelog_text = ctk.CTkTextbox(info_frame, height=200)
        changelog_text.pack(fill="both", expand=True, padx=10, pady=5)
        changelog_text.insert("1.0", self.update_info.get("changelog", "Aucune information disponible"))
        changelog_text.configure(state="disabled")
        
        # Boutons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=20, pady=20)
        
        cancel_button = ctk.CTkButton(
            button_frame, 
            text="Plus tard", 
            command=self.cancel_update
        )
        cancel_button.pack(side="right", padx=5)
        
        update_button = ctk.CTkButton(
            button_frame, 
            text="Mettre à jour maintenant", 
            command=self.start_update,
            fg_color="#22c55e",
            hover_color="#16a34a"
        )
        update_button.pack(side="right", padx=5)
    
    def cancel_update(self):
        self.result = False
        self.destroy()
    
    def start_update(self):
        self.result = True
        self.destroy()

class UpdateProgressDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Mise à jour en cours")
        self.geometry("400x150")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.create_widgets()
    
    def create_widgets(self):
        # Label de statut
        self.status_label = ctk.CTkLabel(self, text="Préparation...", font=("Arial", 12))
        self.status_label.pack(pady=20)
        
        # Barre de progression
        self.progress_bar = ctk.CTkProgressBar(self, width=350)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        
        # Pourcentage
        self.percent_label = ctk.CTkLabel(self, text="0%")
        self.percent_label.pack(pady=5)
    
    def update_progress(self, progress, status):
        """Met à jour la barre de progression"""
        self.progress_bar.set(progress / 100)
        self.percent_label.configure(text=f"{int(progress)}%")
        self.status_label.configure(text=status)
        self.update()

def check_for_updates_background(app, settings_manager):
    """Fonction pour vérifier les mises à jour en arrière-plan"""
    if not settings_manager.get("auto_update", True):
        return
    
    def check_updates():
        updater = AutoUpdater()
        update_info = updater.check_for_updates(silent=True)
        
        if update_info.get("available"):
            # Afficher la boîte de dialogue dans le thread principal
            app.after(0, lambda: show_update_dialog(app, update_info))
    
    # Lancer la vérification dans un thread séparé
    thread = threading.Thread(target=check_updates, daemon=True)
    thread.start()

def show_update_dialog(app, update_info):
    """Affiche la boîte de dialogue de mise à jour"""
    dialog = UpdateDialog(app, update_info)
    app.wait_window(dialog)
    
    if dialog.result:
        # L'utilisateur veut mettre à jour
        progress_dialog = UpdateProgressDialog(app)
        
        def do_update():
            updater = AutoUpdater()
            success = updater.download_and_install_update(
                update_info["download_url"],
                progress_callback=lambda p, s: app.after(0, lambda: progress_dialog.update_progress(p, s))
            )
            
            app.after(0, lambda: update_completed(progress_dialog, success))
        
        # Lancer la mise à jour dans un thread séparé
        thread = threading.Thread(target=do_update, daemon=True)
        thread.start()

def update_completed(progress_dialog, success):
    """Appelé quand la mise à jour est terminée"""
    progress_dialog.destroy()
    
    if success:
        messagebox.showinfo(
            "Mise à jour terminée", 
            "La mise à jour a été installée avec succès!\nVeuillez redémarrer l'application."
        )
    else:
        messagebox.showerror(
            "Erreur de mise à jour", 
            "Une erreur s'est produite lors de la mise à jour.\nVeuillez réessayer plus tard."
        )
