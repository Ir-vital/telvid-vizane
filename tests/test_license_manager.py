"""
Tests pour le module license_manager
"""
import pytest
import json
import os
import tempfile
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

# Ajouter le répertoire src au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from license_manager import LicenseManager


class TestLicenseManager:
    """Tests pour la classe LicenseManager"""
    
    def setup_method(self):
        """Configuration avant chaque test"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock des fichiers de configuration
        with patch('os.path.exists', return_value=False), \
             patch('builtins.open', mock_open()):
            self.license_manager = LicenseManager()
    
    def teardown_method(self):
        """Nettoyage après chaque test"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init(self):
        """Test de l'initialisation du LicenseManager"""
        assert self.license_manager.config_file == 'premium_config.json'
        assert self.license_manager.license_file == 'license.json'
        assert self.license_manager.is_premium is False
        assert self.license_manager.license_type == "free"
        assert self.license_manager.user_id is not None
    
    @patch('uuid.uuid4')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    def test_get_or_create_user_id_new(self, mock_exists, mock_file, mock_uuid):
        """Test de création d'un nouvel ID utilisateur"""
        mock_exists.return_value = False
        mock_uuid.return_value = "test-uuid-12345"
        
        user_id = self.license_manager._get_or_create_user_id()
        
        assert user_id == "test-uuid-12345"
        mock_file.assert_called_with('user_id.txt', 'w')
        mock_file().write.assert_called_with("test-uuid-12345")
    
    @patch('builtins.open', new_callable=mock_open, read_data="existing-user-id")
    @patch('os.path.exists')
    def test_get_or_create_user_id_existing(self, mock_exists, mock_file):
        """Test de récupération d'un ID utilisateur existant"""
        mock_exists.return_value = True
        
        user_id = self.license_manager._get_or_create_user_id()
        
        assert user_id == "existing-user-id"
        mock_file.assert_called_with('user_id.txt', 'r')
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    def test_load_license_no_file(self, mock_exists, mock_file):
        """Test de chargement de licence sans fichier existant"""
        mock_exists.return_value = False
        
        self.license_manager.load_license()
        
        assert self.license_manager.license_key == ""
        assert self.license_manager.license_type == "free"
        assert self.license_manager.expiry_date is None
        assert self.license_manager.is_premium is False
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    def test_load_license_with_valid_file(self, mock_exists, mock_file):
        """Test de chargement de licence avec fichier valide"""
        mock_exists.return_value = True
        
        # Données de licence valides
        license_data = {
            'license_key': 'TEST-KEY-12345',
            'license_type': 'premium',
            'expiry_date': (datetime.now() + timedelta(days=30)).isoformat()
        }
        
        mock_file.return_value.read.return_value = json.dumps(license_data)
        
        with patch.object(self.license_manager, 'is_license_valid', return_value=True):
            self.license_manager.load_license()
        
        assert self.license_manager.license_key == 'TEST-KEY-12345'
        assert self.license_manager.license_type == 'premium'
        assert self.license_manager.is_premium is True
    
    def test_is_license_valid_no_key(self):
        """Test de validation de licence sans premium actif"""
        self.license_manager.is_premium = False
        self.license_manager.license_type = "free"
        
        assert self.license_manager.is_license_valid() is False
    
    def test_is_license_valid_expired(self):
        """Test de validation de licence expirée"""
        self.license_manager.is_premium = True
        self.license_manager.license_type = "monthly"
        self.license_manager.expiry_date = datetime.now() - timedelta(days=1)
        
        with patch.object(self.license_manager, 'save_license'):
            assert self.license_manager.is_license_valid() is False
    
    def test_is_license_valid_active(self):
        """Test de validation de licence active (non expirée)"""
        self.license_manager.is_premium = True
        self.license_manager.license_type = "monthly"
        self.license_manager.expiry_date = datetime.now() + timedelta(days=30)
        
        assert self.license_manager.is_license_valid() is True
    
    @patch('json.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_license(self, mock_file, mock_json_dump):
        """Test de sauvegarde de licence"""
        self.license_manager.license_key = "TEST-KEY"
        self.license_manager.license_type = "premium"
        expiry = datetime.now() + timedelta(days=30)
        self.license_manager.expiry_date = expiry
        self.license_manager.user_id = "test-user-id"
        
        self.license_manager.save_license()
        
        mock_file.assert_called_with('license.json', 'w')
        
        # Vérifier les données passées à json.dump
        dump_args = mock_json_dump.call_args[0]
        license_data = dump_args[0]
        
        assert license_data['license_key'] == "TEST-KEY"
        assert license_data['license_type'] == "premium"
        assert license_data['expiry_date'] == expiry.isoformat()
        assert license_data['user_id'] == "test-user-id"
    
    def test_activate_license_invalid_key(self):
        """Test d'activation avec clé vide"""
        success, message = self.license_manager.activate_license("")
        
        assert success is False
        assert "vide" in message.lower() or "invalide" in message.lower()
    
    @patch('hashlib.sha256')
    def test_activate_license_valid_format(self, mock_hash):
        """Test d'activation — vérifie que le serveur est bien appelé"""
        mock_server_response = {
            "status": "success",
            "type": "monthly",
            "expiry": (datetime.now() + timedelta(days=30)).isoformat()
        }
        with patch.object(
            self.license_manager,
            '_validate_license_on_server',
            return_value=(True, mock_server_response)
        ), patch.object(self.license_manager, 'save_license'):
            success, message = self.license_manager.activate_license("SOME-VALID-KEY-123")
        
        assert success is True
        assert self.license_manager.is_premium is True
        assert self.license_manager.license_type == "monthly"
        assert "activée avec succès" in message
    
    @pytest.mark.parametrize("license_type,is_premium_expected", [
        ("free", False),
        ("monthly", True),
        ("yearly", True),
        ("lifetime", True),
    ])
    def test_license_type_validation(self, license_type, is_premium_expected):
        """Test de validation des types de licence"""
        self.license_manager.is_premium = is_premium_expected
        self.license_manager.license_type = license_type
        self.license_manager.expiry_date = datetime.now() + timedelta(days=30) if is_premium_expected else None

        with patch.object(self.license_manager, 'save_license'):
            result = self.license_manager.is_license_valid()

        assert result is is_premium_expected
    
    def test_reset_license(self):
        """Test de réinitialisation de licence"""
        # Configurer une licence premium
        self.license_manager.license_key = "TEST-KEY"
        self.license_manager.license_type = "premium"
        self.license_manager.is_premium = True
        self.license_manager.expiry_date = datetime.now() + timedelta(days=30)
        
        # Réinitialiser
        with patch.object(self.license_manager, 'save_license'):
            self.license_manager.reset_license()
        
        assert self.license_manager.license_key == ""
        assert self.license_manager.license_type == "free"
        assert self.license_manager.is_premium is False
        assert self.license_manager.expiry_date is None
