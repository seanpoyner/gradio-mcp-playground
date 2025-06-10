"""Event Handlers Fix

This module provides fixes for common Gradio event handler issues,
particularly dropdown validation errors.
"""

import functools
from typing import Any, Callable, Optional, Union, List


def fix_dropdown_event_handlers(interface_class):
    """Class decorator to automatically fix dropdown event handlers.
    
    This decorator wraps methods that are commonly used as dropdown event handlers
    to ensure they handle empty/invalid inputs gracefully.
    """
    
    # List of method names that commonly handle dropdown events
    dropdown_handler_methods = [
        '_select_server_by_name',
        '_reconnect_connection',
        '_disconnect_connection',
        '_load_connection_details',
        '_test_connection',
        '_call_tool',
        '_handle_dropdown_change',
        '_on_dropdown_select',
        'on_select',
        'on_change'
    ]
    
    def safe_wrapper(original_method):
        """Wrapper that ensures dropdown value is valid before calling method"""
        @functools.wraps(original_method)
        def wrapped(self, dropdown_value=None, *args, **kwargs):
            # Handle various empty value scenarios
            if dropdown_value is None:
                # Try to get a sensible default return value
                return None
            
            if isinstance(dropdown_value, list) and len(dropdown_value) == 0:
                return None
                
            if isinstance(dropdown_value, str) and dropdown_value.strip() == "":
                return None
            
            # Call original method with validated value
            return original_method(self, dropdown_value, *args, **kwargs)
        
        return wrapped
    
    # Apply wrapper to all dropdown handler methods
    for attr_name in dir(interface_class):
        if attr_name in dropdown_handler_methods:
            attr = getattr(interface_class, attr_name)
            if callable(attr):
                setattr(interface_class, attr_name, safe_wrapper(attr))
    
    return interface_class


def validate_gradio_inputs(*expected_types):
    """Decorator to validate Gradio input types and handle mismatches gracefully.
    
    Args:
        *expected_types: Expected types for each input parameter
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Validate each input against expected type
            validated_args = []
            
            for i, (arg, expected_type) in enumerate(zip(args, expected_types)):
                if expected_type == 'dropdown':
                    # Special handling for dropdown inputs
                    if isinstance(arg, list) and len(arg) == 0:
                        arg = None
                    elif isinstance(arg, str) and arg.strip() == "":
                        arg = None
                elif expected_type == 'textbox':
                    # Ensure textbox input is string
                    if arg is None:
                        arg = ""
                    elif not isinstance(arg, str):
                        arg = str(arg)
                
                validated_args.append(arg)
            
            # Add remaining args that don't have type specifications
            validated_args.extend(args[len(expected_types):])
            
            return func(*validated_args, **kwargs)
        
        return wrapper
    return decorator

from gradio.events import Dependency

def patch_gradio_components():
    """Patch Gradio components to handle common issues.
    
    This should be called at application startup to apply global fixes.
    """
    try:
        import gradio as gr
        
        # Store original Dropdown class
        _original_dropdown = gr.Dropdown
        
        class SafeDropdown(_original_dropdown):
            """Enhanced Dropdown that handles empty values better"""
            
            def __init__(self, *args, **kwargs):
                # Ensure choices is not empty
                if 'choices' in kwargs and not kwargs['choices']:
                    kwargs['choices'] = ["No options available"]
                
                # Validate default value
                if 'value' in kwargs and kwargs['value']:
                    if 'choices' in kwargs and kwargs['value'] not in kwargs['choices']:
                        kwargs['value'] = None
                
                super().__init__(*args, **kwargs)
            
            def preprocess(self, x):
                """Override preprocess to handle edge cases"""
                if x is None or (isinstance(x, list) and len(x) == 0):
                    return None
                    
                # Let parent handle the rest
                return super().preprocess(x)
    from typing import Callable, Literal, Sequence, Any, TYPE_CHECKING
    from gradio.blocks import Block
    if TYPE_CHECKING:
        from gradio.components import Timer
        from gradio.components.base import Component
        
        # Replace Gradio's Dropdown with our safe version
        gr.Dropdown = SafeDropdown
        
    except Exception as e:
        print(f"Warning: Could not patch Gradio components: {e}")


# Auto-patch on import
patch_gradio_components()