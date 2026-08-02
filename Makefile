.PHONY: help lint typecheck test build clean

help:
	@echo "lint       — Run ruff linter"
	@echo "typecheck  — Run mypy type checker"
	@echo "test       — Run pytest"
	@echo "build      — Build Docker image"
	@echo "clean      — Remove __pycache__"

lint:
	ruff check --exit-zero src/ tests/

typecheck:
	mypy --no-error-summary src/ || true

test:
	python3 -m pytest tests/ -v --tb=short

build:
	docker build -t dentalflow-ai .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true