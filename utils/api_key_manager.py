"""
API Key Rotation Manager for ICAP Platform v8.10.0
==================================================
Secure API key generation, validation, and rotation
"""

import secrets
import hashlib
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("ICAP_APIKeyManager")


class APIKeyManager:
    """Manager for API key lifecycle including rotation"""
    
    def __init__(self, db_path: str = None):
        """Initialize API key manager with database connection"""
        if db_path is None:
            db_path = os.environ.get("ICAP_DB_PATH", "icap.db")
        
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize database tables for API keys"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create api_keys table if not exists
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS api_keys (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key_id TEXT UNIQUE NOT NULL,
                        key_hash TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        tenant_id TEXT,
                        is_active BOOLEAN DEFAULT TRUE,
                        expires_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_used_at TIMESTAMP
                    )
                ''')
                
                # Create indexes
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_api_keys_key_id 
                    ON api_keys(key_id)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_api_keys_user_id 
                    ON api_keys(user_id)
                ''')
                
                conn.commit()
                logger.info("API keys database initialized")
                
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def generate_api_key(self, user_id: str, tenant_id: str = None, 
                        expires_days: int = 90) -> Dict[str, str]:
        """Generate a new API key for a user
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier (optional)
            expires_days: Days until key expiration (default: 90)
            
        Returns:
            Dictionary with key_id and api_key
        """
        try:
            # Generate secure random key
            api_key = f"icap_{secrets.token_urlsafe(32)}"
            key_id = secrets.token_hex(16)
            
            # Hash the key for storage
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Calculate expiration
            expires_at = datetime.now() + timedelta(days=expires_days)
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO api_keys (key_id, key_hash, user_id, tenant_id, expires_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (key_id, key_hash, user_id, tenant_id, expires_at.isoformat()))
                conn.commit()
            
            logger.info(f"Generated API key for user {user_id}")
            
            return {
                "key_id": key_id,
                "api_key": api_key,
                "expires_at": expires_at.isoformat()
            }
            
        except sqlite3.Error as e:
            logger.error(f"API key generation error: {e}")
            raise
    
    def validate_api_key(self, api_key: str) -> Optional[Dict[str, any]]:
        """Validate an API key and return user info
        
        Args:
            api_key: The API key to validate
            
        Returns:
            Dictionary with user info if valid, None otherwise
        """
        try:
            # Hash the provided key
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT key_id, user_id, tenant_id, is_active, expires_at
                    FROM api_keys
                    WHERE key_hash = ? AND is_active = TRUE
                ''', (key_hash,))
                
                result = cursor.fetchone()
                
                if result is None:
                    logger.warning("Invalid API key provided")
                    return None
                
                key_id, user_id, tenant_id, is_active, expires_at = result
                
                # Check expiration
                if expires_at:
                    expires_dt = datetime.fromisoformat(expires_at)
                    if datetime.now() > expires_dt:
                        logger.warning(f"Expired API key used: {key_id}")
                        self.revoke_api_key(key_id)
                        return None
                
                # Update last used timestamp
                cursor.execute('''
                    UPDATE api_keys
                    SET last_used_at = CURRENT_TIMESTAMP
                    WHERE key_id = ?
                ''', (key_id,))
                conn.commit()
                
                return {
                    "key_id": key_id,
                    "user_id": user_id,
                    "tenant_id": tenant_id
                }
                
        except sqlite3.Error as e:
            logger.error(f"API key validation error: {e}")
            return None
    
    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key
        
        Args:
            key_id: The key ID to revoke
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE api_keys
                    SET is_active = FALSE
                    WHERE key_id = ?
                ''', (key_id,))
                conn.commit()
                
                logger.info(f"Revoked API key: {key_id}")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"API key revocation error: {e}")
            return False
    
    def rotate_api_key(self, old_key_id: str, user_id: str, 
                     tenant_id: str = None, expires_days: int = 90) -> Dict[str, str]:
        """Rotate an existing API key (create new, revoke old)
        
        Args:
            old_key_id: The old key ID to replace
            user_id: User identifier
            tenant_id: Tenant identifier (optional)
            expires_days: Days until new key expiration (default: 90)
            
        Returns:
            Dictionary with new key_id and api_key
        """
        try:
            # Revoke old key
            self.revoke_api_key(old_key_id)
            
            # Generate new key
            new_key = self.generate_api_key(user_id, tenant_id, expires_days)
            
            logger.info(f"Rotated API key for user {user_id}")
            return new_key
            
        except Exception as e:
            logger.error(f"API key rotation error: {e}")
            raise
    
    def list_user_keys(self, user_id: str) -> List[Dict[str, any]]:
        """List all API keys for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            List of API key information
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT key_id, tenant_id, is_active, expires_at, created_at, last_used_at
                    FROM api_keys
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                ''', (user_id,))
                
                results = cursor.fetchall()
                
                return [
                    {
                        "key_id": row[0],
                        "tenant_id": row[1],
                        "is_active": row[2],
                        "expires_at": row[3],
                        "created_at": row[4],
                        "last_used_at": row[5]
                    }
                    for row in results
                ]
                
        except sqlite3.Error as e:
            logger.error(f"List user keys error: {e}")
            return []
    
    def cleanup_expired_keys(self) -> int:
        """Clean up expired API keys
        
        Returns:
            Number of keys cleaned up
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE api_keys
                    SET is_active = FALSE
                    WHERE expires_at < CURRENT_TIMESTAMP AND is_active = TRUE
                ''')
                count = cursor.rowcount
                conn.commit()
                
                if count > 0:
                    logger.info(f"Cleaned up {count} expired API keys")
                
                return count
                
        except sqlite3.Error as e:
            logger.error(f"Cleanup expired keys error: {e}")
            return 0


# Global API key manager instance
api_key_manager = APIKeyManager()
