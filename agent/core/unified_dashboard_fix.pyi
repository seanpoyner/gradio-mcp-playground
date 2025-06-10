"""Unified Dashboard Integration Fix

This module provides fixes specifically for integrating the GMP Agent
with the parent Gradio MCP Playground unified dashboard.
"""

import functools
from typing import Any, Dict, List, Optional

from gradio.events import Dependency

def fix_unified_dashboard_integration():
    """Apply fixes for unified dashboard integration issues.
    
    The main issue is that event handlers from different components
    can get mixed up when integrated into the unified dashboard.
    """
    
    try:
        import gradio as gr
        
        # Store original component classes
        _original_dropdown = gr.Dropdown
        _original_textbox = gr.Textbox
        
        class IsolatedDropdown(_original_dropdown):
            """Dropdown that isolates its events from other components"""
            
            def __init__(self, *args, **kwargs):
                # Add a unique elem_id if not provided
                if 'elem_id' not in kwargs:
                    import uuid
                    kwargs['elem_id'] = f"dropdown_{uuid.uuid4().hex[:8]}"
                
                # Ensure choices is valid
                if 'choices' in kwargs:
                    choices = kwargs['choices']
                    if not choices or (isinstance(choices, list) and len(choices) == 0):
                        kwargs['choices'] = []
                        kwargs['value'] = None
                    elif 'value' in kwargs and kwargs['value'] not in choices:
                        kwargs['value'] = None
                
                super().__init__(*args, **kwargs)
    from typing import Callable, Literal, Sequence, Any, TYPE_CHECKING
    from gradio.blocks import Block
    if TYPE_CHECKING:
        from gradio.components import Timer
        from gradio.components.base import Component
        
        class IsolatedTextbox(_original_textbox):
            """Textbox that prevents cross-component event pollution"""
            
            def __init__(self, *args, **kwargs):
                # Add unique elem_id
                if 'elem_id' not in kwargs:
                    import uuid
                    kwargs['elem_id'] = f"textbox_{uuid.uuid4().hex[:8]}"
                
                super().__init__(*args, **kwargs)
        
        # Replace components
        gr.Dropdown = IsolatedDropdown
        gr.Textbox = IsolatedTextbox
        
    except Exception as e:
        print(f"Warning: Could not apply unified dashboard fixes: {e}")


def create_isolated_interface(interface_func):
    """Decorator to create an isolated interface for unified dashboard.
    
    This ensures that components created within the interface don't
    interfere with other parts of the unified dashboard.
    """
    
    @functools.wraps(interface_func)
    def wrapper(*args, **kwargs):
        # Apply isolation fixes
        fix_unified_dashboard_integration()
        
        # Create the interface
        return interface_func(*args, **kwargs)
    
    return wrapper


def validate_chat_input(func):
    """Decorator to ensure chat input is not misrouted to other handlers"""
    
    @functools.wraps(func)
    def wrapper(message, *args, **kwargs):
        # Ensure message is a string (not a dropdown choice)
        if isinstance(message, list):
            # This shouldn't happen for chat input
            return None
            
        if not isinstance(message, str):
            message = str(message) if message else ""
            
        return func(message, *args, **kwargs)
    
    return wrapper


def isolate_component_events(component_class):
    """Class decorator to isolate component events"""
    
    original_init = component_class.__init__
    
    def new_init(self, *args, **kwargs):
        # Call original init
        original_init(self, *args, **kwargs)
        
        # Add isolation marker
        self._isolated = True
        
    component_class.__init__ = new_init
    
    return component_class