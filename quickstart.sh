#!/bin/bash
# GuardBot Quick Start Script

set -e  # Exit on error

echo "========================================="
echo "GuardBot Quick Start"
echo "========================================="
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "❗ Please edit .env and add your BOT_TOKEN"
    echo "   nano .env"
    echo ""
    exit 1
fi

# Check if BOT_TOKEN is set
if grep -q "YOUR_TELEGRAM_BOT_TOKEN_HERE" .env; then
    echo "❌ BOT_TOKEN not configured in .env"
    echo "📝 Please edit .env and add your actual bot token"
    echo "   nano .env"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/media data/export logs

# Check if running in Docker or native
if [ -f "/.dockerenv" ]; then
    echo "🐳 Running in Docker container"
    MODE="docker"
else
    echo "🖥️  Running natively"
    MODE="native"
fi

if [ "$MODE" = "native" ]; then
    # Check Python version
    echo "🐍 Checking Python version..."
    if ! command -v python3.12 &> /dev/null; then
        echo "❌ Python 3.12 not found!"
        echo "   Install: sudo apt install python3.12 python3.12-venv"
        exit 1
    fi
    
    # Create virtual environment if not exists
    if [ ! -d "venv" ]; then
        echo "📦 Creating virtual environment..."
        python3.12 -m venv venv
    fi
    
    # Activate venv
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
    
    # Install dependencies
    echo "📥 Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo ""
    echo "========================================="
    echo "✅ Setup complete!"
    echo "========================================="
    echo ""
    echo "🚀 Starting bot..."
    python start_bot.py
else
    echo ""
    echo "========================================="
    echo "✅ Running in Docker"
    echo "========================================="
    echo ""
    exec python start_bot.py
fi
