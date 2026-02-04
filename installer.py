#!/usr/bin/env python3
"""
TimeBars Installer
Sets up virtual environment, installs dependencies, and creates initial data files.
"""

import subprocess
import sys
import os
import json
import shutil
from pathlib import Path


def check_python_version() -> bool:
    """Ensure Python 3.10+ is being used."""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"FAILED: Python 3.10+ required, found: {version.major}.{version.minor}")
        return False


def get_venv_python(venv_path: Path) -> Path:
    """Get the path to the venv Python executable."""
    if os.name == 'nt':  # Windows
        return venv_path / "Scripts" / "python.exe"
    else:  # Unix
        return venv_path / "bin" / "python"


def purge_and_create_venv(venv_path: Path) -> bool:
    """Remove existing venv and create fresh one."""
    try:
        if venv_path.exists():
            print("Purging existing virtual environment...")
            shutil.rmtree(venv_path, ignore_errors=True)
            print("Old venv purged.")
        
        print("Creating fresh virtual environment...")
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            capture_output=True
        )
        print("Virtual environment created.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"FAILED: Could not create venv: {e}")
        return False


def upgrade_pip(venv_python: Path) -> bool:
    """Upgrade pip in the virtual environment."""
    try:
        print("Upgrading pip...")
        subprocess.run(
            [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            capture_output=True
        )
        print("Pip upgraded.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"FAILED: Could not upgrade pip: {e}")
        return False


def install_requirements(venv_python: Path) -> bool:
    """Install required packages."""
    requirements = [
        "nicegui>=1.4.0",
        "pywebview>=5.0",
        "pythonnet",
    ]
    
    try:
        print("Installing dependencies...")
        for package in requirements:
            print(f"  {package}")
            subprocess.run(
                [str(venv_python), "-m", "pip", "install", package],
                check=True,
                capture_output=True,
                text=True
            )
        print("Dependencies installed.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"FAILED: Could not install requirements: {e.stderr}")
        return False


def create_data_directory(data_path: Path) -> bool:
    """Create the data directory."""
    try:
        data_path.mkdir(parents=True, exist_ok=True)
        print("Data directory ready.")
        return True
    except Exception as e:
        print(f"FAILED: Could not create data directory: {e}")
        return False


def create_persistent_json(json_path: Path) -> bool:
    """Create or replace the persistent.json file."""
    try:
        default_data = {
            "settings": {
                "default_alarm_enabled": True,
                "alarm_duration_seconds": 5,
                "flash_on_alarm": True
            },
            "timer_queue": []
        }
        
        if json_path.exists():
            print("Replacing existing persistent.json with fresh default.")
        else:
            print("Creating persistent.json...")
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, indent=2)
        
        print("persistent.json created.")
        return True
    except Exception as e:
        print(f"FAILED: Could not create persistent.json: {e}")
        return False


def create_scripts_directory(scripts_path: Path) -> bool:
    """Create the scripts directory."""
    try:
        scripts_path.mkdir(parents=True, exist_ok=True)
        print("Scripts directory ready.")
        return True
    except Exception as e:
        print(f"FAILED: Could not create scripts directory: {e}")
        return False


def main() -> int:
    """Main installer function."""
    base_path = Path(__file__).parent.resolve()
    
    venv_path = base_path / "venv"
    data_path = base_path / "data"
    scripts_path = base_path / "scripts"
    json_path = data_path / "persistent.json"
    
    print(f"Install location: {base_path}")
    
    if not check_python_version():
        return 1
    
    # Always purge and recreate venv
    if not purge_and_create_venv(venv_path):
        return 1
    
    venv_python = get_venv_python(venv_path)
    if not venv_python.exists():
        print("FAILED: Virtual environment Python not found.")
        return 1
    if not upgrade_pip(venv_python):
        return 1
    
    print("Installing dependencies...")
    if not install_requirements(venv_python):
        return 1
    
    print("Creating directories...")
    if not create_data_directory(data_path):
        return 1
    if not create_scripts_directory(scripts_path):
        return 1
    
    print("Creating data files...")
    if not create_persistent_json(json_path):
        return 1
    
    print()
    print("Installation Complete!")
    print("You can now run the program.")
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        sys.exit(1)