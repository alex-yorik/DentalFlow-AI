.PHONY: help install lint typecheck test build clean

help:
	@echo "install    — Install dev dependencies"
	@echo "lint       — Run ruff linter"
	@echo "typecheck  — Run mypy type checker"
	@echo "test       — Run pytest"
	@echo "build      — Build Docker image"
	@echo "clean      — Remove __pycache__"

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

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true