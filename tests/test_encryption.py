"""
Unit tests for Encryption Module
================================
"""

import pytest
import os
import tempfile
from utils.encryption import (
    EncryptionManager, SensitiveDataHandler,
    encrypt_database_value, decrypt_database_value,
    encrypt_config_value, decrypt_config_value
)

class TestEncryptionManager:
    """Test encryption manager functions."""
    
    def test_encrypt_string(self):
        """Test encrypting a string."""
        data = "test_sensitive_data"
        encrypted = EncryptionManager.encrypt(data)
        
        assert encrypted is not None
        assert encrypted != data
        assert isinstance(encrypted, str)
        assert len(encrypted) > len(data)
        
    def test_decrypt_string(self):
        """Test decrypting a string."""
        data = "test_sensitive_data"
        encrypted = EncryptionManager.encrypt(data)
        decrypted = EncryptionManager.decrypt(encrypted)
        
        assert decrypted == data
        
    def test_encrypt_bytes(self):
        """Test encrypting bytes."""
        data = b"test_bytes_data"
        encrypted = EncryptionManager.encrypt(data)
        
        assert encrypted is not None
        assert encrypted != data
        
    def test_decrypt_bytes(self):
        """Test decrypting bytes."""
        data = b"test_bytes_data"
        encrypted = EncryptionManager.encrypt(data)
        decrypted = EncryptionManager.decrypt(encrypted)
        
        assert decrypted == data
        
    def test_encrypt_dict(self):
        """Test encrypting a dictionary."""
        data = {"key": "value", "number": 123}
        encrypted = EncryptionManager.encrypt(data)
        
        assert encrypted is not None
        assert encrypted != str(data)
        
    def test_decrypt_dict(self):
        """Test decrypting a dictionary."""
        data = {"key": "value", "number": 123}
        encrypted = EncryptionManager.encrypt(data)
        decrypted = EncryptionManager.decrypt(encrypted, as_json=True)
        
        assert decrypted == data
        
    def test_encrypt_file(self):
        """Test encrypting a file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test file content")
            temp_path = f.name
        
        try:
            encrypted_path = EncryptionManager.encrypt_file(temp_path)
            
            assert os.path.exists(encrypted_path)
            assert encrypted_path.endswith('.enc')
            
            # Clean up
            os.remove(encrypted_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    def test_decrypt_file(self):
        """Test decrypting a file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test file content")
            temp_path = f.name
        
        try:
            encrypted_path = EncryptionManager.encrypt_file(temp_path)
            decrypted_path = EncryptionManager.decrypt_file(encrypted_path)
            
            assert os.path.exists(decrypted_path)
            
            with open(decrypted_path, 'r') as f:
                content = f.read()
            assert content == "test file content"
            
            # Clean up
            os.remove(encrypted_path)
            os.remove(decrypted_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    def test_encrypt_field(self):
        """Test encrypting a field value."""
        value = "sensitive_password"
        encrypted = EncryptionManager.encrypt_field(value)
        
        assert encrypted.startswith("ENC:")
        assert encrypted != value
        
    def test_decrypt_field(self):
        """Test decrypting a field value."""
        value = "sensitive_password"
        encrypted = EncryptionManager.encrypt_field(value)
        decrypted = EncryptionManager.decrypt_field(encrypted)
        
        assert decrypted == value
        
    def test_decrypt_non_encrypted_field(self):
        """Test decrypting a non-encrypted field."""
        value = "plain_text"
        decrypted = EncryptionManager.decrypt_field(value)
        
        assert decrypted == value

class TestSensitiveDataHandler:
    """Test sensitive data handler functions."""
    
    def test_mask_sensitive_data(self):
        """Test masking sensitive fields."""
        data = {
            "username": "testuser",
            "password": "secret123",
            "email": "test@example.com"
        }
        
        masked = SensitiveDataHandler.mask_sensitive_data(data, ["password"])
        
        assert masked["username"] == "testuser"
        assert masked["password"] == "****"
        assert masked["email"] == "test@example.com"
        
    def test_encrypt_sensitive_fields(self):
        """Test encrypting sensitive fields."""
        data = {
            "username": "testuser",
            "password": "secret123",
            "email": "test@example.com"
        }
        
        encrypted = SensitiveDataHandler.encrypt_sensitive_fields(data, ["password"])
        
        assert encrypted["username"] == "testuser"
        assert encrypted["password"].startswith("ENC:")
        assert encrypted["email"] == "test@example.com"
        
    def test_decrypt_sensitive_fields(self):
        """Test decrypting sensitive fields."""
        data = {
            "username": "testuser",
            "password": "secret123",
            "email": "test@example.com"
        }
        
        encrypted = SensitiveDataHandler.encrypt_sensitive_fields(data, ["password"])
        decrypted = SensitiveDataHandler.decrypt_sensitive_fields(encrypted, ["password"])
        
        assert decrypted["username"] == "testuser"
        assert decrypted["password"] == "secret123"
        assert decrypted["email"] == "test@example.com"

class TestDatabaseEncryption:
    """Test database encryption helpers."""
    
    def test_encrypt_database_value(self):
        """Test encrypting database value."""
        value = "db_secret"
        encrypted = encrypt_database_value(value)
        
        assert encrypted.startswith("ENC:")
        assert encrypted != value
        
    def test_decrypt_database_value(self):
        """Test decrypting database value."""
        value = "db_secret"
        encrypted = encrypt_database_value(value)
        decrypted = decrypt_database_value(encrypted)
        
        assert decrypted == value

class TestConfigEncryption:
    """Test configuration encryption helpers."""
    
    def test_encrypt_sensitive_config(self):
        """Test encrypting sensitive configuration."""
        encrypted = encrypt_config_value("api_key", "secret_key_123")
        
        assert encrypted.startswith("ENC:")
        assert encrypted != "secret_key_123"
        
    def test_encrypt_non_sensitive_config(self):
        """Test that non-sensitive config is not encrypted."""
        encrypted = encrypt_config_value("app_name", "ICAP")
        
        assert encrypted == "ICAP"
        assert not encrypted.startswith("ENC:")
        
    def test_decrypt_sensitive_config(self):
        """Test decrypting sensitive configuration."""
        encrypted = encrypt_config_value("api_key", "secret_key_123")
        decrypted = decrypt_config_value("api_key", encrypted)
        
        assert decrypted == "secret_key_123"
        
    def test_decrypt_non_sensitive_config(self):
        """Test decrypting non-sensitive configuration."""
        value = "ICAP"
        decrypted = decrypt_config_value("app_name", value)
        
        assert decrypted == value

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
