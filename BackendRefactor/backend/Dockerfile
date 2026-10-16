# Use a lightweight Python base image (includes PyTorch runtime)
FROM pytorch/pytorch:2.9.0-cuda12.8-cudnn9-runtime

WORKDIR /app

# Install dependencies first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

EXPOSE 5000

# Run Gunicorn with 2 workers + sane timeouts
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "--timeout", "120", "--graceful-timeout", "30", "--max-requests", "200", "--max-requests-jitter", "50", "app:app"]