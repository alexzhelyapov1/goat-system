# Base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Create a directory for the shared database
RUN mkdir /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .