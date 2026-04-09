"""
Tests pour le module main (interface utilisateur)
"""
import pytest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tkinter as tk
import customtkinter as ctk

# Ajouter le répertoire src au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def app(monkeypatch):
    """
    Fixture pytest qui initialise l'application VideoDownloaderApp dans un
    environnement de test contrôlé, sans afficher de fenêtre.
    """
    # Empêcher la fenêtre principale de s'afficher et de bloquer les tests
    monkeypatch.setattr(ctk.CTk, "mainloop", lambda self: None)
    monkeypatch.setattr(ctk.CTk, "withdraw", lambda self: None)

    # Patcher toutes les dépendances externes de l'application
    with patch('src.main.SettingsManager') as mock_settings_class, \
         patch('src.main.DownloadHistory') as mock_history_class, \
         patch('src.main.VideoDownloader') as mock_downloader_class, \
         patch('src.main.LicenseManager') as mock_license_class, \
         patch('src.main.IconManager') as mock_icon_class, \
         patch('src.main.check_for_updates_background'):

        # Configurer les mocks pour qu'ils retournent des valeurs par défaut saines
        mock_icon_class.return_value.get.return_value = None
        mock_license_class.return_value.is_premium = False
        
        # Configurer le mock de SettingsManager pour retourner les bonnes valeurs
        mock_settings_instance = mock_settings_class.return_value
        def get_setting_side_effect(key, default=None):
            settings = {
                "window_geometry": "900x750",
                "download_path": os.path.expanduser("~/Downloads"),
                "theme": "dark",
                "language": "fr",
                "auto_update": False,
                "history_enabled": True,
                "notifications": True,
            }
            return settings.get(key, default)
        mock_settings_instance.get.side_effect = get_setting_side_effect

        from src.main import VideoDownloaderApp
        test_app = VideoDownloaderApp()
        yield test_app
        # Nettoyage après le test
        test_app.destroy()


class TestIconManager:
    """Tests pour la classe IconManager"""
    
    def setup_method(self):
        """Configuration avant chaque test"""
        with patch('os.path.exists', return_value=True), \
             patch('customtkinter.CTkImage'), \
             patch('PIL.Image.open'):
            from src.main import IconManager
            self.icon_manager = IconManager()
    
    def test_init(self):
        """Test de l'initialisation de IconManager"""
        assert self.icon_manager.icons is not None
        assert self.icon_manager.icon_size == (28, 28)
    
    @patch('os.path.exists')
    @patch('customtkinter.CTkImage')
    @patch('PIL.Image.open')
    def test_load_icons_existing_files(self, mock_image_open, mock_ctk_image, mock_exists):
        """Test de chargement d'icônes existantes"""
        mock_exists.return_value = True
        mock_image = Mock()
        mock_image_open.return_value = mock_image
        mock_ctk_image.return_value = "mock_icon"
        
        from src.main import IconManager
        icon_manager = IconManager()
        
        # Vérifier que les icônes ont été chargées
        assert 'logo' in icon_manager.icons
        assert 'download' in icon_manager.icons
        assert 'video_hd' in icon_manager.icons
        assert 'video_sd' in icon_manager.icons
        assert 'audio' in icon_manager.icons
    
    @patch('os.path.exists')
    def test_load_icons_missing_files(self, mock_exists):
        """Test de chargement avec fichiers manquants"""
        mock_exists.return_value = False
        
        from src.main import IconManager
        icon_manager = IconManager()
        
        # Vérifier que les icônes sont None quand les fichiers n'existent pas
        for icon_name in ['logo', 'download', 'video_hd', 'video_sd', 'audio']:
            assert icon_manager.icons[icon_name] is None
    
    def test_get_existing_icon(self):
        """Test de récupération d'icône existante"""
        self.icon_manager.icons['test_icon'] = "mock_icon"
        
        result = self.icon_manager.get('test_icon')
        
        assert result == "mock_icon"
    
    def test_get_nonexistent_icon(self):
        """Test de récupération d'icône inexistante"""
        result = self.icon_manager.get('nonexistent_icon')
        
        assert result is None


