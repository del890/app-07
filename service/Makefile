.PHONY: install run run-dev build clean test

install:
	uv sync

run-dev:
	@echo "Running service..."
	uv run uvicorn service.main:app --reload --port 8000

build:
	@echo "Building service..."
	docker build -f Dockerfile -t del890/app-007-service .

run:
	docker run -d -p 8000:8000 --env-file ./.env --name app-007-service del890/app-007-service

clean:
	docker rm -f app-007-service
	docker rmi -f del890/app-007-service

test:
	@echo "Running tests on service..."