"""Prompt Manager for Gradio MCP Playground

This module handles loading and managing prompts from YAML configuration files.
"""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class PromptManager:
    """Manages prompts and configuration from YAML files"""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize the prompt manager

        Args:
            config_dir: Path to configuration directory. If None, uses default location.
        """
        if config_dir is None:
            # Default to config directory relative to this file
            config_dir = Path(__file__).parent / "config"

        self.config_dir = Path(config_dir)
        self._cache = {}

    def _load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """Load a YAML file and cache the result"""
        if str(file_path) in self._cache:
            return self._cache[str(file_path)]

        try:
            with open(file_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                self._cache[str(file_path)] = data
                return data
        except FileNotFoundError:
            print(f"Warning: Configuration file not found: {file_path}")
            return {}
        except yaml.YAMLError as e:
            print(f"Error loading YAML file {file_path}: {e}")
            return {}

    def get_system_prompt(self, prompt_name: str = "coding_agent.main", include_environment: bool = True) -> str:
        """Get a system prompt by name, optionally with environment context

        Args:
            prompt_name: Dot-separated path to prompt (e.g., "coding_agent.main")
            include_environment: Whether to append environment information to the prompt

        Returns:
            The prompt string, or empty string if not found
        """
        prompts_file = self.config_dir / "prompts" / "system_prompts.yaml"
        data = self._load_yaml(prompts_file)

        # Navigate through nested structure
        parts = prompt_name.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                print(f"Warning: Prompt '{prompt_name}' not found")
                return ""

        prompt = str(current).strip()
        
        # Append environment information if requested
        if include_environment:
            try:
                from .environment_config import get_agent_prompt_context
                env_context = get_agent_prompt_context()
                if env_context:
                    prompt += f"\n\n{env_context}"
            except ImportError:
                pass  # Environment config not available
            except Exception as e:
                print(f"Warning: Could not load environment context: {e}")
        
        return prompt

    def get_model_config(self, model_id: Optional[str] = None) -> Dict[str, Any]:
        """Get model configuration

        Args:
            model_id: Model identifier. If None, returns all models.

        Returns:
            Model configuration dict
        """
        models_file = self.config_dir / "models.yaml"
        data = self._load_yaml(models_file)

        if model_id:
            return data.get("models", {}).get(model_id, {})
        else:
            return data.get("models", {})

    def get_available_models(self) -> Dict[str, Dict[str, Any]]:
        """Get all available models configuration"""
        return self.get_model_config()

    def get_model_defaults(self) -> Dict[str, Any]:
        """Get default model settings"""
        models_file = self.config_dir / "models.yaml"
        data = self._load_yaml(models_file)
        return data.get("defaults", {})

    def get_mcp_knowledge(self, server_id: Optional[str] = None) -> Dict[str, Any]:
        """Get MCP server knowledge base

        Args:
            server_id: Server identifier. If None, returns general knowledge.

        Returns:
            Knowledge dict
        """
        knowledge_file = self.config_dir / "knowledge" / "mcp_servers.yaml"
        data = self._load_yaml(knowledge_file)

        if server_id:
            return data.get("servers", {}).get(server_id, {})
        else:
            return data.get("general", {})

    def get_best_practices(self) -> list:
        """Get MCP best practices list"""
        knowledge_file = self.config_dir / "knowledge" / "mcp_servers.yaml"
        data = self._load_yaml(knowledge_file)
        return data.get("best_practices", [])

    def get_gradio_help(self, component: Optional[str] = None) -> Dict[str, Any]:
        """Get Gradio component help

        Args:
            component: Component name. If None, returns general tips.

        Returns:
            Help information dict
        """
        components_file = self.config_dir / "gradio_components.yaml"
        data = self._load_yaml(components_file)

        if component:
            return data.get("components", {}).get(component, {})
        else:
            return {"general_tips": data.get("general_tips", [])}

    def get_tool_description(self, tool_name: str) -> str:
        """Get tool description from prompts

        Args:
            tool_name: Name of the tool

        Returns:
            Tool description string
        """
        prompts_file = self.config_dir / "prompts" / "system_prompts.yaml"
        data = self._load_yaml(prompts_file)

        descriptions = data.get("tool_descriptions", {})
        return descriptions.get(tool_name, f"Tool: {tool_name}")

    def get_server_guidance(self, server_id: str, guidance_type: str = "success", **kwargs) -> str:
        """Get server-specific guidance messages

        Args:
            server_id: Server identifier
            guidance_type: Type of guidance (success, error, wsl_path_issue, etc.)
            **kwargs: Variables to format into the guidance message

        Returns:
            Formatted guidance message
        """
        guidance_file = self.config_dir / "server_guidance.yaml"
        data = self._load_yaml(guidance_file)

        # Try to get server-specific guidance
        server_guidance = data.get("servers", {}).get(server_id, {})
        guidance = server_guidance.get(guidance_type, "")

        # Fall back to default if not found
        if not guidance and guidance_type in data.get("default", {}):
            guidance = data["default"][guidance_type]
            kwargs["server_name"] = server_id.replace("-", " ").title()

        # Format the guidance with provided kwargs
        try:
            return guidance.format(**kwargs)
        except KeyError as e:
            print(f"Warning: Missing variable {e} in guidance template")
            return guidance

    def reload(self):
        """Clear cache and reload all configuration files"""
        self._cache.clear()


# Global instance for easy access
_prompt_manager = None


def get_prompt_manager() -> PromptManager:
    """Get the global prompt manager instance"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager
