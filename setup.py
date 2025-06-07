#!/usr/bin/env python3
"""
Custom setup.py to handle Windows PATH updates during installation.
"""

import os
import sys
import sysconfig
from pathlib import Path
from setuptools import setup
from setuptools.command.install import install
from setuptools.command.develop import develop


def get_scripts_dir():
    """Get the directory where scripts are installed."""
    if sys.platform == "win32":
        # On Windows, scripts go to Scripts directory
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            # Virtual environment
            return os.path.join(sys.prefix, 'Scripts')
        else:
            # User installation
            return sysconfig.get_path('scripts')
    else:
        # On Unix-like systems
        return sysconfig.get_path('scripts')


def update_windows_path(scripts_dir):
    """Update Windows PATH environment variable to include scripts directory."""
    if sys.platform != "win32":
        return
    
    try:
        import winreg
        
        # Get current user PATH
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS) as key:
            try:
                current_path, _ = winreg.QueryValueEx(key, "PATH")
            except FileNotFoundError:
                current_path = ""
            
            # Check if scripts_dir is already in PATH
            paths = [p.strip() for p in current_path.split(';') if p.strip()]
            scripts_dir_normalized = os.path.normpath(scripts_dir)
            
            if not any(os.path.normpath(p) == scripts_dir_normalized for p in paths):
                # Add scripts_dir to PATH
                new_path = f"{current_path};{scripts_dir}" if current_path else scripts_dir
                winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
                
                print(f"✅ Added {scripts_dir} to your Windows PATH")
                print("💡 You may need to restart your terminal for the PATH changes to take effect")
                print("🎉 You can now use: gmp --help")
                
                # Notify Windows of environment change
                try:
                    import ctypes
                    from ctypes import wintypes
                    
                    HWND_BROADCAST = 0xFFFF
                    WM_SETTINGCHANGE = 0x001A
                    SMTO_ABORTIFHUNG = 0x0002
                    
                    result = ctypes.windll.user32.SendMessageTimeoutW(
                        HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment",
                        SMTO_ABORTIFHUNG, 5000, None
                    )
                    if result:
                        print("🔄 Notified Windows of PATH changes")
                except Exception as e:
                    print(f"⚠️  Could not notify Windows of PATH changes: {e}")
            else:
                print(f"✅ {scripts_dir} is already in your PATH")
                
    except ImportError:
        print("⚠️  winreg module not available - cannot update PATH automatically")
    except Exception as e:
        print(f"⚠️  Could not update PATH: {e}")
        print(f"💡 Please manually add {scripts_dir} to your PATH environment variable")
        print("🔧 Or run: python -m gradio_mcp_playground.setup_path")
        print("📚 Or use: python -m gradio_mcp_playground.cli setup-path")


class CustomInstallCommand(install):
    """Custom install command that updates PATH on Windows."""
    
    def run(self):
        install.run(self)
        
        # Update PATH after installation
        scripts_dir = get_scripts_dir()
        print(f"\n📍 Scripts installed to: {scripts_dir}")
        update_windows_path(scripts_dir)


class CustomDevelopCommand(develop):
    """Custom develop command that updates PATH on Windows."""
    
    def run(self):
        develop.run(self)
        
        # Update PATH after development installation
        scripts_dir = get_scripts_dir()
        print(f"\n📍 Scripts installed to: {scripts_dir}")
        update_windows_path(scripts_dir)


if __name__ == "__main__":
    setup(
        cmdclass={
            'install': CustomInstallCommand,
            'develop': CustomDevelopCommand,
        }
    )