"""
Storage and Database Backup & Recovery Utility.
Archives database and persistent image storage into timestamped zip bundles.
"""

import os
import sys
import time
import zipfile
import shutil
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] Backup: %(message)s")
logger = logging.getLogger("Backup")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
STORAGE_DIR = os.environ.get("STORAGE_DIR", os.path.join(PROJECT_ROOT, "storage"))
BACKUPS_DIR = os.path.join(PROJECT_ROOT, "backups")


def create_backup(dest_folder: str = BACKUPS_DIR) -> str:
    """Creates a compressed archive of persistent storage and database files."""
    os.makedirs(dest_folder, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"lumina_backup_{timestamp}.zip"
    backup_path = os.path.join(dest_folder, backup_filename)

    logger.info(f"Creating backup archive: {backup_path}")
    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        if os.path.exists(STORAGE_DIR):
            for root, _, files in os.walk(STORAGE_DIR):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, STORAGE_DIR)
                    zipf.write(full_path, arcname=os.path.join("storage", rel_path))

    size_mb = os.path.getsize(backup_path) / (1024 * 1024)
    logger.info(f"Backup created successfully: {backup_filename} ({size_mb:.2f} MB)")
    return backup_path


def restore_backup(archive_path: str, target_dir: str = STORAGE_DIR) -> bool:
    """Restores persistent storage from a zip backup archive."""
    if not os.path.exists(archive_path):
        logger.error(f"Archive not found: {archive_path}")
        return False

    logger.info(f"Restoring backup from {archive_path} to {target_dir}...")
    with zipfile.ZipFile(archive_path, 'r') as zipf:
        for member in zipf.namelist():
            if member.startswith("storage/"):
                rel_path = member[len("storage/"):]
                if not rel_path:
                    continue
                dest_path = os.path.join(target_dir, rel_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                with zipf.open(member) as source, open(dest_path, "wb") as target:
                    shutil.copyfileobj(source, target)

    logger.info("Restore completed successfully.")
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "restore" and len(sys.argv) > 2:
        restore_backup(sys.argv[2])
    else:
        create_backup()
