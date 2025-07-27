# Adobe India Hackathon 2025 - Challenge 1a: PDF Processing Solution
# Platform: linux/amd64 (required for compatibility)
FROM --platform=linux/amd64 python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model for multilingual support
RUN python -m spacy download xx_core_news_sm

# Copy source code
COPY src/ ./src/
COPY process_pdfs.py .
COPY docker_test.py .

# Create input and output directories
RUN mkdir -p /app/input /app/output

# Test the environment (optional - can be commented out for production)
# RUN python docker_test.py

# Set the default command
CMD ["python", "process_pdfs.py"] 