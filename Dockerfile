FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip setuptools wheel

# Create user
RUN useradd -u 1000 -m appuser

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /tmp/uploads && \
    mkdir -p /app/audio && \
    chown -R appuser:appuser /tmp/uploads && \
    chown -R appuser:appuser /app/audio

# Copy application code
COPY app/ ./app/

# Set all permissions
RUN chown -R appuser:appuser /app

# Run the application with lower privileges
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/.local/bin:$PATH"

# Expose port
EXPOSE 8049

# Run the application
CMD ["python", "app/main.py"]
