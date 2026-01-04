#!/bin/bash

# AAAI-26 Talent Hunter - Quick Start Script

echo "=========================================="
echo "  AAAI-26 Talent Hunter"
echo "  Multi-Agent Service System"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "✅ .env file created"
    echo "⚠️  Please edit .env and add your SILICONFLOW_API_KEY"
    echo ""
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt -q

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "🚀 Starting FastAPI server..."
echo ""
echo "📡 API will be available at:"
echo "   - http://localhost:8000"
echo "   - Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python app/main.py

