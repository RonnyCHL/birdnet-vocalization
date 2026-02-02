FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir psycopg2-binary

# Copy server
COPY feedback_server.py .

# Expose port
EXPOSE 8089

# Run server
CMD ["python", "feedback_server.py", "--port", "8089"]
