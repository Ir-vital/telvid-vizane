"""
Tests pour le module downloader
"""
import pytest
import os
import tempfile
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Ajouter le répertoire src au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from downloader import VideoDownloader


class TestVideoDownloader:
    """Tests pour la classe VideoDownloader"""
    
    def setup_method(self):
        """Configuration avant chaque test"""
        self.downloader = VideoDownloader()
        self.test_url = "https://www.youtube.com/watch?v=test123"
        self.test_output_path = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Nettoyage après chaque test"""
        import shutil
        if os.path.exists(self.test_output_path):
            shutil.rmtree(self.test_output_path, ignore_errors=True)
    
    def test_init(self):
        """Test de l'initialisation du downloader"""
        assert self.downloader is not None
        # La classe ne stocke plus ydl_opts comme attribut d'instance (thread-safety)
        # Les options sont créées à la volée dans _get_ydl_opts()
        assert hasattr(self.downloader, '_get_ydl_opts')
        assert hasattr(self.downloader, 'download_video')
    
    def test_download_video_empty_url(self):
        """Test avec URL vide"""
        completion_callback = Mock()
        
        self.downloader.download_video(
            "",
            self.test_output_path,
            format_option="video_sd",
            is_premium=False,
            completion_callback=completion_callback
        )
        
        # Laisser le thread démarrer
        import time
        time.sleep(0.1)
        completion_callback.assert_called_once_with(False, "L'URL est vide", None)
    
    def test_download_video_invalid_output_path(self):
        """Test avec chemin de sortie invalide"""
        completion_callback = Mock()
        invalid_path = "/invalid/path/that/does/not/exist"
        
        with patch('os.makedirs', side_effect=PermissionError("Permission denied")):
            self.downloader.download_video(
                self.test_url,
                invalid_path,
                format_option="video_sd",
                is_premium=False,
                completion_callback=completion_callback
            )
        
        import time
        time.sleep(0.1)
        completion_callback.assert_called_once()
        args = completion_callback.call_args[0]
        assert args[0] is False
        assert "Impossible de créer le dossier de sortie" in args[1]
    
    @patch('yt_dlp.YoutubeDL')
    def test_download_video_success(self, mock_ydl_class):
        """Test de téléchargement réussi"""
        mock_video_info = {'title': 'Test Video', 'duration': 120}
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.return_value = mock_video_info
        mock_ydl_instance.prepare_filename.return_value = "/tmp/Test Video.mp4"
        
        completion_callback = Mock()
        
        self.downloader.download_video(
            self.test_url,
            self.test_output_path,
            format_option="video_sd",
            is_premium=False,
            completion_callback=completion_callback
        )
        
        import time
        time.sleep(0.5)
        
        completion_callback.assert_called_once()
        args = completion_callback.call_args[0]
        assert args[0] is True
    
    @patch('yt_dlp.YoutubeDL')
    def test_download_video_yt_dlp_error(self, mock_ydl_class):
        """Test d'erreur yt-dlp"""
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.side_effect = Exception("Erreur yt-dlp")
        
        completion_callback = Mock()
        
        self.downloader.download_video(
            self.test_url,
            self.test_output_path,
            format_option="video_sd",
            is_premium=False,
            completion_callback=completion_callback
        )
        
        import time
        time.sleep(0.5)
        
        completion_callback.assert_called_once()
        args = completion_callback.call_args[0]
        assert args[0] is False
    
    def test_progress_callback_integration(self):
        """Test que _get_ydl_opts inclut bien le progress_hook"""
        progress_callback = Mock()
        opts, temp_dir = self.downloader._get_ydl_opts(
            self.test_output_path, "video_sd", False, progress_callback
        )
        assert 'progress_hooks' in opts
        assert progress_callback in opts['progress_hooks']
        # Nettoyer le dossier temporaire créé
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_output_template_configuration(self):
        """Test que le template de sortie est bien configuré dans _get_ydl_opts"""
        import os
        opts, temp_dir = self.downloader._get_ydl_opts(
            self.test_output_path, "video_sd", False, None
        )
        expected_template = os.path.join(self.test_output_path, '%(title)s.%(ext)s')
        assert opts['outtmpl'] == expected_template
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.mark.parametrize("url,expected_valid", [
        ("https://www.youtube.com/watch?v=test123", True),
        ("https://vimeo.com/123456789", True),
        ("https://www.tiktok.com/@user/video/123", True),
        ("https://www.instagram.com/p/abc123/", True),
        ("", False),
        ("   ", False),
        (None, False),
    ])
    def test_url_validation(self, url, expected_valid):
        """Test de validation des URLs"""
        if url is None or not url.strip():
            assert not self.downloader._is_valid_url(url or "")
        else:
            result = self.downloader._is_valid_url(url)
            assert result == expected_valid
    
    def test_options_configuration(self):
        """Test de la configuration des options yt-dlp via _get_ydl_opts"""
        opts, temp_dir = self.downloader._get_ydl_opts(
            self.test_output_path, "video_sd", False, None
        )
        assert opts['noplaylist'] is True
        assert opts['retries'] == 3
        assert opts['ignoreerrors'] is True
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
