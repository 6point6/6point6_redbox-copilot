# 📮 Redbox Copilot

Redbox Copilot is a retrieval augmented generation (RAG) app that uses Claude 2 to organise, categorise and summarise civil service documents. It's designed to handle a variety of administrative sources, such as letters, briefings, minutes, and speech transcripts.

- **Better retrieval**. Redbox Copilot increases organisational memory by indexing documents
- **Faster, accurate summarisation**. Redbox Copilot can summarise reports read months ago, supplement them with current work, and produce a first draft that lets civil servants focus on what they do best

# Local Dev Setup

The entire architecture runs in docker compose for local development. This includes locally hosting the app, databases, object store and orchestration. Therefore, you will need docker installed.

## First time setup

You will need to create a copy of the `.env.example` file as `.env` to store your secrets, such as your Anthropic API key (ask the team for the keys). The `.env` file should not be committed to GitHub.

If you have issues with permissions, you may need to run `chmod 777 data/elastic/` to be able to write to the folder.

## To run

You can simply run:

`docker compose up` or `make run`

You'll find a series of useful `docker compose` commands already maded in [`Makefile`](./Makefile)

Any time you update code for the the repo, you'll likely need to rebuild the containers.

# Codespace

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/i-dot-ai/redbox-copilot?quickstart=1)

# Development

- Download and install [pre-commit](https://pre-commit.com) to benefit from pre-commit hooks
  - `pip install pre-commit`
  - `pre-commit install`
