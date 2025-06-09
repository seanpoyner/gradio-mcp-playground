"""Test secure storage functionality"""

import os
import tempfile
import pytest
from pathlib import Path

from gradio_mcp_playground.secure_storage import (
    SecureStorage,
    SecureTokenStorage,
    get_secure_storage,
    HAS_CRYPTOGRAPHY,
)


@pytest.mark.skipif(not HAS_CRYPTOGRAPHY, reason="cryptography package not installed")
class TestSecureStorage:
    """Test SecureStorage class"""

    @pytest.fixture
    def temp_storage_dir(self):
        """Create a temporary directory for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def storage(self, temp_storage_dir):
        """Create a SecureStorage instance with temp directory"""
        return SecureStorage(config_dir=temp_storage_dir)

    def test_store_and_retrieve_key(self, storage):
        """Test storing and retrieving an API key"""
        service = "test_service"
        key_name = "api_key"
        key_value = "test-api-key-12345"

        # Store key
        assert storage.store_key(service, key_name, key_value)

        # Retrieve key
        retrieved = storage.retrieve_key(service, key_name)
        assert retrieved == key_value

    def test_update_key(self, storage):
        """Test updating an existing key"""
        service = "test_service"
        key_name = "api_key"
        original_value = "original-key"
        new_value = "updated-key"

        # Store original
        storage.store_key(service, key_name, original_value)

        # Update
        assert storage.update_key(service, key_name, new_value)

        # Verify update
        retrieved = storage.retrieve_key(service, key_name)
        assert retrieved == new_value

    def test_delete_key(self, storage):
        """Test deleting a key"""
        service = "test_service"
        key_name = "api_key"
        key_value = "test-key"

        # Store key
        storage.store_key(service, key_name, key_value)

        # Delete specific key
        assert storage.delete_key(service, key_name)

        # Verify deletion
        assert storage.retrieve_key(service, key_name) is None

    def test_delete_service(self, storage):
        """Test deleting all keys for a service"""
        service = "test_service"
        
        # Store multiple keys
        storage.store_key(service, "key1", "value1")
        storage.store_key(service, "key2", "value2")

        # Delete entire service
        assert storage.delete_key(service)

        # Verify all keys are gone
        assert len(storage.list_keys(service)) == 0

    def test_list_services_and_keys(self, storage):
        """Test listing services and keys"""
        # Store keys for multiple services
        storage.store_key("service1", "key1", "value1")
        storage.store_key("service1", "key2", "value2")
        storage.store_key("service2", "key3", "value3")

        # List services
        services = storage.list_services()
        assert set(services) == {"service1", "service2"}

        # List keys for each service
        assert set(storage.list_keys("service1")) == {"key1", "key2"}
        assert set(storage.list_keys("service2")) == {"key3"}

    def test_store_and_retrieve_server_keys(self, storage):
        """Test storing and retrieving multiple keys for a server"""
        server_name = "test_server"
        api_keys = {
            "openai_key": "sk-12345",
            "anthropic_key": "sk-ant-67890",
            "google_key": "AIza-abcdef"
        }

        # Store server keys
        assert storage.store_server_keys(server_name, api_keys)

        # Retrieve server keys
        retrieved = storage.retrieve_server_keys(server_name)
        assert retrieved == api_keys

    def test_has_server_keys(self, storage):
        """Test checking if server has required keys"""
        server_name = "test_server"
        
        # Store some keys
        storage.store_key(server_name, "key1", "value1")
        storage.store_key(server_name, "key2", "value2")

        # Check with all present keys
        assert storage.has_server_keys(server_name, ["key1", "key2"])

        # Check with missing key
        assert not storage.has_server_keys(server_name, ["key1", "key2", "key3"])

    def test_get_key_info(self, storage):
        """Test getting key metadata"""
        service = "test_service"
        key_name = "api_key"
        key_value = "test-key"

        # Store key
        storage.store_key(service, key_name, key_value)

        # Get info
        info = storage.get_key_info(service, key_name)
        assert info is not None
        assert info["service"] == service
        assert info["key_name"] == key_name
        assert info["has_value"] is True
        assert "value" not in info  # Should not expose actual key

    def test_get_all_keys_info(self, storage):
        """Test getting all keys metadata"""
        # Store multiple keys
        storage.store_key("service1", "key1", "value1")
        storage.store_key("service2", "key2", "value2")

        # Get all info
        info = storage.get_all_keys_info()
        assert "service1" in info
        assert "key1" in info["service1"]
        assert info["service1"]["key1"]["has_value"] is True

    def test_export_and_import_keys(self, storage):
        """Test exporting and importing keys"""
        # Store some keys
        storage.store_key("service1", "key1", "value1")
        storage.store_key("service2", "key2", "value2")

        # Export with password
        password = "test-password-123"
        export_data = storage.export_keys(password)
        assert export_data is not None

        # Clear all keys
        storage.clear_all_keys()
        assert len(storage.list_services()) == 0

        # Import back
        assert storage.import_keys(export_data, password)

        # Verify keys are restored
        assert storage.retrieve_key("service1", "key1") == "value1"
        assert storage.retrieve_key("service2", "key2") == "value2"

    def test_import_with_wrong_password(self, storage):
        """Test importing with wrong password fails gracefully"""
        # Store and export
        storage.store_key("service1", "key1", "value1")
        export_data = storage.export_keys("correct-password")

        # Try to import with wrong password
        assert not storage.import_keys(export_data, "wrong-password")

    def test_clear_all_keys(self, storage):
        """Test clearing all keys"""
        # Store multiple keys
        storage.store_key("service1", "key1", "value1")
        storage.store_key("service2", "key2", "value2")

        # Clear all
        assert storage.clear_all_keys()

        # Verify all gone
        assert len(storage.list_services()) == 0

    def test_backward_compatibility(self, temp_storage_dir):
        """Test backward compatibility with SecureTokenStorage"""
        storage = SecureTokenStorage(config_dir=temp_storage_dir)

        # Test old methods
        assert storage.save_token("huggingface", "hf_12345")
        assert storage.load_token("huggingface") == "hf_12345"
        assert storage.delete_token("huggingface")
        assert storage.load_token("huggingface") is None

    def test_file_permissions(self, storage):
        """Test that encrypted file has restrictive permissions"""
        if os.name == "nt":
            pytest.skip("File permission test not applicable on Windows")

        # Store a key to create the file
        storage.store_key("test", "key", "value")

        # Check file permissions
        keys_file = storage.keys_file
        assert keys_file.exists()
        
        # Get file permissions
        stat_info = os.stat(keys_file)
        mode = stat_info.st_mode & 0o777
        
        # Should be readable/writable by owner only (0o600)
        assert mode == 0o600

    def test_storage_directory_creation(self, temp_storage_dir):
        """Test that storage directory is created with proper structure"""
        # Use a subdirectory that doesn't exist
        new_dir = temp_storage_dir / "nested" / "path"
        storage = SecureStorage(config_dir=new_dir)

        # Directory should be created
        assert new_dir.exists()
        assert new_dir.is_dir()

        # Store a key to ensure everything works
        assert storage.store_key("test", "key", "value")


@pytest.mark.skipif(not HAS_CRYPTOGRAPHY, reason="cryptography package not installed")
def test_get_secure_storage():
    """Test get_secure_storage helper function"""
    storage = get_secure_storage()
    assert storage is not None
    assert isinstance(storage, SecureStorage)


def test_get_secure_storage_without_cryptography(monkeypatch):
    """Test get_secure_storage returns None when cryptography is not available"""
    # Mock HAS_CRYPTOGRAPHY to False
    monkeypatch.setattr("gradio_mcp_playground.secure_storage.HAS_CRYPTOGRAPHY", False)
    
    storage = get_secure_storage()
    assert storage is None