# Justfile for Python/uv MCP server Docker project
# Works on Windows (PowerShell), Linux, and macOS

# Set shell for Windows
set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

# Variables
image_name := "mlb-injury-scraper"
container_name := "mlb-injury-scraper"
tag := "latest"

# Default recipe - show available commands
default:
    @just --list

# Test that just is working
test-just:
    #!/usr/bin/env sh
    if [ "{{ os() }}" = "windows" ]; then
        powershell -Command "Write-Host 'Hello from Windows PowerShell!'"
    else
        echo "Hello from {{ os() }}!"
    fi

# Build Docker image
build tag=tag:
    #!/usr/bin/env sh
    if [ "{{ os() }}" = "windows" ]; then
        powershell -Command "docker build -t {{ image_name }}:{{ tag }} ."
    else
        docker build -t {{ image_name }}:{{ tag }} .
    fi

# Run MCP server interactively (STDIO)
run tag=tag *args="":
    #!/usr/bin/env sh
    if [ "{{ os() }}" = "windows" ]; then
        powershell -Command "docker run -it --rm --name {{ container_name }} {{ image_name }}:{{ tag }} {{ args }}"
    else
        docker run -it --rm --name {{ container_name }} {{ image_name }}:{{ tag }} {{ args }}
    fi

# Run with port mapping (for future SSE implementation)
run-sse port="8000" tag=tag *args="":
    #!/usr/bin/env sh
    if [ "{{ os() }}" = "windows" ]; then
        powershell -Command "docker run -it --rm -p {{ port }}:{{ port }} --name {{ container_name }} {{ image_name }}:{{ tag }} {{ args }}"
    else
        docker run -it --rm -p {{ port }}:{{ port }} --name {{ container_name }} {{ image_name }}:{{ tag }} {{ args }}
    fi

# Development: run with volume mount
dev tag=tag:
    #!/usr/bin/env sh
    if [ "{{ os() }}" = "windows" ]; then
        powershell -Command "docker run -it --rm -v \"${PWD}:/app\" --name {{ container_name }} {{ image_name }}:{{ tag }}"
    else
        docker run -it --rm -v "$(pwd):/app" --name {{ container_name }} {{ image_name }}:{{ tag }}
    fi

# Stop and cleanup
stop:
    #!/usr/bin/env sh
    if [ "{{ os() }}" = "windows" ]; then
        powershell -Command "docker stop {{ container_name }} 2>$null; docker rm {{ container_name }} 2>$null"
    else
        docker stop {{ container_name }} 2>/dev/null; docker rm {{ container_name }} 2>/dev/null
    fi

# Show container logs
logs:
    #!/usr/bin/env sh
    if [ "{{ os() }}" = "windows" ]; then
        powershell -Command "docker logs {{ container_name }}"
    else
        docker logs {{ container_name }}
    fi

# Clean up Docker images and containers
clean:
    #!/usr/bin/env sh
    if [ "{{ os() }}" = "windows" ]; then
        powershell -Command "docker system prune -f"
    else
        docker system prune -f
    fi