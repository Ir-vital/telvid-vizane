"""
Configuration des tests pour TelVid-Vizane
"""
import os
import sys
import pytest
import tempfile
import shutil
from unittest.mock import Mock, patch
from pathlib import Path

# Ajouter le répertoire racine au path pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture
def temp_dir():
    """Créer un répertoire temporaire pour les tests"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)

@pytest.fixture
def mock_config():
    """Configuration mock pour les tests"""
    return {
        'APPLICATION': {
            'name': 'TelVid-Vizane-Test',
            'version': '1.0.0-test',
            'debug': 'true',
            'log_level': 'DEBUG'
        },
        'DOWNLOAD': {
            'default_output_path': './test_downloads',
            'max_retries': '1',
            'timeout': '5'
        },
        'PREMIUM': {
            'trial_period_days': '1',
            'max_free_downloads': '2'
        }
    }

@pytest.fixture
def mock_license_data():
    """Données de licence mock pour les tests"""
    return {
        'license_key': 'TEST-LICENSE-KEY-12345',
        'license_type': 'premium',
        'expiry_date': '2025-12-31T23:59:59',
        'user_id': 'test-user-id-12345'
    }

@pytest.fixture
def mock_video_info():
    """Informations vidéo mock pour les tests"""
    return {
        'id': 'test_video_123',
        'title': 'Test Video Title',
        'uploader': 'Test Channel',
        'duration': 120,
        'view_count': 1000,
        'upload_date': '20240301',
        'formats': [
            {
                'format_id': '720p',
                'ext': 'mp4',
                'height': 720,
                'filesize': 50000000
            },
            {
                'format_id': '480p',
                'ext': 'mp4',
                'height': 480,
                'filesize': 30000000
            }
        ]
    }

@pytest.fixture
def mock_yt_dlp():
    """Mock pour yt-dlp"""
    with patch('yt_dlp.YoutubeDL') as mock_ydl:
        yield mock_ydl

@pytest.fixture
def mock_tkinter():
    """Mock pour tkinter pour les tests GUI"""
    with patch('tkinter.Tk'), \
         patch('customtkinter.CTk'), \
         patch('customtkinter.CTkLabel'), \
         patch('customtkinter.CTkEntry'), \
         patch('customtkinter.CTkButton'):
        yield

@pytest.fixture(autouse=True)
def setup_test_environment(temp_dir, monkeypatch):
    """Configuration automatique de l'environnement de test"""
    # Créer les répertoires nécessaires
    os.makedirs(os.path.join(temp_dir, 'logs'), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, 'config'), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, 'downloads'), exist_ok=True)
    
    # Définir les variables d'environnement de test
    monkeypatch.setenv('TELVID_TEST_MODE', '1')
    monkeypatch.setenv('TELVID_DATA_DIR', temp_dir)
    monkeypatch.setenv('TELVID_LOG_LEVEL', 'DEBUG')
    
    yield temp_dir

class MockProgress:
    """Mock pour les callbacks de progression"""
    def __init__(self):
        self.calls = []
    
    def __call__(self, d):
        self.calls.append(d)

class MockCompletion:
    """Mock pour les callbacks de completion"""
    def __init__(self):
        self.calls = []
    
    def __call__(self, success, message=None):
        self.calls.append({'success': success, 'message': message})
