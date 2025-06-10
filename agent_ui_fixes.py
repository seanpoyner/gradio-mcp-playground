#!/usr/bin/env python3
"""
Fixes for agent UI components to prevent event handler errors
"""

def patch_control_panel():
    """Patch the control panel to fix event handler issues"""
    import sys
    from pathlib import Path
    
    # Add the project root to Python path
    project_root = Path(__file__).parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    try:
        # Import the control panel module
        from agent.ui import control_panel
        
        # Store original methods
        original_test_code = control_panel.ControlPanelUI._test_code
        original_save_agent = control_panel.ControlPanelUI._save_agent
        
        # Create wrapper for _test_code that handles missing inputs
        def safe_test_code(self, code=None):
            """Safe wrapper for _test_code that handles None or empty inputs"""
            if code is None:
                return "❌ Test Failed", "No code provided to test"
            return original_test_code(self, code)
        
        # Create wrapper for _save_agent that validates inputs
        def safe_save_agent(self, agent_name=None, code=None):
            """Safe wrapper for _save_agent that validates inputs"""
            if agent_name is None:
                return "❌ Save Failed", "No agent selected"
            if code is None:
                return "❌ Save Failed", "No code to save"
            return original_save_agent(self, agent_name, code)
        
        # Apply patches
        control_panel.ControlPanelUI._test_code = safe_test_code
        control_panel.ControlPanelUI._save_agent = safe_save_agent
        
        print("✅ Patched control panel event handlers")
        
    except Exception as e:
        print(f"⚠️  Could not patch control panel: {e}")


def patch_pipeline_view():
    """Patch the pipeline view to fix filter_templates issues"""
    try:
        # Import the pipeline view module
        from agent.ui import pipeline_view
        
        # Store original method
        original_filter_templates = pipeline_view.PipelineView._filter_templates
        
        # Create wrapper that handles missing inputs
        def safe_filter_templates(self, category=None):
            """Safe wrapper for _filter_templates that handles None category"""
            if category is None:
                category = "All"
            return original_filter_templates(self, category)
        
        # Apply patch
        pipeline_view.PipelineView._filter_templates = safe_filter_templates
        
        print("✅ Patched pipeline view event handlers")
        
    except Exception as e:
        print(f"⚠️  Could not patch pipeline view: {e}")


def patch_filesystem_paths():
    """Patch filesystem operations to prevent permission errors"""
    try:
        import gradio.processing_utils as processing_utils
        
        # Store original hash_file function
        original_hash_file = processing_utils.hash_file
        
        def safe_hash_file(file_path):
            """Safe wrapper that checks if path is a directory"""
            import os
            
            # Convert to string if it's a Path object
            if hasattr(file_path, '__fspath__'):
                file_path = str(file_path)
            
            # Check if the path is a directory
            if os.path.isdir(file_path):
                # Return a default hash for directories
                return "directory_" + str(abs(hash(file_path)))
            
            # Check if we have permission to read the file
            try:
                with open(file_path, 'rb') as f:
                    # Just test if we can open it
                    pass
            except (PermissionError, OSError):
                # Return a default hash for inaccessible files
                return "inaccessible_" + str(abs(hash(file_path)))
            
            # Otherwise use original function
            return original_hash_file(file_path)
        
        # Apply patch
        processing_utils.hash_file = safe_hash_file
        
        print("✅ Patched filesystem operations")
        
    except Exception as e:
        print(f"⚠️  Could not patch filesystem operations: {e}")


def apply_all_patches():
    """Apply all UI patches"""
    print("🔧 Applying agent UI patches...")
    patch_control_panel()
    patch_pipeline_view()
    patch_filesystem_paths()
    print("✅ All patches applied")


if __name__ == "__main__":
    apply_all_patches()