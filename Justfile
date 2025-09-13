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

# Test that just is working
test-just:
    @echo "Hello from {{ os() }}!"

# Build Docker image
build tag=tag:
    docker build -t {{ image_name }}:{{ tag }} .

# Run MCP server interactively (STDIO)
run tag=tag *args="":
    docker run -it --rm --name {{ container_name }} {{ image_name }}:{{ tag }} {{ args }}

# Run with port mapping (for future SSE implementation)
run-sse port="8000" tag=tag *args="":
    docker run -it --rm -p {{ port }}:{{ port }} --name {{ container_name }} {{ image_name }}:{{ tag }} {{ args }}

# Development: run with volume mount
dev tag=tag:
    docker run -it --rm -v "{{ justfile_directory() }}:/app" --name {{ container_name }} {{ image_name }}:{{ tag }}

# Stop and cleanup
stop:
    -docker stop {{ container_name }}
    -docker rm {{ container_name }}

# Show container logs
logs:
    docker logs {{ container_name }}

# Clean up project-specific Docker artifacts
clean:
    -docker stop {{ container_name }}
    -docker rm {{ container_name }}
    -docker rmi {{ image_name }}:{{ tag }}
    -docker rmi {{ image_name }}:latest