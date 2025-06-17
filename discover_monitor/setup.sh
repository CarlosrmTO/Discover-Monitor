#!/bin/bash

# Create a virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
echo "Installing required packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Create data directory
echo "Creating data directory..."
mkdir -p data

# Make the script executable
chmod +x main.py

echo """
Setup complete!

Next steps:
1. Get Google Search Console API credentials:
   - Go to https://console.cloud.google.com/
   - Create a new project and enable the Search Console API
   - Create OAuth 2.0 credentials and download the JSON file
   - Save it as 'credentials.json' in this directory

2. Run the monitor:
   python main.py

For more options, see the README.md file.
"""
