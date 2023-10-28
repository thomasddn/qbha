FROM python:3.12-slim

# Keep Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turn off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Setup directories
RUN mkdir /app && mkdir /data

# Install pip requirements
COPY requirements.txt /app
RUN python -m pip install -r /app/requirements.txt

# Copy source
COPY src/ /app

# Run app
CMD ["python", "/app/main.py"]
