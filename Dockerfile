FROM smrati/python-uv-slim-bookworm:3.13

WORKDIR /app
COPY pyproject.toml /app/
RUN uv sync
COPY . /app

ENTRYPOINT ["uv", "run"]
CMD ["server.py"]