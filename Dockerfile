FROM python:3.10-slim

# Keep Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turn off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Setup directories
RUN mkdir /app && mkdir /data

# Create a non-root user with an explicit UID and adds permission to access the /app folder
RUN adduser -u 5678 --disabled-password --gecos "" appuser && \
    chown -R appuser /app && \
    chown -R appuser /data
USER appuser

# Install pip requirements
COPY requirements.txt /app
RUN python -m pip install -r /app/requirements.txt

# Copy source
COPY src/ /app

# Run app
CMD ["python", "/app/main.py"]
