FROM python:3.11-slim

WORKDIR /app

# Create data directory for database
RUN mkdir -p /app/data

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Run the bot
CMD ["python", "-m", "src.main"]
