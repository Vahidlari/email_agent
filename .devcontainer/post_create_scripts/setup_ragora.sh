#!/bin/bash

# Post-create script for setting up ragora environment
# This script installs ragora and configures the PATH environment variable

set -e  # Exit on any error

echo "🚀 Setting up ragora environment..."

# Install ragora package
echo "📦 Installing ragora package..."
pip install ragora

# Add /home/vscode/.local/bin to PATH in bashrc
echo "🔧 Configuring PATH environment variable..."
echo 'export PATH="/home/vscode/.local/bin:$PATH"' >> ~/.bashrc

# Also add to current session
export PATH="/home/vscode/.local/bin:$PATH"

# Verify installation
echo "✅ Verifying ragora installation..."
if command -v ragora &> /dev/null; then
    echo "✅ ragora CLI is now available!"
    ragora --help | head -5
else
    echo "❌ ragora CLI not found after installation"
    exit 1
fi

echo "🎉 ragora setup completed successfully!"

