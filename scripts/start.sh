#!/bin/bash
# Start KB Service

set -e

echo "Starting Knowledge Base Service..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Load proxy settings from .env if exists
if [ -f ".env" ]; then
    export $(grep -E '^(HTTP_PROXY|HTTPS_PROXY|ALL_PROXY)=' .env | xargs)
    if [ -n "$HTTP_PROXY" ]; then
        echo "Using proxy: $HTTP_PROXY"
    fi
fi

# Check virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d "$PROJECT_DIR/venv" ]; then
        echo "Activating virtual environment..."
        source "$PROJECT_DIR/venv/bin/activate"
    else
        echo "Warning: No virtual environment found."
        echo "It's recommended to use a virtual environment."
        echo "Run: python3 -m venv venv && source venv/bin/activate"
    fi
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "Error: Ollama is not running!"
    echo "Please start Ollama first:"
    echo "  ollama serve"
    exit 1
fi

# Check if required models exist
echo "Checking Ollama models..."
if ! ollama list | grep -q "nomic-embed-text"; then
    echo "Pulling nomic-embed-text..."
    ollama pull nomic-embed-text
fi

if ! ollama list | grep -q "qwen2.5"; then
    echo "Pulling qwen2.5..."
    ollama pull qwen2.5
fi

# Create directories
mkdir -p data/vector_db
mkdir -p knowledge

# Check/Clone knowledge base
echo "Checking knowledge base..."
if [ ! -d "knowledge/.git" ]; then
    echo "Knowledge base not found, cloning from GitHub..."
    rm -rf knowledge
    # Use proxy if configured
    if [ -n "$ALL_PROXY" ]; then
        git config --global http.proxy "$HTTP_PROXY"
        git config --global https.proxy "$HTTPS_PROXY"
    fi
    git clone https://github.com/tangjie133/knowledge-base.git knowledge
    echo "Knowledge base cloned successfully"
else
    echo "Knowledge base exists, pulling latest updates..."
    cd knowledge && git pull && cd ..
fi

# Set Python path (for non-venv installs)
export PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH}"

# Start service
echo "Starting API server..."
python -m src.api
