#!/bin/bash
# Start KB Service

set -e

echo "Starting Knowledge Base Service..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

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

# Set Python path (for non-venv installs)
export PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH}"

# Start service
echo "Starting API server..."
python -m src.api
