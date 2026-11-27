
# 1. Use Python base image
FROM python:3.12-slim

# 2. Set working directory
WORKDIR /app

# 3. Prevent Python from generating bytecode
ENV PYTHONDONTWRITEBYTECODE=1

# 4. Ensure Python logs are sent directly to the terminal
ENV PYTHONUNBUFFERED=1

# 5. Copy dependency file
COPY requirements.txt .

# 6. Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 7. Copy application code
COPY . .

# 8. Expose application port
EXPOSE 8000

# 9. Start Gunicorn with Uvicorn workers
CMD ["gunicorn", "main:app", "--workers", "4", "--worker-class", "uvicorn_worker.UvicornWorker", "--bind", "0.0.0.0:8000"]
