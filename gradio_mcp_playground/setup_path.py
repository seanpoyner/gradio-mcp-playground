#!/usr/bin/env python3
"""
Script to add gmp command to Windows PATH after installation.
Run this script after installing gradio-mcp-playground to enable the gmp command.
"""

import os
import subprocess
import sys
import sysconfig


def get_scripts_dir():
    """Get the directory where Python scripts are installed."""
    if sys.platform == "win32":
        # Try to find where pip installs scripts
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "-f", "gradio-mcp-playground"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if "gmp.exe" in line or "../../../Scripts/gmp.exe" in line:
                    # Extract the scripts directory path
                    if hasattr(sys, "real_prefix") or (
                        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
                    ):
                        # Virtual environment
                        return os.path.join(sys.prefix, "Scripts")
                    else:
                        # User installation - use the path from pip show
                        return os.path.join(
                            os.path.expanduser("~"),
                            "AppData",
                            "Roaming",
                            "Python",
                            f"Python{sys.version_info.major}{sys.version_info.minor}",
                            "Scripts",
                        )

        # Fallback
        return sysconfig.get_path("scripts")
    else:
        return sysconfig.get_path("scripts")


def update_windows_path(scripts_dir):
    """Update Windows PATH environment variable."""
    if sys.platform != "win32":
        print("This script is only needed on Windows.")
        return

    try:
        import winreg

        # Get current user PATH
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS
        ) as key:
            try:
                current_path, _ = winreg.QueryValueEx(key, "PATH")
            except FileNotFoundError:
                current_path = ""

            # Normalize paths for comparison
            paths = [p.strip() for p in current_path.split(";") if p.strip()]
            scripts_dir_normalized = os.path.normpath(scripts_dir)

            if not any(os.path.normpath(p) == scripts_dir_normalized for p in paths):
                # Add scripts_dir to PATH
                new_path = f"{current_path};{scripts_dir}" if current_path else scripts_dir
                winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)

                print(f"Successfully added {scripts_dir} to your Windows PATH")
                print("\nYou may need to:")
                print("   1. Restart your terminal/PowerShell")
                print(f"   2. Or run: $env:PATH += ';{scripts_dir}'")
                print("   3. Then try: gmp --help")

                # Try to notify Windows of environment change
                try:
                    import ctypes

                    HWND_BROADCAST = 0xFFFF
                    WM_SETTINGCHANGE = 0x001A
                    SMTO_ABORTIFHUNG = 0x0002

                    result = ctypes.windll.user32.SendMessageTimeoutW(
                        HWND_BROADCAST,
                        WM_SETTINGCHANGE,
                        0,
                        "Environment",
                        SMTO_ABORTIFHUNG,
                        5000,
                        None,
                    )
                    if result:
                        print("Notified Windows of PATH changes")
                except Exception:
                    pass  # Silent fail for notification

            else:
                print(f"{scripts_dir} is already in your PATH")
                print("Try running: gmp --help")

    except ImportError:
        print("Cannot update PATH automatically (winreg not available)")
        print(f"Please manually add this directory to your PATH: {scripts_dir}")
    except Exception as e:
        print(f"Could not update PATH: {e}")
        print(f"Please manually add this directory to your PATH: {scripts_dir}")


def main():
    """Main function."""
    print("Setting up gradio-mcp-playground PATH...")

    # Check if gmp is already available
    try:
        result = subprocess.run(["gmp", "--help"], capture_output=True)
        if result.returncode == 0:
            print("gmp command is already available!")
            return
    except FileNotFoundError:
        pass

    scripts_dir = get_scripts_dir()
    print(f"Scripts directory: {scripts_dir}")

    # Check if gmp.exe exists
    gmp_exe = os.path.join(scripts_dir, "gmp.exe")
    if not os.path.exists(gmp_exe):
        print(f"gmp.exe not found at {gmp_exe}")
        print("Make sure gradio-mcp-playground is installed: pip install -e .")
        return

    update_windows_path(scripts_dir)


if __name__ == "__main__":
    main()
