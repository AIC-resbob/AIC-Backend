FROM python:3.12-slim

# Install system dependencies required by LightGBM
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Set working directory to src for module resolution
WORKDIR /app/src

EXPOSE 7700

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7700"]