class TestVideoDownloaderApp:
    """Tests pour la classe VideoDownloaderApp"""
    
    def test_init(self, app):
        """Test de l'initialisation de l'application"""
        assert app.output_path == os.path.expanduser("~/Downloads")
        assert hasattr(app, 'icon_manager')
        assert hasattr(app, 'downloader')
        assert hasattr(app, 'license_manager')
        assert isinstance(app.url_var, tk.StringVar)
    
    @patch('tkinter.filedialog.askdirectory')
    def test_browse_folder_selected(self, mock_askdirectory, app):
        """Test de sélection de dossier"""
        mock_askdirectory.return_value = "/test/path"
        app.choose_output_path()
        assert app.output_path == "/test/path"
        assert app.output_path_var.get() == "/test/path"
    
    @patch('tkinter.filedialog.askdirectory')
    def test_browse_folder_cancelled(self, mock_askdirectory, app):
        """Test d'annulation de sélection de dossier"""
        mock_askdirectory.return_value = ""
        original_path = app.output_path
        app.choose_output_path()
        assert app.output_path == original_path
    
    @patch('tkinter.messagebox.showerror')
    def test_start_download_empty_url(self, mock_showerror, app):
        """Test de démarrage de téléchargement avec URL vide"""
        app.url_var.set("")
        app.start_download()
        mock_showerror.assert_called_once_with("Erreur", "Veuillez entrer une URL valide")
    
    def test_start_download_valid_url(self, app):
        """Test de démarrage de téléchargement avec URL valide"""
        app.url_var.set("https://www.youtube.com/watch?v=test123")
        app.start_download()
        app.downloader.download_video.assert_called_once()
        assert app.download_button.cget("state") == "disabled"
    
    def test_update_progress(self, app):
        """Test de mise à jour de la progression"""
        progress_data = {
            'status': 'downloading',
            'total_bytes': 1000,
            'downloaded_bytes': 500,
            'speed': 1024 * 500,  # 500 KB/s
            'eta': 10
        }
        app.update_progress(progress_data)
        assert app.progress_var.get() == 0.5
        assert "50.0%" in app.status_var.get()
        assert "0.50 MB/s" in app.status_var.get()
    
    @patch('main.messagebox.showinfo')
    def test_download_complete_success(self, mock_showinfo, app):
        """Test de completion de téléchargement réussie"""
        app.download_complete(True, "Test Video", file_path="/path/to/video.mp4")
        mock_showinfo.assert_called_once()
        assert app.download_button.cget("state") == "normal"
        assert app.progress_var.get() == 0
        app.history_manager.add_download.assert_called_once()
    
    @patch('main.messagebox.showerror')
    def test_download_complete_failure(self, mock_showerror, app):
        """Test de completion de téléchargement échouée"""
        app.download_complete(False, "Erreur de téléchargement")
        mock_showerror.assert_called_once()
        assert app.download_button.cget("state") == "normal"

    def test_upgrade_to_premium(self, app):
        """Test d'ouverture de la fenêtre premium"""
        with patch('main.PaymentWindow') as mock_payment_window:
            app.upgrade_to_premium()
            mock_payment_window.assert_called_once_with(app, app.license_manager, callback=app.refresh_after_upgrade)
    
    def test_update_ui_for_premium(self, app):
        """Test de mise à jour de l'UI pour utilisateur premium"""
        app.license_manager.is_premium = True
        app.update_premium_banner()
        # Vérifier que le bouton "Passer Premium" n'est PAS présent
        found_button = False
        for widget in app.banner.winfo_children():
            if isinstance(widget, ctk.CTkButton) and "Premium" in widget.cget("text"):
                found_button = True
        assert not found_button
        # Vérifier qu'un label de statut premium EST présent
        found_label = False
        for widget in app.banner.winfo_children():
            if isinstance(widget, ctk.CTkLabel) and "Premium actif" in widget.cget("text"):
                found_label = True
        assert found_label
    
    def test_update_ui_for_free(self, app):
        """Test de mise à jour de l'UI pour utilisateur gratuit"""
        app.license_manager.is_premium = False
        app.update_premium_banner()
        # Vérifier que le bouton "Passer Premium" EST présent
        found_button = False
        for widget in app.banner.winfo_children():
            if isinstance(widget, ctk.CTkButton) and "Premium" in widget.cget("text"):
                found_button = True
        assert found_button


@pytest.mark.integration
class TestAppIntegration:
    """Tests d'intégration pour l'application complète"""
    
    def test_app_startup(self, app):
        """Test de démarrage complet de l'application"""
        # La fixture 'app' gère déjà le démarrage. On vérifie juste que c'est bien une instance de l'app.
        assert app is not None
        assert isinstance(app, ctk.CTk)
        assert app.title() == "TelVid-Vizane - Téléchargeur de Vidéos"
    
    def test_main_function(self):
        """Test de la fonction main"""
        with patch('src.main.VideoDownloaderApp') as mock_app_class:
            mock_app_instance = mock_app_class.return_value
            
            import src.main as main
            main.main()
            
            mock_app_class.assert_called_once()
            mock_app_instance.mainloop.assert_called_once()


