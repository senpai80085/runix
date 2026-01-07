# Runix Cloud Run Dockerfile
# Optimized for free tier (minimal image size)

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first (layer caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY runix/ ./runix/
COPY templates/ ./templates/
COPY local_server.py .

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Run the local dashboard server
CMD ["python", "local_server.py"]
