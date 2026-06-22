"""
Data Encryption at Rest for ICAP
=================================
AES-256 encryption for sensitive data storage.
"""

import os
import base64
import logging
from typing import Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import json

logger = logging.getLogger("Encryption")

# Encryption key from environment or generate one
ENCRYPTION_KEY = os.environ.get("ICAP_ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    # Generate a key for development (NOT for production)
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    logger.warning("Using auto-generated encryption key. Set ICAP_ENCRYPTION_KEY in production!")

# Ensure key is bytes
if isinstance(ENCRYPTION_KEY, str):
    ENCRYPTION_KEY = ENCRYPTION_KEY.encode()

# Derive a proper key from the encryption key
kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=b'icap-salt-2026',  # In production, use a random salt per deployment
    iterations=100000,
)
key = base64.urlsafe_b64encode(kdf.derive(ENCRYPTION_KEY))
cipher_suite = Fernet(key)

class EncryptionManager:
    """Manager for data encryption and decryption operations."""
    
    @staticmethod
    def encrypt(data: Union[str, bytes, dict, list]) -> str:
        """
        Encrypt data using AES-256.
        
        Args:
            data: Data to encrypt (string, bytes, dict, or list)
            
        Returns:
            Base64 encoded encrypted string
        """
        try:
            # Convert data to bytes
            if isinstance(data, (dict, list)):
                data_bytes = json.dumps(data).encode()
            elif isinstance(data, str):
                data_bytes = data.encode()
            elif isinstance(data, bytes):
                data_bytes = data
            else:
                raise ValueError(f"Unsupported data type: {type(data)}")
            
            # Encrypt
            encrypted = cipher_suite.encrypt(data_bytes)
            
            # Return as base64 string
            return base64.b64encode(encrypted).decode()
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    @staticmethod
    def decrypt(encrypted_data: str, as_json: bool = False) -> Union[str, dict, list]:
        """
        Decrypt data using AES-256.
        
        Args:
            encrypted_data: Base64 encoded encrypted string
            as_json: If True, parse result as JSON
            
        Returns:
            Decrypted data (string or parsed JSON)
        """
        try:
            # Decode base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            
            # Decrypt
            decrypted = cipher_suite.decrypt(encrypted_bytes)
            
            # Convert to string
            decrypted_str = decrypted.decode()
            
            # Parse as JSON if requested
            if as_json:
                return json.loads(decrypted_str)
            
            return decrypted_str
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    @staticmethod
    def encrypt_file(file_path: str, output_path: Optional[str] = None) -> str:
        """
        Encrypt a file.
        
        Args:
            file_path: Path to file to encrypt
            output_path: Path for encrypted file (default: file_path.enc)
            
        Returns:
            Path to encrypted file
        """
        try:
            if output_path is None:
                output_path = file_path + '.enc'
            
            # Read file
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # Encrypt
            encrypted = cipher_suite.encrypt(data)
            
            # Write encrypted file
            with open(output_path, 'wb') as f:
                f.write(encrypted)
            
            logger.info(f"File encrypted: {file_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"File encryption failed: {e}")
            raise
    
    @staticmethod
    def decrypt_file(encrypted_path: str, output_path: Optional[str] = None) -> str:
        """
        Decrypt a file.
        
        Args:
            encrypted_path: Path to encrypted file
            output_path: Path for decrypted file (default: removes .enc extension)
            
        Returns:
            Path to decrypted file
        """
        try:
            if output_path is None:
                if encrypted_path.endswith('.enc'):
                    output_path = encrypted_path[:-4]
                else:
                    output_path = encrypted_path + '.dec'
            
            # Read encrypted file
            with open(encrypted_path, 'rb') as f:
                encrypted_data = f.read()
            
            # Decrypt
            decrypted = cipher_suite.decrypt(encrypted_data)
            
            # Write decrypted file
            with open(output_path, 'wb') as f:
                f.write(decrypted)
            
            logger.info(f"File decrypted: {encrypted_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"File decryption failed: {e}")
            raise
    
    @staticmethod
    def encrypt_field(field_value: str) -> str:
        """
        Encrypt a single field value (e.g., for database storage).
        
        Args:
            field_value: Value to encrypt
            
        Returns:
            Encrypted value with prefix
        """
        encrypted = EncryptionManager.encrypt(field_value)
        return f"ENC:{encrypted}"
    
    @staticmethod
    def decrypt_field(field_value: str) -> str:
        """
        Decrypt a single field value.
        
        Args:
            field_value: Encrypted value with prefix
            
        Returns:
            Decrypted value
        """
        if not field_value.startswith("ENC:"):
            # Not encrypted, return as-is
            return field_value
        
        encrypted_part = field_value[4:]  # Remove "ENC:" prefix
        return EncryptionManager.decrypt(encrypted_part)

class SensitiveDataHandler:
    """Handler for sensitive data operations."""
    
    @staticmethod
    def mask_sensitive_data(data: dict, fields_to_mask: list) -> dict:
        """
        Mask sensitive fields in a dictionary.
        
        Args:
            data: Dictionary containing potentially sensitive data
            fields_to_mask: List of field names to mask
            
        Returns:
            Dictionary with masked fields
        """
        masked_data = data.copy()
        
        for field in fields_to_mask:
            if field in masked_data and masked_data[field]:
                # Show only first 4 and last 4 characters
                value = str(masked_data[field])
                if len(value) > 8:
                    masked_data[field] = value[:4] + "****" + value[-4:]
                else:
                    masked_data[field] = "****"
        
        return masked_data
    
    @staticmethod
    def encrypt_sensitive_fields(data: dict, fields_to_encrypt: list) -> dict:
        """
        Encrypt sensitive fields in a dictionary.
        
        Args:
            data: Dictionary containing sensitive data
            fields_to_encrypt: List of field names to encrypt
            
        Returns:
            Dictionary with encrypted fields
        """
        encrypted_data = data.copy()
        
        for field in fields_to_encrypt:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = EncryptionManager.encrypt_field(
                    str(encrypted_data[field])
                )
        
        return encrypted_data
    
    @staticmethod
    def decrypt_sensitive_fields(data: dict, fields_to_decrypt: list) -> dict:
        """
        Decrypt sensitive fields in a dictionary.
        
        Args:
            data: Dictionary containing encrypted data
            fields_to_decrypt: List of field names to decrypt
            
        Returns:
            Dictionary with decrypted fields
        """
        decrypted_data = data.copy()
        
        for field in fields_to_decrypt:
            if field in decrypted_data and decrypted_data[field]:
                try:
                    decrypted_data[field] = EncryptionManager.decrypt_field(
                        str(decrypted_data[field])
                    )
                except Exception as e:
                    logger.warning(f"Failed to decrypt field {field}: {e}")
                    # Keep encrypted value if decryption fails
                    pass
        
        return decrypted_data

# Database encryption helpers
def encrypt_database_value(value: str) -> str:
    """Encrypt a value for database storage."""
    return EncryptionManager.encrypt_field(value)

def decrypt_database_value(encrypted_value: str) -> str:
    """Decrypt a value from database storage."""
    return EncryptionManager.decrypt_field(encrypted_value)

def encrypt_config_value(config_key: str, config_value: str) -> str:
    """
    Encrypt a configuration value.
    
    Args:
        config_key: Configuration key (to determine if encryption is needed)
        config_value: Configuration value to encrypt
        
    Returns:
        Encrypted value if key is sensitive, otherwise original value
    """
    sensitive_keys = [
        'password', 'secret', 'key', 'token', 'api_key', 'private',
        'credential', 'auth', 'certificate'
    ]
    
    if any(sensitive in config_key.lower() for sensitive in sensitive_keys):
        return EncryptionManager.encrypt_field(config_value)
    
    return config_value

def decrypt_config_value(config_key: str, encrypted_value: str) -> str:
    """
    Decrypt a configuration value.
    
    Args:
        config_key: Configuration key (to determine if decryption is needed)
        encrypted_value: Encrypted configuration value
        
    Returns:
        Decrypted value if key is sensitive, otherwise original value
    """
    sensitive_keys = [
        'password', 'secret', 'key', 'token', 'api_key', 'private',
        'credential', 'auth', 'certificate'
    ]
    
    if any(sensitive in config_key.lower() for sensitive in sensitive_keys):
        try:
            return EncryptionManager.decrypt_field(encrypted_value)
        except Exception as e:
            logger.warning(f"Failed to decrypt config value for {config_key}: {e}")
            return encrypted_value
    
    return encrypted_value

# Environment variable encryption
def encrypt_env_var(var_name: str, var_value: str) -> str:
    """Encrypt an environment variable value."""
    return encrypt_config_value(var_name, var_value)

def decrypt_env_var(var_name: str, encrypted_value: str) -> str:
    """Decrypt an environment variable value."""
    return decrypt_config_value(var_name, encrypted_value)
