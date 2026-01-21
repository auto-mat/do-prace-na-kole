# Minimal Locust Dockerfile for load testing with latest stable version

FROM python:3.12-slim

WORKDIR /app

# Install Locust (latest stable version as of April 2025)
RUN pip install --no-cache-dir locust==2.34.1

# Copy Locust test files
COPY locustfile.py .
COPY DSC00002.JPG .


# Expose Locust web UI port
EXPOSE 8089

# Default command: run Locust in web UI mode
CMD ["locust", "-f", "locustfile.py", "--host", "http://your-app-host"]
