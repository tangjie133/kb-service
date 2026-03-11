FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY src/ ./src/

# Create data directory
RUN mkdir -p /app/data

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Run
CMD ["python", "-m", "src.api"]
