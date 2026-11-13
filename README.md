# FreshCart Pipelines

This repository contains a compact end-to-end data engineering project centered on the FreshCart case study. It includes an ELT pattern for Snowflake-style transformations, an Iris-based ML pipeline, and a RabbitMQ event-streaming exercise.

## Project structure

- `elt/` – ELT SQL and notebook-style workflow for FreshCart batch processing.
- `iris_project/` – Python package and Mage-compatible pipeline assets for the Iris classification workflow.
- `stream/` – RabbitMQ publisher/consumer scripts for routing tests.
- `tests/` – Automated pytest checks for the data preparation logic.
- `.github/workflows/ci.yml` – Continuous integration workflow.

## Installation

```bash
python -m venv .venv
. .venv/bin/activate   # On Windows use .venv\Scripts\activate
pip install -r requirements.txt
```

## Local test run

```bash
pytest -q
```

## Architecture overview

1. FreshCart data is staged from raw sources into a bronze layer.
2. Validation and normalization occur in a silver layer.
3. Business logic creates dim/fact tables and gold metrics.
4. ML training uses the Iris dataset via a Mage-style pipeline.
5. Event traffic is simulated with RabbitMQ topic exchange routing.

## External service notes

Some assignment items require external systems such as Snowflake, Mage, and RabbitMQ. This repository includes the logic and project structure, but the actual cloud and broker services must be configured outside this repo using environment variables and credentials not stored in Git.

## CI

GitHub Actions runs `pytest` automatically on every push.
