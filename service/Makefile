.PHONY: test-client build-client run-client

build:
	docker build -f Dockerfile -t del890/app-007-service ..

run:
	docker run -d -p 5000:8000 --env-file ../.env -e DATA_JSON_PATH=/app/data.json --name app-007-service del890/app-007-service

run-dev:
	uv run uvicorn service.main:app --reload --port 8000


dclean:
	docker rm -f app-007-service
	docker rmi -f del890/app-007-service