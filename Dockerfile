# Use Python 3.11 slim as the base image
FROM python:3.11-slim

# Install system dependencies for Tesseract, OpenCV, and other requirements
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements.txt first to leverage Docker caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the Flask port for keep-alive
EXPOSE 10000

# Set environment variable for Tesseract (optional, for clarity)
ENV TESSERACT_CMD=/usr/bin/tesseract

# Command to run the bot
CMD ["python", "main.py"]
