# Justfile for Python/uv MCP server Docker project
# Works on Windows (PowerShell), Linux, and macOS

# Set shell for Windows
set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

# Variables
image_name := "mlb-injury-scraper"
container_name := "mlb-injury-scraper-container"
tag := "latest"

# Default recipe - show available commands
default:
    @just --list

# Build Docker image
build tag=tag:
    docker build -t {{ image_name }}:{{ tag }} .

# Run MCP server interactively (STDIO)
run tag=tag *args="":
    docker run -it --rm --name {{ container_name }} {{ image_name }}:{{ tag }} {{ args }}

# Stop and cleanup
stop:
    -docker stop {{ container_name }}
    -docker rm {{ container_name }}

# Show container logs
logs:
    docker logs {{ container_name }}

# Run locally with uv (syncs if needed)
uv-run:
    #!/usr/bin/env sh
    if [ "{{ os() }}" = "windows" ]; then
        powershell -Command "if (!(Test-Path '.venv')) { Write-Host 'No .venv found, running uv sync first...'; uv sync }; uv run server.py"
    else
        if [ ! -d ".venv" ]; then
            echo "No .venv found, running uv sync first..."
            uv sync
        fi
        uv run server.py
    fi

# Clean up project-specific Docker artifacts
clean:
    -docker stop {{ container_name }}
    -docker rm {{ container_name }}
    -docker rmi {{ image_name }}:{{ tag }}
    -docker rmi {{ image_name }}:latest