#!/usr/bin/env python3
"""
TimeBars Installer
Sets up virtual environment, installs dependencies, and creates initial data files.
"""

import subprocess
import sys
import os
import json
import struct
import wave
import math
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


def create_venv(venv_path: Path) -> bool:
    """Create a virtual environment."""
    try:
        if venv_path.exists():
            print("Virtual environment already exists, skipping creation.")
            return True
        
        print("Creating virtual environment...")
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


def get_venv_python(venv_path: Path) -> Path:
    """Get the path to the venv Python executable."""
    if os.name == 'nt':  # Windows
        return venv_path / "Scripts" / "python.exe"
    else:  # Unix
        return venv_path / "bin" / "python"


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
    # Requirements embedded directly
    # pywebview with EdgeChromium support for Windows
    requirements = [
        "nicegui>=1.4.0",
        "pywebview>=5.0",
        "pythonnet",  # Required for EdgeChromium on Windows
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
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, indent=2)
        
        print("persistent.json created.")
        return True
    except Exception as e:
        print(f"FAILED: Could not create persistent.json: {e}")
        return False


def generate_alarm_sound(wav_path: Path) -> bool:
    """Generate a simple alarm beep WAV file."""
    try:
        if wav_path.exists():
            print("alarm-bleep.wav already exists, skipping generation.")
            return True
        
        # Audio parameters
        sample_rate = 44100
        duration = 0.15  # seconds per beep
        frequency = 880  # Hz (A5 note)
        volume = 0.7
        
        # Generate a beep pattern: beep-pause-beep-pause-beep
        beep_samples = int(sample_rate * duration)
        pause_samples = int(sample_rate * 0.1)
        
        samples = []
        
        for beep_num in range(3):
            # Generate beep
            for i in range(beep_samples):
                t = i / sample_rate
                # Sine wave with envelope
                envelope = min(1.0, min(i / 500, (beep_samples - i) / 500))
                value = volume * envelope * (
                    0.6 * math.sin(2 * math.pi * frequency * t) +
                    0.3 * math.sin(2 * math.pi * frequency * 2 * t) +
                    0.1 * math.sin(2 * math.pi * frequency * 3 * t)
                )
                samples.append(int(value * 32767))
            
            # Add pause between beeps (except after last)
            if beep_num < 2:
                samples.extend([0] * pause_samples)
        
        # Write WAV file
        with wave.open(str(wav_path), 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 2 bytes per sample
            wav_file.setframerate(sample_rate)
            
            # Pack samples as 16-bit signed integers
            packed = struct.pack('<' + 'h' * len(samples), *samples)
            wav_file.writeframes(packed)
        
        print("alarm-bleep.wav generated.")
        return True
    except Exception as e:
        print(f"FAILED: Could not generate alarm sound: {e}")
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
    # Get base path (directory containing this script)
    base_path = Path(__file__).parent.resolve()
    
    # Define paths
    venv_path = base_path / "venv"
    data_path = base_path / "data"
    scripts_path = base_path / "scripts"
    json_path = data_path / "persistent.json"
    wav_path = data_path / "alarm-bleep.wav"
    
    print(f"Install location: {base_path}")
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Create virtual environment
    if not create_venv(venv_path):
        return 1
    
    # Get venv Python and upgrade pip
    venv_python = get_venv_python(venv_path)
    if not venv_python.exists():
        print("FAILED: Virtual environment Python not found.")
        return 1
    if not upgrade_pip(venv_python):
        return 1
    
    # Install requirements
    if not install_requirements(venv_python):
        return 1
    
    # Create directories
    print("Creating directories...")
    if not create_data_directory(data_path):
        return 1
    if not create_scripts_directory(scripts_path):
        return 1
    
    # Create data files
    print("Creating data files...")
    if not create_persistent_json(json_path):
        return 1
    if not generate_alarm_sound(wav_path):
        return 1
    
    print()
    print("Installation Complete!")
    
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