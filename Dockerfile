FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir ".[full]"

EXPOSE 8000
CMD ["sh", "-c", "engram-forge serve-http --host 0.0.0.0 --port ${PORT:-8000}"]
