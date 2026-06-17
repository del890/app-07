CLIENT_DIR := client
SERVICE_DIR := service

.PHONY: help install build run run-dev test clean \
	client-install client-build client-run client-run-dev client-test client-clean client-clean-deps \
	service-install service-build service-run service-run-dev service-test service-clean

help:
	@echo "Available targets: install, build, run, run-dev, test, clean"
	@echo "Run specific sub-targets with 'make client-<target>' or 'make service-<target>'"
## Install dependencies for both projects
install: client-install service-install

client-install:
	$(MAKE) -C $(CLIENT_DIR) install

service-install:
	$(MAKE) -C $(SERVICE_DIR) install

## Build both projects
build: client-build service-build

client-build:
	$(MAKE) -C $(CLIENT_DIR) build

service-build:
	$(MAKE) -C $(SERVICE_DIR) build

## Run both projects (note: these may be blocking)
run: client-run service-run

client-run:
	$(MAKE) -C $(CLIENT_DIR) run

service-run:
	$(MAKE) -C $(SERVICE_DIR) run

## Run development servers in parallel
run-dev:
	@echo "Starting client and service development servers (in separate terminals)..."
	@$(MAKE) -C $(CLIENT_DIR) run-dev &
	@$(MAKE) -C $(SERVICE_DIR) run-dev &

## Tests
test: client-test service-test

client-test:
	$(MAKE) -C $(CLIENT_DIR) test

service-test:
	$(MAKE) -C $(SERVICE_DIR) test

## Cleanup
clean: client-clean service-clean

client-clean:
	$(MAKE) -C $(CLIENT_DIR) clean

client-clean-deps:
	$(MAKE) -C $(CLIENT_DIR) clean-deps

service-clean:
	$(MAKE) -C $(SERVICE_DIR) clean


