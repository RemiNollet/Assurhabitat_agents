.PHONY: setup run all test test-verbose test-coverage test-agents test-tools test-fast clean-test

# =========================
# Environment variables
# Mandatory: create .env file with variables HF_TOKEN, LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_BASE_URL
# =========================
include .env 

# =========================
# Setup project
# =========================
setup:
	pip install -r requirements.txt

# =========================
# Run project
# =========================
run:
	export HF_TOKEN=$(HF_TOKEN) && \
	export LANGFUSE_SECRET_KEY=$(LANGFUSE_SECRET_KEY) && \
	export LANGFUSE_PUBLIC_KEY=$(LANGFUSE_PUBLIC_KEY) && \
	export LANGFUSE_BASE_URL=$(LANGFUSE_BASE_URL) && \
	cd src && python -m assurhabitat_agents.main

eval:
	cd src
	python ../eval/run_evaluation.py 

# =========================
# Testing
# =========================

# Run all tests
test:
	pytest tests/

# Run tests with verbose output
test-verbose:
	pytest tests/ -v

# Run tests with coverage report
test-coverage:
	pytest tests/ --cov=src/assurhabitat_agents --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/index.html"

# Run only agent tests
test-agents:
	pytest tests/agents/ -v

# Run only tool tests
test-tools:
	pytest tests/tools/ -v

# Run tests without slow tests
test-fast:
	pytest tests/ -m "not slow"

# Clean test artifacts
clean-test:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# =========================
# Setup + Run
# =========================
all: setup run
