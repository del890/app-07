.PHONY: install run run-dev build clean test clean-deps

install:
	npm install

run-dev:
# Check if the client dependencies are installed, if not, install them first
	@echo "Checking if client dependencies are installed..."
	npm list > /dev/null || (echo "Installing client dependencies..." && npm install)
	@echo "Running development environment..."
	npm run dev

build:
	@echo "Building client image..."
	docker build . -t del890/app-007

run:
# Needs to check if an image is already built, if not, build it first
	@echo "Checking if client image is built..."
	docker images -q del890/app-007 > /dev/null || (echo "Building client image..." && docker build . -t del890/app-007)
	@echo "Running client container..."
	docker run -p 3000:80 --name app-007 del890/app-007

	
test:
	@echo "Running tests..."

clean:
	docker rm -f app-007
	docker rmi -f del890/app-007

clean-deps: clean
	rm -rf node_modules
	npm cache clean --force