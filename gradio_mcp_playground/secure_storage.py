"""Secure Storage for Gradio MCP Playground

Provides encrypted storage for API keys and sensitive data.
Uses industry-standard encryption practices with the cryptography library.
"""

import base64
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, List

# Optional imports for encryption
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


class SecureStorage:
    """Secure storage for API keys and sensitive configuration
    
    This class provides encrypted storage for API keys at rest using the
    cryptography library. Keys are stored in an encrypted JSON file in the
    ~/.gradio-mcp/ directory.
    """

    def __init__(self, config_dir: Optional[Path] = None):
        if not HAS_CRYPTOGRAPHY:
            raise ImportError(
                "cryptography package required for secure storage. Install with: pip install cryptography"
            )

        # Use ~/.gradio-mcp/ directory as specified
        if config_dir is None:
            config_dir = Path.home() / ".gradio-mcp"

        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.keys_file = self.config_dir / "api_keys.enc"
        self.salt_file = self.config_dir / "salt.key"

        # Generate or load encryption key
        self._setup_encryption()

    def _setup_encryption(self):
        """Setup encryption key using machine-specific data"""
        # Create a machine-specific salt
        if not self.salt_file.exists():
            salt = os.urandom(16)
            with open(self.salt_file, "wb") as f:
                f.write(salt)
        else:
            with open(self.salt_file, "rb") as f:
                salt = f.read()

        # Generate key from machine-specific data
        machine_id = self._get_machine_id()
        password = machine_id.encode("utf-8")

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        self.cipher = Fernet(key)

    def _get_machine_id(self) -> str:
        """Get a machine-specific identifier"""
        try:
            # Try to get machine ID (works on most systems)
            if os.name == "nt":  # Windows
                import subprocess

                result = subprocess.run(
                    ["wmic", "csproduct", "get", "UUID"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split("\n")
                    if len(lines) > 1:
                        return lines[1].strip()
            else:  # Unix-like
                machine_id_file = Path("/etc/machine-id")
                if machine_id_file.exists():
                    return machine_id_file.read_text().strip()

                # Fallback to other system identifiers
                try:
                    import subprocess

                    result = subprocess.run(["hostid"], capture_output=True, text=True)
                    if result.returncode == 0:
                        return result.stdout.strip()
                except:
                    pass
        except:
            pass

        # Fallback: use home directory path hash (stable per user)
        return hashlib.sha256(str(Path.home()).encode()).hexdigest()[:16]

    def store_key(self, service: str, key_name: str, key_value: str) -> bool:
        """Store an encrypted API key for a service

        Args:
            service: Service name (e.g., 'openai', 'huggingface', 'anthropic')
            key_name: Name of the API key (e.g., 'api_key', 'secret_key')
            key_value: The actual API key value to encrypt and store

        Returns:
            bool: True if successful
        """
        try:
            # Load existing keys
            keys = self._load_keys()

            # Initialize service if it doesn't exist
            if service not in keys:
                keys[service] = {}

            # Encrypt and store new key
            encrypted_key = self.cipher.encrypt(key_value.encode("utf-8"))
            keys[service][key_name] = {
                "value": base64.urlsafe_b64encode(encrypted_key).decode("utf-8"),
                "created_at": self._get_timestamp(),
                "updated_at": self._get_timestamp(),
            }

            # Save back to file
            return self._save_keys(keys)

        except Exception as e:
            print(f"Error storing API key: {e}")
            return False

    def retrieve_key(self, service: str, key_name: str) -> Optional[str]:
        """Retrieve and decrypt an API key for a service

        Args:
            service: Service name (e.g., 'openai', 'huggingface', 'anthropic')
            key_name: Name of the API key to retrieve

        Returns:
            str or None: Decrypted API key if found
        """
        try:
            keys = self._load_keys()

            if service not in keys or key_name not in keys[service]:
                return None

            encrypted_data = base64.urlsafe_b64decode(
                keys[service][key_name]["value"].encode("utf-8")
            )
            decrypted_key = self.cipher.decrypt(encrypted_data)
            return decrypted_key.decode("utf-8")

        except Exception as e:
            print(f"Error retrieving API key: {e}")
            return None

    def delete_key(self, service: str, key_name: Optional[str] = None) -> bool:
        """Delete a stored API key

        Args:
            service: Service name
            key_name: Specific key to delete. If None, deletes all keys for the service

        Returns:
            bool: True if successful
        """
        try:
            keys = self._load_keys()

            if service not in keys:
                return True  # Already doesn't exist

            if key_name is None:
                # Delete all keys for the service
                del keys[service]
            else:
                # Delete specific key
                if key_name in keys[service]:
                    del keys[service][key_name]
                    # If no more keys for this service, remove the service
                    if not keys[service]:
                        del keys[service]

            return self._save_keys(keys)

        except Exception as e:
            print(f"Error deleting API key: {e}")
            return False

    def list_services(self) -> List[str]:
        """List all services with stored API keys

        Returns:
            list: Service names with stored keys
        """
        try:
            keys = self._load_keys()
            return list(keys.keys())
        except:
            return []

    def list_keys(self, service: str) -> List[str]:
        """List all key names for a specific service

        Args:
            service: Service name

        Returns:
            list: Key names for the service
        """
        try:
            keys = self._load_keys()
            if service in keys:
                return list(keys[service].keys())
            return []
        except:
            return []

    def get_all_keys_info(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        """Get metadata about all stored keys (without the actual key values)

        Returns:
            dict: Nested dict of service -> key_name -> metadata
        """
        try:
            keys = self._load_keys()
            info = {}
            for service, service_keys in keys.items():
                info[service] = {}
                for key_name, key_data in service_keys.items():
                    info[service][key_name] = {
                        "created_at": key_data.get("created_at", "unknown"),
                        "updated_at": key_data.get("updated_at", "unknown"),
                        "has_value": True
                    }
            return info
        except:
            return {}

    def clear_all_keys(self) -> bool:
        """Clear all stored API keys

        Returns:
            bool: True if successful
        """
        try:
            if self.keys_file.exists():
                self.keys_file.unlink()
            return True
        except Exception as e:
            print(f"Error clearing API keys: {e}")
            return False

    def _load_keys(self) -> Dict[str, Any]:
        """Load API keys from encrypted file"""
        if not self.keys_file.exists():
            return {}

        try:
            with open(self.keys_file, "rb") as f:
                encrypted_data = f.read()

            decrypted_data = self.cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode("utf-8"))

        except Exception:
            # If we can't decrypt (corruption, key change, etc.), start fresh
            return {}

    def _save_keys(self, keys: Dict[str, Any]) -> bool:
        """Save API keys to encrypted file"""
        try:
            data = json.dumps(keys, indent=2)
            encrypted_data = self.cipher.encrypt(data.encode("utf-8"))

            with open(self.keys_file, "wb") as f:
                f.write(encrypted_data)

            # Set restrictive permissions (owner only)
            if os.name != "nt":  # Unix-like systems
                os.chmod(self.keys_file, 0o600)

            return True

        except Exception as e:
            print(f"Error saving API keys: {e}")
            return False

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime

        return datetime.now().isoformat()

    def get_key_info(self, service: str, key_name: str) -> Optional[Dict[str, str]]:
        """Get metadata about a stored API key (without the key value itself)

        Args:
            service: Service name
            key_name: Key name

        Returns:
            dict or None: Key metadata
        """
        try:
            keys = self._load_keys()
            if service in keys and key_name in keys[service]:
                info = keys[service][key_name].copy()
                info.pop("value", None)  # Remove actual key value
                info["service"] = service
                info["key_name"] = key_name
                info["has_value"] = True
                return info
            return None
        except:
            return None

    def update_key(self, service: str, key_name: str, key_value: str) -> bool:
        """Update an existing API key

        Args:
            service: Service name
            key_name: Name of the API key
            key_value: New API key value

        Returns:
            bool: True if successful
        """
        try:
            keys = self._load_keys()

            if service not in keys or key_name not in keys[service]:
                # Key doesn't exist, create it
                return self.store_key(service, key_name, key_value)

            # Update existing key
            encrypted_key = self.cipher.encrypt(key_value.encode("utf-8"))
            keys[service][key_name]["value"] = base64.urlsafe_b64encode(encrypted_key).decode("utf-8")
            keys[service][key_name]["updated_at"] = self._get_timestamp()

            return self._save_keys(keys)

        except Exception as e:
            print(f"Error updating API key: {e}")
            return False

    # Integration methods for MCP server installation
    def store_server_keys(self, server_name: str, api_keys: Dict[str, str]) -> bool:
        """Store multiple API keys for an MCP server during installation

        Args:
            server_name: Name of the MCP server
            api_keys: Dictionary of key_name -> key_value pairs

        Returns:
            bool: True if all keys stored successfully
        """
        success = True
        for key_name, key_value in api_keys.items():
            if not self.store_key(server_name, key_name, key_value):
                success = False
        return success

    def retrieve_server_keys(self, server_name: str) -> Dict[str, str]:
        """Retrieve all API keys for an MCP server

        Args:
            server_name: Name of the MCP server

        Returns:
            dict: Dictionary of key_name -> key_value pairs
        """
        keys = {}
        for key_name in self.list_keys(server_name):
            key_value = self.retrieve_key(server_name, key_name)
            if key_value:
                keys[key_name] = key_value
        return keys

    def has_server_keys(self, server_name: str, required_keys: List[str]) -> bool:
        """Check if an MCP server has all required API keys stored

        Args:
            server_name: Name of the MCP server
            required_keys: List of required key names

        Returns:
            bool: True if all required keys are present
        """
        stored_keys = self.list_keys(server_name)
        return all(key in stored_keys for key in required_keys)

    def export_keys(self, password: str) -> Optional[str]:
        """Export all keys encrypted with a password for backup

        Args:
            password: Password to encrypt the export

        Returns:
            str or None: Base64 encoded encrypted export
        """
        try:
            # Generate key from password
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))
            cipher = Fernet(key)

            # Export all keys
            keys = self._load_keys()
            export_data = {
                "version": 1,
                "keys": keys,
                "exported_at": self._get_timestamp()
            }

            # Encrypt and encode
            data = json.dumps(export_data)
            encrypted = cipher.encrypt(data.encode("utf-8"))
            
            # Include salt in the export
            export = salt + encrypted
            return base64.urlsafe_b64encode(export).decode("utf-8")

        except Exception as e:
            print(f"Error exporting keys: {e}")
            return None

    def import_keys(self, export_data: str, password: str) -> bool:
        """Import keys from an encrypted export

        Args:
            export_data: Base64 encoded encrypted export
            password: Password to decrypt the export

        Returns:
            bool: True if successful
        """
        try:
            # Decode export
            export = base64.urlsafe_b64decode(export_data.encode("utf-8"))
            
            # Extract salt and encrypted data
            salt = export[:16]
            encrypted = export[16:]

            # Generate key from password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))
            cipher = Fernet(key)

            # Decrypt and load
            decrypted = cipher.decrypt(encrypted)
            import_data = json.loads(decrypted.decode("utf-8"))

            # Merge with existing keys
            current_keys = self._load_keys()
            imported_keys = import_data.get("keys", {})
            
            for service, service_keys in imported_keys.items():
                if service not in current_keys:
                    current_keys[service] = {}
                current_keys[service].update(service_keys)

            return self._save_keys(current_keys)

        except Exception as e:
            print(f"Error importing keys: {e}")
            return False


# Backward compatibility aliases
class SecureTokenStorage(SecureStorage):
    """Alias for backward compatibility"""
    
    def save_token(self, service: str, token: str) -> bool:
        """Backward compatibility method"""
        return self.store_key(service, "api_token", token)
    
    def load_token(self, service: str) -> Optional[str]:
        """Backward compatibility method"""
        return self.retrieve_key(service, "api_token")
    
    def delete_token(self, service: str) -> bool:
        """Backward compatibility method"""
        return self.delete_key(service, "api_token")
    
    def clear_all_tokens(self) -> bool:
        """Backward compatibility method"""
        return self.clear_all_keys()


def get_secure_storage() -> Optional[SecureStorage]:
    """Get secure storage instance if cryptography is available

    Returns:
        SecureStorage or None: Storage instance if available
    """
    if not HAS_CRYPTOGRAPHY:
        return None

    try:
        return SecureStorage()
    except Exception as e:
        print(f"Could not initialize secure storage: {e}")
        return None
