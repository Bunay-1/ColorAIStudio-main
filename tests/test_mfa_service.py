"""
Unit tests for MFA Service
"""

import pytest
from unittest.mock import Mock, patch
from utils.mfa_service import MFAService, MFAMethod, MFAStatus


@pytest.fixture
def mfa_service():
    """Fixture for MFAService instance"""
    return MFAService()


@pytest.fixture
def mock_pyotp():
    """Mock pyotp library"""
    with patch('utils.mfa_service.pyotp') as mock:
        yield mock


@pytest.fixture
def mock_qrcode():
    """Mock qrcode library"""
    with patch('utils.mfa_service.qrcode') as mock:
        yield mock


class TestMFAService:
    """Test cases for MFAService"""

    def test_setup_mfa(self, mfa_service, mock_pyotp):
        """Test MFA setup"""
        mock_pyotp.random_base32.return_value = "JBSWY3DPEHPK3PXP"
        mock_pyotp.TOTP.return_value.provisioning_uri.return_value = "otpauth://totp/test"
        
        setup_data = mfa_service.setup_mfa(user_id="user_123", username="test_user")
        
        assert setup_data["secret"] == "JBSWY3DPEHPK3PXP"
        assert setup_data["provisioning_uri"] == "otpauth://totp/test"
        assert setup_data["qr_code"] is not None
        assert setup_data["backup_codes"] is not None
        assert len(setup_data["backup_codes"]) == 10

    def test_enable_mfa(self, mfa_service, mock_pyotp):
        """Test enabling MFA"""
        mock_pyotp.TOTP.return_value.verify.return_value = True
        
        result = mfa_service.enable_mfa(
            user_id="user_123",
            secret="JBSWY3DPEHPK3PXP",
            verification_code="123456"
        )
        
        assert result["success"] is True
        assert result["status"] == MFAStatus.ENABLED

    def test_enable_mfa_invalid_code(self, mfa_service, mock_pyotp):
        """Test enabling MFA with invalid code"""
        mock_pyotp.TOTP.return_value.verify.return_value = False
        
        result = mfa_service.enable_mfa(
            user_id="user_123",
            secret="JBSWY3DPEHPK3PXP",
            verification_code="000000"
        )
        
        assert result["success"] is False
        assert result["status"] == MFAStatus.FAILED

    def test_verify_mfa_code(self, mfa_service, mock_pyotp):
        """Test verifying MFA code"""
        mock_pyotp.TOTP.return_value.verify.return_value = True
        
        result = mfa_service.verify_code(
            user_id="user_123",
            code="123456",
            method=MFAMethod.TOTP
        )
        
        assert result["valid"] is True
        assert result["method"] == MFAMethod.TOTP

    def test_verify_mfa_code_invalid(self, mfa_service, mock_pyotp):
        """Test verifying invalid MFA code"""
        mock_pyotp.TOTP.return_value.verify.return_value = False
        
        result = mfa_service.verify_code(
            user_id="user_123",
            code="000000",
            method=MFAMethod.TOTP
        )
        
        assert result["valid"] is False

    def test_verify_backup_code(self, mfa_service):
        """Test verifying backup code"""
        backup_codes = ["ABC123", "DEF456", "GHI789"]
        mfa_service.store_backup_codes("user_123", backup_codes)
        
        result = mfa_service.verify_backup_code("user_123", "ABC123")
        
        assert result["valid"] is True
        assert result["code_used"] == "ABC123"

    def test_verify_backup_code_invalid(self, mfa_service):
        """Test verifying invalid backup code"""
        backup_codes = ["ABC123", "DEF456"]
        mfa_service.store_backup_codes("user_123", backup_codes)
        
        result = mfa_service.verify_backup_code("user_123", "INVALID")
        
        assert result["valid"] is False

    def test_disable_mfa(self, mfa_service):
        """Test disabling MFA"""
        result = mfa_service.disable_mfa(user_id="user_123")
        
        assert result["success"] is True
        assert result["status"] == MFAStatus.DISABLED

    def test_get_mfa_status(self, mfa_service):
        """Test getting MFA status"""
        mfa_service.enable_mfa("user_123", "JBSWY3DPEHPK3PXP", "123456")
        
        status = mfa_service.get_status(user_id="user_123")
        
        assert status["enabled"] is True
        assert status["method"] == MFAMethod.TOTP

    def test_regenerate_backup_codes(self, mfa_service):
        """Test regenerating backup codes"""
        new_codes = mfa_service.regenerate_backup_codes(user_id="user_123")
        
        assert len(new_codes) == 10
        assert all(len(code) == 6 for code in new_codes)

    def test_generate_qr_code(self, mfa_service, mock_qrcode):
        """Test generating QR code"""
        mock_qrcode.make.return_value = Mock()
        
        qr_code = mfa_service.generate_qr_code("otpauth://totp/test")
        
        assert qr_code is not None
        mock_qrcode.make.assert_called_once()

    def test_check_mfa_enabled(self, mfa_service):
        """Test checking if MFA is enabled"""
        mfa_service.enable_mfa("user_123", "JBSWY3DPEHPK3PXP", "123456")
        
        is_enabled = mfa_service.is_enabled("user_123")
        
        assert is_enabled is True

    def test_check_mfa_disabled(self, mfa_service):
        """Test checking if MFA is disabled"""
        is_enabled = mfa_service.is_enabled("user_456")
        
        assert is_enabled is False

    def test_get_mfa_statistics(self, mfa_service):
        """Test getting MFA statistics"""
        mfa_service.enable_mfa("user_123", "JBSWY3DPEHPK3PXP", "123456")
        mfa_service.enable_mfa("user_456", "ABCDEF123456", "654321")
        
        stats = mfa_service.get_statistics()
        
        assert stats["total_users_with_mfa"] == 2
        assert stats["method_distribution"][MFAMethod.TOTP] == 2

    def test_validate_secret_format(self, mfa_service):
        """Test validating secret format"""
        valid_secret = "JBSWY3DPEHPK3PXP"
        invalid_secret = "invalid"
        
        assert mfa_service.validate_secret(valid_secret) is True
        assert mfa_service.validate_secret(invalid_secret) is False

    def test_generate_secret(self, mfa_service):
        """Test generating MFA secret"""
        secret = mfa_service.generate_secret()
        
        assert len(secret) == 16
        assert secret.isalnum()

    def test_backup_code_usage_tracking(self, mfa_service):
        """Test tracking backup code usage"""
        backup_codes = ["ABC123", "DEF456"]
        mfa_service.store_backup_codes("user_123", backup_codes)
        
        mfa_service.verify_backup_code("user_123", "ABC123")
        
        remaining_codes = mfa_service.get_remaining_backup_codes("user_123")
        
        assert len(remaining_codes) == 1
        assert "ABC123" not in remaining_codes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
