#!/usr/bin/env python3
"""
Setup script for DANDI External Resources Web App
"""
import os
import sys
import subprocess
import venv

def create_virtual_environment():
    """Create a virtual environment for the webapp"""
    venv_path = os.path.join(os.path.dirname(__file__), 'venv')
    
    if os.path.exists(venv_path):
        print("Virtual environment already exists.")
        return venv_path
    
    print("Creating virtual environment...")
    venv.create(venv_path, with_pip=True)
    print(f"Virtual environment created at: {venv_path}")
    return venv_path

def install_requirements(venv_path):
    """Install required packages"""
    if sys.platform == "win32":
        pip_path = os.path.join(venv_path, "Scripts", "pip")
        python_path = os.path.join(venv_path, "Scripts", "python")
    else:
        pip_path = os.path.join(venv_path, "bin", "pip")
        python_path = os.path.join(venv_path, "bin", "python")
    
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    
    print("Installing requirements...")
    try:
        subprocess.check_call([pip_path, "install", "-r", requirements_path])
        print("Requirements installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {e}")
        return False
    
    return True

def check_yaml_file():
    """Check if external_resources.yaml exists"""
    yaml_path = os.path.join(os.path.dirname(__file__), '..', 'external_resources.yaml')
    
    if not os.path.exists(yaml_path):
        print(f"Warning: external_resources.yaml not found at {yaml_path}")
        print("The webapp will create this file when you add your first resource.")
    else:
        print(f"Found external_resources.yaml at: {yaml_path}")
    
    return yaml_path

def print_instructions(venv_path):
    """Print instructions for running the webapp"""
    if sys.platform == "win32":
        activate_cmd = os.path.join(venv_path, "Scripts", "activate")
        python_cmd = os.path.join(venv_path, "Scripts", "python")
    else:
        activate_cmd = f"source {os.path.join(venv_path, 'bin', 'activate')}"
        python_cmd = os.path.join(venv_path, "bin", "python")
    
    print("\n" + "="*60)
    print("SETUP COMPLETE!")
    print("="*60)
    print("\nTo run the DANDI External Resources webapp:")
    print("\n1. Activate the virtual environment:")
    if sys.platform == "win32":
        print(f"   {activate_cmd}")
    else:
        print(f"   {activate_cmd}")
    
    print("\n2. Run the Flask application:")
    print(f"   {python_cmd} app.py")
    
    print("\n3. Open your web browser and go to:")
    print("   http://127.0.0.1:5000")
    
    print("\nAlternatively, you can run directly:")
    print(f"   {python_cmd} app.py")
    
    print("\nThe webapp will:")
    print("- Display a form matching your DANDI interface")
    print("- Validate input using your Pydantic models")
    print("- Save resources to external_resources.yaml")
    print("- Create backups before modifying files")
    
    print("\nPress Ctrl+C in the terminal to stop the server.")
    print("="*60)

def main():
    """Main setup function"""
    print("DANDI External Resources Web App Setup")
    print("="*40)
    
    # Create virtual environment
    venv_path = create_virtual_environment()
    
    # Install requirements
    if not install_requirements(venv_path):
        print("Setup failed. Please check the error messages above.")
        return
    
    # Check for YAML file
    check_yaml_file()
    
    # Print instructions
    print_instructions(venv_path)

if __name__ == "__main__":
    main()
