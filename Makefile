.PHONY: test-client build-client run-client

test-client:
	@echo "Running tests..."


run-dev:
	@echo "Running development environment..."
	cd client && npm run dev

build-client:
	@echo "Building client image..."
	docker build client/. -t del890/app-007

run-client:
	@echo "Running client container..."
	docker run -p 3000:80 --name app-001-client del890/app-001

build-run: build-client run-client

run-service:
	cd ./service && uv run uvicorn service.main:app --reload --port 8000