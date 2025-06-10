"""Gradio Helper Utilities

Helper functions for handling common Gradio UI patterns and event handling.
"""

from typing import Any, Optional, Union, List, Dict, Callable
import functools


def safe_dropdown_handler(default_return=None):
    """Decorator to safely handle dropdown event handlers when value is None or empty.
    
    Args:
        default_return: Default value to return when dropdown value is invalid
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(dropdown_value: Optional[Union[str, List]], *args, **kwargs):
            # Handle different types of empty values
            if dropdown_value is None:
                return default_return
            if isinstance(dropdown_value, list) and len(dropdown_value) == 0:
                return default_return
            if isinstance(dropdown_value, str) and dropdown_value.strip() == "":
                return default_return
                
            # Call the original function with valid value
            return func(dropdown_value, *args, **kwargs)
        return wrapper
    return decorator


def validate_dropdown_input(value: Any, choices: List[str], allow_custom: bool = False) -> Optional[str]:
    """Validate dropdown input against available choices.
    
    Args:
        value: The input value to validate
        choices: List of valid choices
        allow_custom: Whether to allow custom values not in choices
        
    Returns:
        Validated value or None if invalid
    """
    if value is None:
        return None
        
    # Convert to string if needed
    str_value = str(value) if value else ""
    
    # Check if empty
    if not str_value.strip():
        return None
        
    # Check if in choices
    if str_value in choices:
        return str_value
        
    # Check if custom values allowed
    if allow_custom:
        return str_value
        
    return None


def safe_dataframe_handler(default_rows=None):
    """Decorator to safely handle dataframe selection events.
    
    Args:
        default_rows: Default value to return when no rows selected
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(dataframe_data: Any, *args, **kwargs):
            if dataframe_data is None:
                return default_rows
            if isinstance(dataframe_data, list) and len(dataframe_data) == 0:
                return default_rows
                
            return func(dataframe_data, *args, **kwargs)
        return wrapper
    return decorator


def create_safe_dropdown(choices: List[str], value: Optional[str] = None, **kwargs) -> Any:
    """Create a dropdown with safe default handling.
    
    Args:
        choices: List of dropdown choices
        value: Default value (will be validated)
        **kwargs: Other Gradio dropdown parameters
        
    Returns:
        Gradio dropdown component
    """
    import gradio as gr
    
    # Validate default value
    if value and value not in choices:
        value = None
        
    # Ensure choices is not empty
    if not choices:
        choices = ["No options available"]
        value = None
        
    return gr.Dropdown(
        choices=choices,
        value=value,
        **kwargs
    )