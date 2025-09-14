FROM python:3.12-slim

WORKDIR /app

# Upgrade pip and install build dependencies
RUN pip install --upgrade pip

# Copy only dependency files first for better caching
COPY pyproject.toml /app/

# Install dependencies
RUN pip install --no-cache-dir .

# Copy the rest of the source code
COPY . /app

CMD ["python", "server.py"]