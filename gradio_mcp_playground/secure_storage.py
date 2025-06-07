"""Secure Token Storage for Gradio MCP Playground

Provides encrypted storage for sensitive data like HuggingFace API tokens.
Uses industry-standard encryption practices.
"""

import base64
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

# Optional imports for encryption
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


class SecureTokenStorage:
    """Secure storage for API tokens and sensitive configuration"""

    def __init__(self, config_dir: Optional[Path] = None):
        if not HAS_CRYPTOGRAPHY:
            raise ImportError(
                "cryptography package required for secure token storage. Install with: pip install cryptography"
            )

        # Use user's config directory
        if config_dir is None:
            if os.name == "nt":  # Windows
                config_dir = Path.home() / "AppData" / "Local" / "GradioMCPPlayground"
            else:  # Unix-like
                config_dir = Path.home() / ".config" / "gradio-mcp-playground"

        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.tokens_file = self.config_dir / "tokens.enc"
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

    def save_token(self, service: str, token: str) -> bool:
        """Save an encrypted token for a service

        Args:
            service: Service name (e.g., 'huggingface')
            token: API token to encrypt and store

        Returns:
            bool: True if successful
        """
        try:
            # Load existing tokens
            tokens = self._load_tokens()

            # Encrypt and store new token
            encrypted_token = self.cipher.encrypt(token.encode("utf-8"))
            tokens[service] = {
                "token": base64.urlsafe_b64encode(encrypted_token).decode("utf-8"),
                "created_at": self._get_timestamp(),
            }

            # Save back to file
            return self._save_tokens(tokens)

        except Exception as e:
            print(f"Error saving token: {e}")
            return False

    def load_token(self, service: str) -> Optional[str]:
        """Load and decrypt a token for a service

        Args:
            service: Service name (e.g., 'huggingface')

        Returns:
            str or None: Decrypted token if found
        """
        try:
            tokens = self._load_tokens()

            if service not in tokens:
                return None

            encrypted_data = base64.urlsafe_b64decode(tokens[service]["token"].encode("utf-8"))
            decrypted_token = self.cipher.decrypt(encrypted_data)
            return decrypted_token.decode("utf-8")

        except Exception as e:
            print(f"Error loading token: {e}")
            return None

    def delete_token(self, service: str) -> bool:
        """Delete a stored token

        Args:
            service: Service name to delete

        Returns:
            bool: True if successful
        """
        try:
            tokens = self._load_tokens()

            if service in tokens:
                del tokens[service]
                return self._save_tokens(tokens)

            return True  # Already doesn't exist

        except Exception as e:
            print(f"Error deleting token: {e}")
            return False

    def list_services(self) -> list:
        """List all services with stored tokens

        Returns:
            list: Service names with stored tokens
        """
        try:
            tokens = self._load_tokens()
            return list(tokens.keys())
        except:
            return []

    def clear_all_tokens(self) -> bool:
        """Clear all stored tokens

        Returns:
            bool: True if successful
        """
        try:
            if self.tokens_file.exists():
                self.tokens_file.unlink()
            return True
        except Exception as e:
            print(f"Error clearing tokens: {e}")
            return False

    def _load_tokens(self) -> Dict[str, Any]:
        """Load tokens from encrypted file"""
        if not self.tokens_file.exists():
            return {}

        try:
            with open(self.tokens_file, "rb") as f:
                encrypted_data = f.read()

            decrypted_data = self.cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode("utf-8"))

        except Exception:
            # If we can't decrypt (corruption, key change, etc.), start fresh
            return {}

    def _save_tokens(self, tokens: Dict[str, Any]) -> bool:
        """Save tokens to encrypted file"""
        try:
            data = json.dumps(tokens, indent=2)
            encrypted_data = self.cipher.encrypt(data.encode("utf-8"))

            with open(self.tokens_file, "wb") as f:
                f.write(encrypted_data)

            # Set restrictive permissions (owner only)
            if os.name != "nt":  # Unix-like systems
                os.chmod(self.tokens_file, 0o600)

            return True

        except Exception as e:
            print(f"Error saving tokens: {e}")
            return False

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime

        return datetime.now().isoformat()

    def get_token_info(self, service: str) -> Optional[Dict[str, str]]:
        """Get metadata about a stored token (without the token itself)

        Args:
            service: Service name

        Returns:
            dict or None: Token metadata
        """
        try:
            tokens = self._load_tokens()
            if service in tokens:
                info = tokens[service].copy()
                info.pop("token", None)  # Remove actual token
                info["service"] = service
                info["has_token"] = True
                return info
            return None
        except:
            return None


def get_secure_storage() -> Optional[SecureTokenStorage]:
    """Get secure storage instance if cryptography is available

    Returns:
        SecureTokenStorage or None: Storage instance if available
    """
    if not HAS_CRYPTOGRAPHY:
        return None

    try:
        return SecureTokenStorage()
    except Exception as e:
        print(f"Could not initialize secure storage: {e}")
        return None
