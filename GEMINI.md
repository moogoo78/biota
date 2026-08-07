# GEMINI.md

This file provides guidance for working with the Biota application.

## Overview

Biota is a Flask-based taxonomic data management system designed for biological specimen collection and nomenclature handling. It integrates with external taxonomy APIs (such as GBIF, TaiCOL, Tai2, TBIA) and provides tools for creating taxonomic checklists and generating Word documents.

## Architecture

### Core Components

- **Flask Application**: The core of the application is a Flask server, with the main application factory located in `app/application.py`. It uses a blueprint-based architecture to organize routes and logic.
- **Database Layer**: The application uses PostgreSQL as its database, with SQLAlchemy as the ORM. Database migrations are handled by Alembic.
- **External API Integration**: The system interfaces with various external services like GBIF, TaiCOL, Tai2, and TBIA to fetch and process taxonomic data.
- **Document Generation**: It can generate Word documents for taxonomic publications using the `python-docx` library.

### Key Files

- `app/application.py`: Contains the Flask application factory and configuration setup.
- `app/blueprints/api.py`: Defines the main API endpoints for internal and external data.
- `app/models.py`: Defines the SQLAlchemy models for the PostgreSQL database.
- `app/helpers.py`: Includes core business logic for data processing and document generation.
- `app/database.py`: Handles the database connection setup.
- `wsgi.py`: The WSGI entry point for running the application in production.
- `compose.yml`: The main Docker Compose file for setting up the development and production environments.

## Development

### Database Migrations

The project uses Flask-Migrate (which wraps Alembic) to handle database migrations.

- **To create a new migration:**
  ```bash
  flask db migrate -m "Your migration message"
  ```

- **To apply migrations:**
  ```bash
  flask db upgrade
  ```

### Running the Application

The application can be run using Docker Compose.

- **To start the development environment:**
  ```bash
  docker-compose up
  ```

- **To run in a specific environment (e.g., production):**
  ```bash
  WEB_ENV=prod docker-compose -f compose.yml -f compose.prod.yml up
  ```

### User Management

- **To create a new user:**
  ```bash
  flask create-user <username> <email> <password>
  ```

## Configuration

The application's configuration is managed in `app/config.py` and is based on the `WEB_ENV` environment variable.

- `DevelopmentConfig`: Used when `WEB_ENV` is set to `dev`.
- `ProductionConfig`: Used when `WEB_ENV` is set to `prod`.

Key environment variables include:
- `WEB_ENV`: The environment (`dev` or `prod`).
- `SECRET_KEY`: The secret key for Flask (used in production).
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`: Parameters for the PostgreSQL connection.

## API Endpoints

### External Data Sources

- `/api/external/names/<source>/<key>`: Searches for taxonomic names from external sources.
- `/api/external/data/<source>/<taxon_key>`: Retrieves specimen or occurrence data.
- **Supported Sources**: `gbif`, `taicol`, `tai2`, `tbia`, and others.

### Internal Data

- `/api/publish`: Generates a Word document from namespace data.
- `/preview/<int:namespace_id>`: Provides a preview interface for the data.

## Core Logic

### Data Processing (`app/helpers.py`)

The `get_namespace_data()` function is a key part of the application. It is responsible for:
- Fetching taxonomic names, synonyms, and literature from the database.
- Processing and formatting specimen data.
- Handling type specimens with detailed locality and collection information.

### Document Generation (`app/helpers.py`)

The `generate_docx()` function creates scientific publications with:
- A multi-column layout for taxonomic lists.
- Proper formatting for scientific names, synonyms, and specimens.
- Handling of literature citations and references.
