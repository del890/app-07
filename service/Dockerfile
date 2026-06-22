# Use a slim image for smaller production footprints
FROM python:3.11-slim

# Copy the UV binary from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# Set working directory
WORKDIR /app

# Copy application code and install the dependencies
COPY . .
RUN uv sync --no-cache --no-dev

# Dataset files live inside the service data folder and are copied with the service sources.
# Tell the service where to find the dataset
ENV DATA_JSON_PATH=/app/data/data.json

# Expose the port
EXPOSE 8000

# Use Gunicorn as the entry point, using Uvicorn as the worker class

CMD ["uv", "run", "gunicorn", "service.main:app", \
     "-w", "1", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000"]