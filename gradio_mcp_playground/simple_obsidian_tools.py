"""Simple Obsidian Tools for Direct Integration

This module provides direct Obsidian vault access without MCP complexity.
"""

import os
from pathlib import Path
from typing import List, Optional


class SimpleObsidianTools:
    """Direct Obsidian vault access tools"""
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {vault_path}")
    
    def list_notes(self) -> str:
        """List all markdown notes in the vault"""
        try:
            notes = []
            for root, dirs, files in os.walk(self.vault_path):
                # Skip .obsidian directory
                if '.obsidian' in root:
                    continue
                for file in files:
                    if file.endswith('.md'):
                        rel_path = os.path.relpath(os.path.join(root, file), self.vault_path)
                        notes.append(rel_path.replace('\\', '/'))
            
            if notes:
                return f"Found {len(notes)} notes in vault:\n" + "\n".join(f"- {note}" for note in sorted(notes))
            else:
                return "No notes found in vault"
        except Exception as e:
            return f"Error listing notes: {str(e)}"
    
    def read_note(self, path: str) -> str:
        """Read a specific note from the vault"""
        try:
            full_path = self.vault_path / path
            if not full_path.exists():
                return f"Note not found: {path}"
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return f"Content of {path}:\n\n{content}"
        except Exception as e:
            return f"Error reading note: {str(e)}"
    
    def create_note(self, path: str, content: str) -> str:
        """Create a new note in the vault"""
        try:
            full_path = self.vault_path / path
            # Create directory if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully created note: {path}"
        except Exception as e:
            return f"Error creating note: {str(e)}"
    
    def search_notes(self, query: str) -> str:
        """Search for notes containing a query string"""
        try:
            if not query:
                return self.list_notes()
            
            results = []
            query_lower = query.lower()
            
            for root, dirs, files in os.walk(self.vault_path):
                if '.obsidian' in root:
                    continue
                for file in files:
                    if file.endswith('.md'):
                        full_path = os.path.join(root, file)
                        try:
                            with open(full_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if query_lower in content.lower() or query_lower in file.lower():
                                    rel_path = os.path.relpath(full_path, self.vault_path)
                                    results.append(rel_path.replace('\\', '/'))
                        except:
                            pass
            
            if results:
                return f"Found {len(results)} notes containing '{query}':\n" + "\n".join(f"- {note}" for note in sorted(results))
            else:
                return f"No notes found containing '{query}'"
        except Exception as e:
            return f"Error searching notes: {str(e)}"


def create_obsidian_tools_for_llamaindex(vault_path: str):
    """Create LlamaIndex-compatible tools for Obsidian vault access"""
    try:
        from llama_index.core.tools import FunctionTool
    except ImportError:
        return []
    
    # Create the Obsidian tools instance
    obsidian = SimpleObsidianTools(vault_path)
    
    # Create wrapper functions for LlamaIndex
    def obsidian_list_notes() -> str:
        """List all notes in the Obsidian vault"""
        return obsidian.list_notes()
    
    def obsidian_read_note(path: str) -> str:
        """Read a note from the Obsidian vault
        
        Args:
            path: Path to the note (e.g., 'folder/note.md')
        """
        return obsidian.read_note(path)
    
    def obsidian_create_note(path: str, content: str) -> str:
        """Create a new note in the Obsidian vault
        
        Args:
            path: Path for the new note (e.g., 'folder/new_note.md')
            content: Content of the note
        """
        return obsidian.create_note(path, content)
    
    def obsidian_search_notes(query: str = "") -> str:
        """Search for notes containing a query string
        
        Args:
            query: Search term (leave empty to list all notes)
        """
        return obsidian.search_notes(query)
    
    # Create LlamaIndex tools
    tools = [
        FunctionTool.from_defaults(fn=obsidian_list_notes, name="obsidian_list_notes"),
        FunctionTool.from_defaults(fn=obsidian_read_note, name="obsidian_read_note"),
        FunctionTool.from_defaults(fn=obsidian_create_note, name="obsidian_create_note"),
        FunctionTool.from_defaults(fn=obsidian_search_notes, name="obsidian_search_notes"),
    ]
    
    return tools