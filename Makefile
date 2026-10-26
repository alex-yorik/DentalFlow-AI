.PHONY: help init demo install lint typecheck test build certs clean

help:
	@echo "init       — Create data/, copy .env.example to .env if missing"
	@echo "demo       — Build and start web + nginx, wait for health"
	@echo "install    — Install dev dependencies"
	@echo "lint       — Run ruff linter"
	@echo "typecheck  — Run mypy type checker"
	@echo "test       — Run pytest"
	@echo "build      — Build Docker image"
	@echo "certs      — Generate self-signed TLS certificates for local use"
	@echo "clean      — Remove __pycache__"

init:
	mkdir -p data
	@test -f .env || (cp .env.example .env && echo ">>> Created .env: set OPENAI_API_KEY (and other values) in it")
	@if [ "$$(id -u)" != "1000" ]; then echo ">>> Containers run as UID 1000. If the app cannot write to data/, run: sudo chown -R 1000:1000 data/"; fi

demo: init certs
	docker compose up -d --build --wait web nginx

install:
	python3 -m pip install -r requirements-dev.txt

lint:
	ruff check src/ tests/

typecheck:
	mypy src/

test:
	python3 -m pytest tests/ -v --tb=short --cov=src --cov-report=term-missing

build:
	docker build -t dentalflow-ai .

certs:
	mkdir -p docker/certs
	openssl req -x509 -nodes -newkey rsa:2048 -days 365 -subj "/CN=localhost" \
		-keyout docker/certs/privkey.pem -out docker/certs/fullchain.pem

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true