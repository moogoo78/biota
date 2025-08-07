# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Biota is a Flask-based taxonomic data management system for biological specimen collection and nomenclature handling. The application integrates with multiple external taxonomy APIs (GBIF, TaiCOL, Tai2, TBIA) and provides tools for creating taxonomic checklists and generating Word documents.

## Architecture

### Core Components

- **Flask Application**: Main app in `app/application.py` with blueprint-based architecture
- **Database Layer**: Dual database setup using PostgreSQL (SQLAlchemy ORM) and MySQL (direct PyMySQL connections)
- **External API Integration**: Interfaces with GBIF, TaiCOL, Tai2, and TBIA for taxonomic data
- **Document Generation**: Creates Word documents using python-docx for taxonomic publications

### Key Files

- `app/application.py`: Flask app factory and configuration
- `app/blueprints/main.py`: Main blueprint with API endpoints and data retrieval logic
- `app/models.py`: SQLAlchemy models for PostgreSQL database
- `app/helpers.py`: Core business logic for namespace data processing and document generation
- `app/database.py`: Database connection setup
- `wsgi.py`: WSGI entry point for production

### Database Architecture

The application uses two databases:
1. **PostgreSQL** (`biota` database): SQLAlchemy ORM models for application data
2. **MySQL** (`taicol` database): Direct PyMySQL connections for legacy taxonomic data

Key PostgreSQL tables include `User`, `Item`, `Collection`, `Publication`, and related entities with proper relationships and mixins for timestamps and source tracking.

## Development Commands

### Database Operations
```bash
# Create database migrations
flask makemigrations "migration message"

# Apply migrations
flask migrate

# Create user account
flask createuser <username> <email> <password>
```

### Docker Development
```bash
# Start development environment
docker-compose up

# Start with specific environment
WEB_ENV=dev docker-compose up
WEB_ENV=prod docker-compose up
```

### Application Startup
- **Development**: `flask run --host 0.0.0.0` (WEB_ENV=dev)
- **Production**: `gunicorn --bind 0.0.0.0:8001 wsgi:app`

## Configuration

Environment-based configuration in `app/config.py`:
- `Config`: Base configuration
- `DevelopmentConfig`: Debug mode enabled
- `ProductionConfig`: Production settings with environment-based secrets
- `TestingConfig`: Testing configuration

Key environment variables:
- `WEB_ENV`: Environment (dev/prod)
- `SECRET_KEY`: Flask secret key (production)
- `POSTGRES_*`: PostgreSQL connection parameters

## API Endpoints

### External Data Sources
- `/api/external/names/<source>/<key>`: Search taxonomic names from external sources
- `/api/external/data/<source>/<taxon_key>`: Retrieve specimen/occurrence data
- Supported sources: `gbif`, `taicol`, `tai2`, `tbia`, `nametool`, `pass`

### Internal Data
- `/api/namespaces/<namespace_ids>`: Get namespace data for document generation
- `/api/publish`: Generate Word documents from namespace data
- `/preview` and `/preview2/<int:namespace_id>`: Preview interfaces

## Key Business Logic

### Namespace Data Processing (`helpers.py:164`)
The `get_namespace_data()` function is central to the application:
- Fetches taxonomic names, synonyms, and literature from MySQL
- Processes specimen data with complex formatting rules
- Handles type specimens with detailed locality and collection information
- Formats display names following taxonomic conventions

### Document Generation (`helpers.py:94`)
The `generate_docx()` function creates scientific publications:
- Multi-column layout for taxonomic lists
- Proper formatting for scientific names, synonyms, and specimens
- Literature citations and reference handling

## Database Connection Patterns

- **SQLAlchemy**: Use `session` from `app.database` for PostgreSQL operations
- **MySQL**: Use `get_db_connection()` and Flask's `g` object for connection management
- Connection teardown is handled in `app/application.py:108`

## External API Integration

The application integrates with several taxonomic databases with specific data formatting and CORS handling. Each source has unique response structures and requires different parsing logic in `app/blueprints/main.py`.

## Development Notes

- Client-side code was removed (deleted `client/` directory)
- Static assets are served from `app/static/`
- Templates use Jinja2 with base template inheritance
- The application handles both specimen data and nomenclatural information
- Geographic data uses Taiwan county mappings for locality standardization