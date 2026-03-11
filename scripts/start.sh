#!/bin/bash
# Start KB Service

set -e

echo "Starting Knowledge Base Service..."

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

# Start service
echo "Starting API server..."
cd "$(dirname "$0")/.."
python -m src.api
