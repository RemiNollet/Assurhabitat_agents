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
	pip install curl unzip
	mkdir -p ../data
	curl -L -o ../data/attachments.zip https://blent-learning-user-ressources.s3.eu-west-3.amazonaws.com/projects/00ba97/attachments.zip
	unzip -o ../data/attachments.zip -d ../data/
	rm -f ../data/attachments.zip

# =========================
# Run project
# =========================
run:
	export HF_TOKEN=$(HF_TOKEN) && \
	export LANGFUSE_SECRET_KEY=$(LANGFUSE_SECRET_KEY) && \
	export LANGFUSE_PUBLIC_KEY=$(LANGFUSE_PUBLIC_KEY) && \
	export LANGFUSE_BASE_URL=$(LANGFUSE_BASE_URL) && \
	cd src && python -m assurhabitat_agents.main

# =========================
# Setup + Run
# =========================
all: setup run