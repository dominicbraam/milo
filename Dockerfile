FROM python:3.11.2-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    libffi-dev libnacl-dev python3-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files (including .env)
COPY . .

CMD ["python", "main.py"]
