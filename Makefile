.PHONY: setup run all

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
# Setup + Run
# =========================
all: setup run
