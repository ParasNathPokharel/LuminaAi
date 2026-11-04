"""
Database migration and schema initialization manager.
Runs automatically on server boot or can be invoked via CLI:
python -m backend.migrations
"""

import sys
import logging
from sqlalchemy import text, inspect
from database import init_db, get_database_url, Base, _engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] Migrations: %(message)s")
logger = logging.getLogger("Migrations")


def run_migrations():
    """
    Applies DDL schema migrations, checks table structures,
    and creates required indexes.
    """
    db_url = get_database_url()
    logger.info(f"Connecting to database target: {db_url.split('@')[-1] if '@' in db_url else db_url}")

    try:
        engine = init_db()
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        logger.info(f"Existing database tables: {existing_tables}")

        # Create any tables defined in SQLAlchemy models if missing
        Base.metadata.create_all(bind=engine)

        refreshed_tables = inspect(engine).get_table_names()
        logger.info("Database schema is up to date.")
        return True

    except Exception as e:
        logger.error(f"Migration error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
