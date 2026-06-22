"""
Unit tests for Export/Import Service
"""

import pytest
from unittest.mock import Mock, patch
from utils.export_import_service import ExportImportService, DataFormat, DataType


@pytest.fixture
def export_import_service():
    """Fixture for ExportImportService instance"""
    return ExportImportService()


@pytest.fixture
def mock_database():
    """Mock database connection"""
    with patch('utils.export_import_service.Database') as mock:
        yield mock.return_value


class TestExportImportService:
    """Test cases for ExportImportService"""

    def test_export_users_json(self, export_import_service, mock_database):
        """Test exporting users to JSON format"""
        mock_database.query.return_value = [
            {"id": 1, "username": "user1", "email": "user1@test.com"},
            {"id": 2, "username": "user2", "email": "user2@test.com"}
        ]
        
        result = export_import_service.export_data(
            data_type=DataType.USERS,
            format=DataFormat.JSON,
            filters={}
        )
        
        assert result["data_type"] == DataType.USERS
        assert result["format"] == DataFormat.JSON
        assert result["record_count"] == 2
        assert "data" in result

    def test_export_users_csv(self, export_import_service, mock_database):
        """Test exporting users to CSV format"""
        mock_database.query.return_value = [
            {"id": 1, "username": "user1", "email": "user1@test.com"}
        ]
        
        result = export_import_service.export_data(
            data_type=DataType.USERS,
            format=DataFormat.CSV,
            filters={}
        )
        
        assert result["data_type"] == DataType.USERS
        assert result["format"] == DataFormat.CSV
        assert result["record_count"] == 1

    def test_export_tenants(self, export_import_service, mock_database):
        """Test exporting tenants"""
        mock_database.query.return_value = [
            {"id": "tenant1", "name": "Company A", "max_users": 50}
        ]
        
        result = export_import_service.export_data(
            data_type=DataType.TENANTS,
            format=DataFormat.JSON,
            filters={}
        )
        
        assert result["data_type"] == DataType.TENANTS
        assert result["record_count"] == 1

    def test_export_measurements(self, export_import_service, mock_database):
        """Test exporting measurements"""
        mock_database.query.return_value = [
            {"id": 1, "batch_id": "batch_001", "delta_e": 1.5}
        ]
        
        result = export_import_service.export_data(
            data_type=DataType.MEASUREMENTS,
            format=DataFormat.JSON,
            filters={"batch_id": "batch_001"}
        )
        
        assert result["data_type"] == DataType.MEASUREMENTS
        assert result["record_count"] == 1

    def test_export_audit_logs(self, export_import_service, mock_database):
        """Test exporting audit logs"""
        mock_database.query.return_value = [
            {"id": 1, "user_id": "user1", "action": "login", "timestamp": "2026-06-20"}
        ]
        
        result = export_import_service.export_data(
            data_type=DataType.AUDIT_LOGS,
            format=DataFormat.JSON,
            filters={}
        )
        
        assert result["data_type"] == DataType.AUDIT_LOGS
        assert result["record_count"] == 1

    def test_import_users_json(self, export_import_service, mock_database):
        """Test importing users from JSON format"""
        data = [
            {"username": "new_user1", "email": "new1@test.com"},
            {"username": "new_user2", "email": "new2@test.com"}
        ]
        
        mock_database.execute.return_value = True
        
        result = export_import_service.import_data(
            data_type=DataType.USERS,
            format=DataFormat.JSON,
            data=data,
            overwrite=False
        )
        
        assert result["success"] is True
        assert result["imported_count"] == 2
        assert result["skipped_count"] == 0

    def test_import_users_csv(self, export_import_service, mock_database):
        """Test importing users from CSV format"""
        csv_data = "username,email\nnew_user1,new1@test.com\nnew_user2,new2@test.com"
        
        mock_database.execute.return_value = True
        
        result = export_import_service.import_data(
            data_type=DataType.USERS,
            format=DataFormat.CSV,
            data=csv_data,
            overwrite=False
        )
        
        assert result["success"] is True
        assert result["imported_count"] == 2

    def test_import_with_overwrite(self, export_import_service, mock_database):
        """Test importing with overwrite enabled"""
        data = [{"username": "existing_user", "email": "updated@test.com"}]
        
        mock_database.execute.return_value = True
        
        result = export_import_service.import_data(
            data_type=DataType.USERS,
            format=DataFormat.JSON,
            data=data,
            overwrite=True
        )
        
        assert result["success"] is True
        assert result["updated_count"] == 1

    def test_import_validation_error(self, export_import_service):
        """Test importing with validation error"""
        data = [{"username": "", "email": "invalid"}]  # Invalid data
        
        result = export_import_service.import_data(
            data_type=DataType.USERS,
            format=DataFormat.JSON,
            data=data,
            overwrite=False
        )
        
        assert result["success"] is False
        assert "errors" in result

    def test_get_available_data_types(self, export_import_service):
        """Test getting available data types"""
        types = export_import_service.get_available_data_types()
        
        assert DataType.USERS in types
        assert DataType.TENANTS in types
        assert DataType.MEASUREMENTS in types
        assert DataType.AUDIT_LOGS in types

    def test_get_available_formats(self, export_import_service):
        """Test getting available formats"""
        formats = export_import_service.get_available_formats()
        
        assert DataFormat.JSON in formats
        assert DataFormat.CSV in formats

    def test_validate_export_data(self, export_import_service):
        """Test validating export data"""
        data = [{"id": 1, "username": "user1"}]
        
        is_valid = export_import_service.validate_data(DataType.USERS, data)
        
        assert is_valid is True

    def test_validate_export_data_invalid(self, export_import_service):
        """Test validating invalid export data"""
        data = [{"invalid_field": "value"}]
        
        is_valid = export_import_service.validate_data(DataType.USERS, data)
        
        assert is_valid is False

    def test_export_with_filters(self, export_import_service, mock_database):
        """Test exporting with filters"""
        mock_database.query.return_value = [
            {"id": 1, "username": "user1", "role": "ADMIN"}
        ]
        
        result = export_import_service.export_data(
            data_type=DataType.USERS,
            format=DataFormat.JSON,
            filters={"role": "ADMIN"}
        )
        
        assert result["record_count"] == 1
        mock_database.query.assert_called_once()

    def test_export_to_file(self, export_import_service, mock_database):
        """Test exporting data to file"""
        mock_database.query.return_value = [{"id": 1, "username": "user1"}]
        
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__ = Mock()
            mock_open.return_value.__exit__ = Mock()
            mock_open.return_value.write = Mock()
            
            result = export_import_service.export_to_file(
                data_type=DataType.USERS,
                format=DataFormat.JSON,
                filename="users_export.json"
            )
            
            assert result["success"] is True
            assert result["filename"] == "users_export.json"

    def test_import_from_file(self, export_import_service, mock_database):
        """Test importing data from file"""
        mock_database.execute.return_value = True
        
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__ = Mock()
            mock_open.return_value.__exit__ = Mock()
            mock_open.return_value.read.return_value = '[{"username":"user1","email":"user1@test.com"}]'
            
            result = export_import_service.import_from_file(
                data_type=DataType.USERS,
                format=DataFormat.JSON,
                filename="users_import.json",
                overwrite=False
            )
            
            assert result["success"] is True
            assert result["imported_count"] == 1

    def test_get_export_history(self, export_import_service, mock_database):
        """Test getting export history"""
        mock_database.query.return_value = [
            {"id": 1, "data_type": "users", "format": "json", "timestamp": "2026-06-20"}
        ]
        
        history = export_import_service.get_export_history()
        
        assert len(history) == 1
        assert history[0]["data_type"] == "users"

    def test_get_import_history(self, export_import_service, mock_database):
        """Test getting import history"""
        mock_database.query.return_value = [
            {"id": 1, "data_type": "users", "format": "json", "timestamp": "2026-06-20"}
        ]
        
        history = export_import_service.get_import_history()
        
        assert len(history) == 1
        assert history[0]["data_type"] == "users"

    def test_schedule_export(self, export_import_service):
        """Test scheduling export"""
        schedule = export_import_service.schedule_export(
            data_type=DataType.USERS,
            format=DataFormat.JSON,
            frequency="daily",
            time="02:00"
        )
        
        assert schedule["data_type"] == DataType.USERS
        assert schedule["frequency"] == "daily"
        assert schedule["time"] == "02:00"

    def test_cancel_scheduled_export(self, export_import_service):
        """Test canceling scheduled export"""
        schedule_id = "schedule_123"
        
        result = export_import_service.cancel_schedule(schedule_id)
        
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
