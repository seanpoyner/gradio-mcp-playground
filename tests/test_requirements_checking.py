"""Test the requirements checking functionality"""

import pytest
from gradio_mcp_playground.registry import ServerRegistry
from gradio_mcp_playground.coding_agent import CodingAgent


class TestRequirementsChecking:
    """Test server requirements checking functionality"""
    
    @pytest.fixture
    def registry(self):
        """Get server registry instance"""
        return ServerRegistry()
    
    def test_memory_server_no_requirements(self, registry):
        """Test that memory server has no requirements"""
        server_info = registry.get_server_info('memory')
        assert server_info is not None
        assert server_info.get('required_args', []) == []
        assert server_info.get('env_vars', {}) == {}
    
    def test_filesystem_server_requires_path(self, registry):
        """Test that filesystem server requires path argument"""
        server_info = registry.get_server_info('filesystem')
        assert server_info is not None
        assert 'path' in server_info.get('required_args', [])
        assert server_info.get('env_vars', {}) == {}
    
    def test_brave_search_requires_api_key(self, registry):
        """Test that brave-search requires API key"""
        server_info = registry.get_server_info('brave-search')
        assert server_info is not None
        assert server_info.get('required_args', []) == []
        assert 'BRAVE_API_KEY' in server_info.get('env_vars', {})
        assert 'brave.com/search/api' in server_info.get('setup_help', '')
    
    def test_github_requires_token(self, registry):
        """Test that github server requires token"""
        server_info = registry.get_server_info('github')
        assert server_info is not None
        assert server_info.get('required_args', []) == []
        assert 'GITHUB_TOKEN' in server_info.get('env_vars', {})
        assert 'github.com/settings/tokens' in server_info.get('setup_help', '')
    
    def test_obsidian_requires_vault_path(self, registry):
        """Test that obsidian requires vault path"""
        server_info = registry.get_server_info('obsidian')
        assert server_info is not None
        assert 'vault_path1' in server_info.get('required_args', [])
        assert 'vault_path2' in server_info.get('optional_args', [])
    
    def test_time_server_requires_timezone(self, registry):
        """Test that time server requires timezone"""
        server_info = registry.get_server_info('time')
        assert server_info is not None
        assert 'timezone' in server_info.get('required_args', [])
        assert 'America/New_York' in server_info.get('setup_help', '')
    
    def test_generate_install_command_with_all_args(self, registry):
        """Test generating install command with all required arguments"""
        # Test filesystem with path
        install_config = registry.generate_install_command('filesystem', {'path': '/home/user'})
        assert install_config is not None
        assert '/home/user' in install_config['args']
        
        # Test brave-search with token
        install_config = registry.generate_install_command('brave-search', {'BRAVE_API_KEY': 'test-key'})
        assert install_config is not None
        assert install_config['env']['BRAVE_API_KEY'] == 'test-key'
    
    def test_generate_install_command_missing_args(self, registry):
        """Test that missing required args returns None"""
        # Missing path for filesystem
        install_config = registry.generate_install_command('filesystem', {})
        assert install_config is None
        
        # Missing timezone for time server
        install_config = registry.generate_install_command('time', {})
        assert install_config is None
    
    def test_generate_install_command_optional_args(self, registry):
        """Test that optional args are handled correctly"""
        # Obsidian with only required vault_path1
        install_config = registry.generate_install_command('obsidian', {'vault_path1': '/vault1'})
        assert install_config is not None
        assert '/vault1' in install_config['args']
        
        # Obsidian with both vault paths
        install_config = registry.generate_install_command('obsidian', {
            'vault_path1': '/vault1',
            'vault_path2': '/vault2'
        })
        assert install_config is not None
        assert '/vault1' in install_config['args']
        assert '/vault2' in install_config['args']


class TestNaturalLanguageParsing:
    """Test natural language input parsing"""
    
    def test_parse_brave_key_patterns(self):
        """Test parsing various brave key input patterns"""
        import re
        
        patterns = [
            ("install brave search with key BSAcIbrB5nHtrlV5iqt98NaYDhfjOCh", "BSAcIbrB5nHtrlV5iqt98NaYDhfjOCh"),
            ("Install Brave Search with token my-api-key-123", "my-api-key-123"),
            ("my brave api key is test-key-456", "test-key-456"),
            ("brave key = abc123", "abc123"),
        ]
        
        for message, expected_key in patterns:
            # Pattern from web_ui.py
            match = re.search(r"install brave search with (?:key|token) ([\w-]+)", message, re.IGNORECASE)
            if not match:
                match = re.search(r"(?:my )?brave (?:api )?key (?:is |= ?)([\w-]+)", message, re.IGNORECASE)
            
            assert match is not None, f"Failed to parse: {message}"
            assert match.group(1) == expected_key
    
    def test_parse_path_patterns(self):
        """Test parsing filesystem path patterns"""
        import re
        
        patterns = [
            ("use path /home/user/workspace", "/home/user/workspace"),
            ("provide path /mnt/data", "/mnt/data"),
            ("path is /Users/john/Documents", "/Users/john/Documents"),
        ]
        
        for message, expected_path in patterns:
            match = re.search(r"(?:use |provide )?path (?:is |= ?)?([/\\][^\s]+)", message, re.IGNORECASE)
            assert match is not None, f"Failed to parse: {message}"
            assert match.group(1) == expected_path
    
    def test_parse_vault_patterns(self):
        """Test parsing Obsidian vault path patterns"""
        import re
        
        patterns = [
            ("my obsidian vault is at /path/to/vault", "/path/to/vault"),
            ("obsidian vault in /Users/jane/Obsidian", "/Users/jane/Obsidian"),
            ("my obsidian vault /home/notes", "/home/notes"),
        ]
        
        for message, expected_path in patterns:
            match = re.search(r"(?:my )?obsidian vault (?:is )?(?:at |in )?([/\\][^\s]+)", message, re.IGNORECASE)
            assert match is not None, f"Failed to parse: {message}"
            assert match.group(1) == expected_path
    
    def test_parse_github_token_patterns(self):
        """Test parsing GitHub token patterns"""
        import re
        
        patterns = [
            ("my github token is ghp_1234567890abcdef", "ghp_1234567890abcdef"),
            ("github personal access token = my-pat-123", "my-pat-123"),
            ("my github pat is test-token", "test-token"),
        ]
        
        for message, expected_token in patterns:
            match = re.search(r"(?:my )?github (?:token|pat|personal access token) (?:is |= ?)([\w-]+)", message, re.IGNORECASE)
            assert match is not None, f"Failed to parse: {message}"
            assert match.group(1) == expected_token