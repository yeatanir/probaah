#!/bin/bash
# Probaah Quick Setup Script
# Run this to get Probaah working in 5 minutes

set -e  # Exit on any error

echo "🌊 Probaah Quick Setup (প্ৰবাহ)"
echo "=================================="
echo ""

# Check if we're in the right directory
if [ ! -f "claude.md" ]; then
    echo "❌ Please run this from the Probaah repository root directory"
    echo "   (The directory containing claude.md file)"
    exit 1
fi

echo "✅ Repository structure detected"

# Check Python version
python3 --version >/dev/null 2>&1 || {
    echo "❌ Python 3 is required but not installed"
    echo "   Install Python 3.8+ and try again"
    exit 1
}

echo "✅ Python 3 found"

# Create virtual environment (optional but recommended)
echo "🐍 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -e .

echo "✅ Dependencies installed"

# Initialize configuration
echo "⚙️  Initializing configuration..."
probaah config init --user anirban --email akp6421@psu.edu

echo "✅ Configuration initialized"

# Test basic functionality
echo "🧪 Testing basic functionality..."
cd /tmp
probaah project create test-probaah --type reaxff --description "Testing Probaah setup"

if [ -d "test-probaah_$(date +%Y%m%d)" ]; then
    echo "✅ Project creation test successful"
    rm -rf "test-probaah_$(date +%Y%m%d)"
else
    echo "❌ Project creation test failed"
    exit 1
fi

# Return to original directory
cd - > /dev/null

echo ""
echo "🎉 PROBAAH SETUP COMPLETE!"
echo "=========================="
echo ""
echo "📋 Quick Start Commands:"
echo "  probaah project create my-research --type reaxff"
echo "  probaah project list"
echo "  probaah jobs status"
echo "  probaah config show"
echo ""
echo "🔧 Next Steps:"
echo "  1. Set up SSH keys: probaah config ssh --setup"
echo "  2. Create your first real project"
echo "  3. Test SLURM integration"
echo ""
echo "📚 Documentation: Check README.md and claude.md"
echo "🐛 Issues: Remember to check .probaah-config.yaml in project folders"
echo ""
echo "Happy researching! 🚀"

# =====================================
# Alternative: Windows WSL Setup
# =====================================

# FILE: setup_windows.bat
@echo off
echo 🌊 Probaah Setup for Windows (WSL)
echo ================================

echo Checking WSL installation...
wsl --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ WSL not found. Please install WSL first:
    echo    https://docs.microsoft.com/en-us/windows/wsl/install
    pause
    exit /b 1
)

echo ✅ WSL found
echo Running setup in WSL...

wsl bash ./setup.sh

echo ""
echo 🎯 Windows-specific tips:
echo   - Use WSL terminal for Probaah commands
echo   - Files are in: \\wsl$\Ubuntu\home\%USERNAME%\
echo   - VS Code: Install "WSL" extension
echo ""
pause

# =====================================
# SSH Key Setup Helper
# =====================================

# FILE: scripts/setup_ssh.sh
#!/bin/bash
echo "🔐 Setting up SSH keys for Roar Collab"
echo "======================================"

SSH_DIR="$HOME/.ssh"
KEY_NAME="roar_collab_probaah"

# Create .ssh directory if it doesn't exist
mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"

# Generate SSH key if it doesn't exist
if [ ! -f "$SSH_DIR/$KEY_NAME" ]; then
    echo "🔑 Generating new SSH key..."
    ssh-keygen -t ed25519 -f "$SSH_DIR/$KEY_NAME" -C "probaah-$(date +%Y%m%d)"
    echo "✅ SSH key generated"
else
    echo "✅ SSH key already exists"
fi

# Add to SSH config
SSH_CONFIG="$SSH_DIR/config"
if ! grep -q "Host roar-collab" "$SSH_CONFIG" 2>/dev/null; then
    echo ""
    echo "📝 Adding to SSH config..."
    cat >> "$SSH_CONFIG" << EOF

# Probaah - Penn State Roar Collab
Host roar-collab
    HostName submit.aci.ics.psu.edu
    User akp6421
    IdentityFile ~/.ssh/$KEY_NAME
    IdentitiesOnly yes
EOF
    echo "✅ SSH config updated"
fi

echo ""
echo "🚀 Next steps:"
echo "1. Copy your public key:"
echo "   cat $SSH_DIR/$KEY_NAME.pub"
echo ""
echo "2. Add it to Roar Collab:"
echo "   ssh akp6421@submit.aci.ics.psu.edu"
echo "   mkdir -p ~/.ssh"
echo "   echo 'PASTE_YOUR_PUBLIC_KEY_HERE' >> ~/.ssh/authorized_keys"
echo ""
echo "3. Test connection:"
echo "   ssh roar-collab 'echo Connection successful!'"
echo ""
echo "4. Enable in Probaah config:"
echo "   probaah config set cluster.roar_collab.ssh_alias roar-collab"

# =====================================
# Development Helper
# =====================================

# FILE: dev_setup.sh
#!/bin/bash
echo "🛠️  Probaah Development Setup"
echo "============================"

# Install development dependencies
pip install pytest black flake8 mypy

# Set up pre-commit hooks
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
echo "Running code quality checks..."

# Format with black
black --check . || {
    echo "❌ Code formatting issues found. Run: black ."
    exit 1
}

# Lint with flake8
flake8 . || {
    echo "❌ Linting issues found. Fix them and commit again."
    exit 1
}

echo "✅ Code quality checks passed"
EOF

chmod +x .git/hooks/pre-commit

echo "✅ Development environment ready"
echo ""
echo "📋 Development Commands:"
echo "  black .           # Format code"
echo "  flake8 .          # Lint code"  
echo "  pytest            # Run tests"
echo "  python -m probaah.cli.main  # Run CLI directly"
echo ""

# =====================================
# First Run Test Script
# =====================================

# FILE: test_installation.py
#!/usr/bin/env python3
"""Test script to verify Probaah installation"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd):
    """Run command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def test_probaah_installation():
    """Test basic Probaah functionality"""
    
    print("🧪 Testing Probaah Installation")
    print("===============================")
    
    tests = [
        ("CLI accessible", "probaah --version"),
        ("Config init", "probaah config init --user test"),
        ("Project creation", "probaah project create test-install --type reaxff"),
        ("Project listing", "probaah project list"),
    ]
    
    for test_name, command in tests:
        print(f"\n🔍 {test_name}...")
        success, stdout, stderr = run_command(command)
        
        if success:
            print(f"✅ {test_name} - PASSED")
        else:
            print(f"❌ {test_name} - FAILED")
            print(f"   Command: {command}")
            print(f"   Error: {stderr}")
            return False
    
    print("\n🎉 All tests passed! Probaah is ready to use.")
    return True

if __name__ == "__main__":
    # Change to temp directory for testing
    os.chdir("/tmp")
    
    success = test_probaah_installation()
    
    # Cleanup
    test_dirs = [d for d in os.listdir(".") if d.startswith("test-install_")]
    for d in test_dirs:
        os.system(f"rm -rf {d}")
    
    sys.exit(0 if success else 1)
