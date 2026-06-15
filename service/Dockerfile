# Use a slim image for smaller production footprints
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and install the package
COPY service/ .
RUN pip install --no-cache-dir .

# Copy dataset files from the project root
COPY data.json data.json
COPY mega-sena.json mega-sena.json

# Tell the service where to find the dataset
ENV DATA_JSON_PATH=/app/data.json

# Expose the port
EXPOSE 8000

# Use Gunicorn as the entry point, using Uvicorn as the worker class
CMD ["gunicorn", "service.main:app", \
     "-w", "1", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000"]