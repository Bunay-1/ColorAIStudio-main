"""
Multi-Factor Authentication Service for ICAP Enterprise
======================================================
TOTP-based MFA implementation with backup codes and recovery options.
"""

import pyotp
import qrcode
import io
import base64
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import sqlite3
import os
import secrets

logger = logging.getLogger("MFA_Service")

class MFAStatus(str, Enum):
    """MFA status."""
    DISABLED = "disabled"
    ENABLED = "enabled"
    ENFORCED = "enforced"

class MFAStatus(str, Enum):
    """MFA method status."""
    ACTIVE = "active"
    INACTIVE = "inactive"

class MFAMethod(str, Enum):
    """MFA methods."""
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    BACKUP_CODES = "backup_codes"

@dataclass
class MFASetup:
    """MFA setup data."""
    user_id: str
    secret: str
    qr_code: str
    backup_codes: List[str]
    created_at: str
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

@dataclass
class MFAVerification:
    """MFA verification result."""
    success: bool
    method: MFAMethod
    verified_at: str
    user_id: str
    
    def __post_init__(self):
        if self.verified_at is None:
            self.verified_at = datetime.now().isoformat()

class MFAService:
    """Main MFA service for ICAP Enterprise."""
    
    def __init__(self, db_path: str = None):
        """Initialize MFA service."""
        self.db_path = db_path or os.path.join(os.path.dirname(__file__), "..", "icap.db")
        self._init_database()
    
    def _init_database(self):
        """Initialize MFA database tables."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # MFA secrets table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mfa_secrets (
                    user_id TEXT PRIMARY KEY,
                    secret TEXT NOT NULL,
                    method TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    enabled_at TEXT,
                    last_verified TEXT
                )
            ''')
            
            # Backup codes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mfa_backup_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    code TEXT NOT NULL,
                    used BOOLEAN DEFAULT FALSE,
                    used_at TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES mfa_secrets (user_id)
                )
            ''')
            
            # MFA verification logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mfa_verification_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    method TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    verified_at TEXT NOT NULL
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("MFA database initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize MFA database: {e}")
    
    def generate_secret(self) -> str:
        """Generate a new TOTP secret."""
        return pyotp.random_base32()
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes for MFA recovery."""
        return [secrets.token_hex(4).upper() for _ in range(count)]
    
    def generate_qr_code(self, user_id: str, secret: str, issuer: str = "ICAP Enterprise") -> str:
        """
        Generate QR code for TOTP setup.
        
        Args:
            user_id: User ID
            secret: TOTP secret
            issuer: Issuer name
        
        Returns:
            Base64 encoded QR code image
        """
        try:
            totp = pyotp.TOTP(secret)
            provisioning_uri = totp.provisioning_uri(
                name=user_id,
                issuer_name=issuer
            )
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            img_io = io.BytesIO()
            img.save(img_io, 'PNG')
            img_io.seek(0)
            qr_base64 = base64.b64encode(img_io.getvalue()).decode()
            
            return f"data:image/png;base64,{qr_base64}"
            
        except Exception as e:
            logger.error(f"Failed to generate QR code: {e}")
            raise
    
    def setup_mfa(self, user_id: str) -> MFASetup:
        """
        Set up MFA for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            MFA setup data with secret and QR code
        """
        try:
            # Generate secret and backup codes
            secret = self.generate_secret()
            backup_codes = self.generate_backup_codes()
            
            # Generate QR code
            qr_code = self.generate_qr_code(user_id, secret)
            
            # Store backup codes
            self._store_backup_codes(user_id, backup_codes)
            
            setup = MFASetup(
                user_id=user_id,
                secret=secret,
                qr_code=qr_code,
                backup_codes=backup_codes,
                created_at=datetime.now().isoformat()
            )
            
            logger.info(f"MFA setup initiated for user: {user_id}")
            return setup
            
        except Exception as e:
            logger.error(f"Failed to setup MFA: {e}")
            raise
    
    def enable_mfa(self, user_id: str, secret: str, verification_code: str) -> bool:
        """
        Enable MFA for a user after verification.
        
        Args:
            user_id: User ID
            secret: TOTP secret
            verification_code: Verification code from authenticator app
        
        Returns:
            True if enabled successfully
        """
        try:
            # Verify the code
            if not self.verify_totp(secret, verification_code):
                logger.warning(f"Invalid verification code for user: {user_id}")
                return False
            
            # Store MFA secret
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO mfa_secrets
                (user_id, secret, method, status, enabled_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, secret, MFAMethod.TOTP.value, MFAStatus.ACTIVE.value, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            logger.info(f"MFA enabled for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enable MFA: {e}")
            return False
    
    def disable_mfa(self, user_id: str) -> bool:
        """
        Disable MFA for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            True if disabled successfully
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM mfa_secrets WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM mfa_backup_codes WHERE user_id = ?', (user_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"MFA disabled for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disable MFA: {e}")
            return False
    
    def verify_totp(self, secret: str, code: str, valid_window: int = 1) -> bool:
        """
        Verify TOTP code.
        
        Args:
            secret: TOTP secret
            code: Code to verify
            valid_window: Number of time windows to check (default: 1)
        
        Returns:
            True if code is valid
        """
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(code, valid_window=valid_window)
        except Exception as e:
            logger.error(f"Failed to verify TOTP: {e}")
            return False
    
    def verify_mfa(
        self,
        user_id: str,
        code: str,
        method: MFAMethod = MFAMethod.TOTP,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> MFAVerification:
        """
        Verify MFA code for a user.
        
        Args:
            user_id: User ID
            code: Code to verify
            method: MFA method
            ip_address: IP address for logging
            user_agent: User agent for logging
        
        Returns:
            Verification result
        """
        try:
            success = False
            
            if method == MFAMethod.TOTP:
                # Get user's secret
                secret = self._get_user_secret(user_id)
                if secret:
                    success = self.verify_totp(secret, code)
            
            elif method == MFAMethod.BACKUP_CODES:
                success = self._verify_backup_code(user_id, code)
            
            # Log verification attempt
            self._log_verification(
                user_id=user_id,
                method=method,
                success=success,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Update last verified time if successful
            if success:
                self._update_last_verified(user_id)
            
            verification = MFAVerification(
                success=success,
                method=method,
                verified_at=datetime.now().isoformat(),
                user_id=user_id
            )
            
            logger.info(f"MFA verification for user {user_id}: {success}")
            return verification
            
        except Exception as e:
            logger.error(f"Failed to verify MFA: {e}")
            return MFAVerification(
                success=False,
                method=method,
                verified_at=datetime.now().isoformat(),
                user_id=user_id
            )
    
    def _get_user_secret(self, user_id: str) -> Optional[str]:
        """Get user's MFA secret."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT secret FROM mfa_secrets WHERE user_id = ? AND status = ?', (user_id, MFAStatus.ACTIVE.value))
            row = cursor.fetchone()
            
            conn.close()
            
            return row[0] if row else None
            
        except Exception as e:
            logger.error(f"Failed to get user secret: {e}")
            return None
    
    def _store_backup_codes(self, user_id: str, codes: List[str]):
        """Store backup codes for a user."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for code in codes:
                cursor.execute('''
                    INSERT INTO mfa_backup_codes (user_id, code, created_at)
                    VALUES (?, ?, ?)
                ''', (user_id, code, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store backup codes: {e}")
    
    def _verify_backup_code(self, user_id: str, code: str) -> bool:
        """Verify and mark backup code as used."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id FROM mfa_backup_codes
                WHERE user_id = ? AND code = ? AND used = FALSE
                LIMIT 1
            ''', (user_id, code.upper()))
            
            row = cursor.fetchone()
            
            if row:
                # Mark as used
                cursor.execute('''
                    UPDATE mfa_backup_codes
                    SET used = TRUE, used_at = ?
                    WHERE id = ?
                ''', (datetime.now().isoformat(), row[0]))
                
                conn.commit()
                conn.close()
                return True
            
            conn.close()
            return False
            
        except Exception as e:
            logger.error(f"Failed to verify backup code: {e}")
            return False
    
    def _log_verification(
        self,
        user_id: str,
        method: MFAMethod,
        success: bool,
        ip_address: Optional[str],
        user_agent: Optional[str]
    ):
        """Log MFA verification attempt."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO mfa_verification_logs
                (user_id, method, success, ip_address, user_agent, verified_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, method.value, success, ip_address, user_agent, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to log verification: {e}")
    
    def _update_last_verified(self, user_id: str):
        """Update last verified time for user."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE mfa_secrets
                SET last_verified = ?
                WHERE user_id = ?
            ''', (datetime.now().isoformat(), user_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to update last verified: {e}")
    
    def is_mfa_enabled(self, user_id: str) -> bool:
        """Check if MFA is enabled for a user."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM mfa_secrets WHERE user_id = ? AND status = ?', (user_id, MFAStatus.ACTIVE.value))
            count = cursor.fetchone()[0]
            
            conn.close()
            
            return count > 0
            
        except Exception as e:
            logger.error(f"Failed to check MFA status: {e}")
            return False
    
    def get_remaining_backup_codes(self, user_id: str) -> List[str]:
        """Get remaining unused backup codes for a user."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT code FROM mfa_backup_codes
                WHERE user_id = ? AND used = FALSE
            ''', (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [row[0] for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get backup codes: {e}")
            return []
    
    def regenerate_backup_codes(self, user_id: str) -> List[str]:
        """Regenerate backup codes for a user."""
        try:
            # Delete old backup codes
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM mfa_backup_codes WHERE user_id = ?', (user_id,))
            
            # Generate new codes
            new_codes = self.generate_backup_codes()
            
            # Store new codes
            for code in new_codes:
                cursor.execute('''
                    INSERT INTO mfa_backup_codes (user_id, code, created_at)
                    VALUES (?, ?, ?)
                ''', (user_id, code, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Backup codes regenerated for user: {user_id}")
            return new_codes
            
        except Exception as e:
            logger.error(f"Failed to regenerate backup codes: {e}")
            return []

# Global MFA service instance
mfa_service = MFAService()
