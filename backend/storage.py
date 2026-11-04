"""
Persistent Image Storage Manager.
Manages disk storage for uploaded originals, processed transparent cutouts,
and multi-format exports. Ensures synchronization between database records and filesystem.
"""

import os
import shutil
import logging
import gc
import time
from typing import Optional, Tuple
from PIL import Image

logger = logging.getLogger("StorageManager")

def _safe_rmtree(path: str, max_retries: int = 4, delay: float = 0.15) -> bool:
    """Safely removes directory tree with retry and garbage collection for Windows."""
    if not os.path.exists(path):
        return True
    gc.collect()
    for attempt in range(max_retries):
        try:
            shutil.rmtree(path)
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                gc.collect()
                time.sleep(delay)
            else:
                logger.error(f"Failed to delete directory {path} after {max_retries} attempts: {e}")
                return False
    return False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
DEFAULT_STORAGE_ROOT = os.path.abspath(os.environ.get("STORAGE_DIR", os.path.join(PROJECT_ROOT, "storage")))


class StorageManager:
    """
    Manages persistent image files organized in a structured hierarchy:
    storage/
       ├── users/
       │    └── <user_id>/
       │         └── <image_id>/
       │              ├── original.<ext>
       │              ├── cutout.png
       │              └── exports/
       │                   ├── export_jpg_1.jpg
       │                   └── export_svg_1.svg
       └── guests/
            └── <guest_session_id>/
                 └── <image_id>/
                      ├── original.<ext>
                      ├── cutout.png
                      └── exports/
    """

    def __init__(self, root_dir: str = DEFAULT_STORAGE_ROOT):
        self.root_dir = os.path.abspath(root_dir)
        os.makedirs(self.root_dir, exist_ok=True)
        os.makedirs(os.path.join(self.root_dir, "users"), exist_ok=True)
        os.makedirs(os.path.join(self.root_dir, "guests"), exist_ok=True)

    def _get_entity_folder(self, user_id: Optional[str], guest_session_id: Optional[str]) -> str:
        """Determines parent folder path based on authentication or guest session."""
        if user_id:
            safe_uid = "".join(c for c in str(user_id) if c.isalnum() or c in "-_")
            path = os.path.join(self.root_dir, "users", safe_uid)
        else:
            safe_gid = "".join(c for c in str(guest_session_id or "default") if c.isalnum() or c in "-_")
            path = os.path.join(self.root_dir, "guests", safe_gid)
        os.makedirs(path, exist_ok=True)
        return path

    def get_image_dir(self, image_id: str, user_id: Optional[str] = None, guest_session_id: Optional[str] = None) -> str:
        """Returns the isolated folder path for an individual image."""
        safe_img_id = "".join(c for c in str(image_id) if c.isalnum() or c in "-_")
        entity_dir = self._get_entity_folder(user_id, guest_session_id)
        img_dir = os.path.join(entity_dir, safe_img_id)
        os.makedirs(img_dir, exist_ok=True)
        os.makedirs(os.path.join(img_dir, "exports"), exist_ok=True)
        return img_dir

    def save_original(
        self,
        pil_image: Image.Image,
        image_id: str,
        original_filename: str,
        user_id: Optional[str] = None,
        guest_session_id: Optional[str] = None
    ) -> Tuple[str, int]:
        """
        Saves the uploaded original image to persistent storage.
        Returns (relative_file_path, file_size_in_bytes).
        """
        img_dir = self.get_image_dir(image_id, user_id, guest_session_id)
        _, ext = os.path.splitext(original_filename.lower())
        if ext not in ('.jpg', '.jpeg', '.png', '.webp'):
            ext = '.png'

        target_name = f"original{ext}"
        target_path = os.path.join(img_dir, target_name)

        # Save preserving highest fidelity
        fmt = "JPEG" if ext in ('.jpg', '.jpeg') else ("PNG" if ext == '.png' else "WEBP")
        if fmt == "JPEG" and pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")
        pil_image.save(target_path, format=fmt, quality=95)

        file_size = os.path.getsize(target_path)
        # Store path relative to root_dir for portability
        rel_path = os.path.relpath(target_path, self.root_dir).replace("\\", "/")
        return rel_path, file_size

    def save_cutout(
        self,
        pil_image: Image.Image,
        image_id: str,
        user_id: Optional[str] = None,
        guest_session_id: Optional[str] = None
    ) -> str:
        """
        Saves the background-removed transparent PNG to persistent storage.
        Returns relative_file_path.
        """
        img_dir = self.get_image_dir(image_id, user_id, guest_session_id)
        target_path = os.path.join(img_dir, "cutout.png")

        # Always save cutout with alpha channel
        if pil_image.mode != 'RGBA':
            pil_image = pil_image.convert('RGBA')
        pil_image.save(target_path, format="PNG", optimize=True)

        rel_path = os.path.relpath(target_path, self.root_dir).replace("\\", "/")
        return rel_path

    def save_export(
        self,
        content_bytes: bytes,
        image_id: str,
        file_ext: str,
        user_id: Optional[str] = None,
        guest_session_id: Optional[str] = None
    ) -> str:
        """
        Saves an exported asset (e.g. customized JPG, composited PNG, or vectorized SVG).
        Returns relative_file_path.
        """
        img_dir = self.get_image_dir(image_id, user_id, guest_session_id)
        exports_dir = os.path.join(img_dir, "exports")
        os.makedirs(exports_dir, exist_ok=True)

        clean_ext = file_ext.lstrip('.').lower()
        export_filename = f"export_{clean_ext}.{clean_ext}"
        export_path = os.path.join(exports_dir, export_filename)

        with open(export_path, "wb") as f:
            f.write(content_bytes)

        rel_path = os.path.relpath(export_path, self.root_dir).replace("\\", "/")
        return rel_path

    def resolve_path(self, relative_path: str) -> Optional[str]:
        """Resolves relative storage path to absolute path, validating safety."""
        if not relative_path:
            return None
        # Handle if already absolute
        if os.path.isabs(relative_path) and os.path.exists(relative_path):
            return relative_path
        abs_path = os.path.abspath(os.path.join(self.root_dir, relative_path.replace("/", os.sep)))
        if abs_path.startswith(self.root_dir) and os.path.exists(abs_path):
            return abs_path
        return None

    def delete_image_files(
        self,
        image_id: str,
        user_id: Optional[str] = None,
        guest_session_id: Optional[str] = None
    ) -> bool:
        """
        Completely deletes all persistent files (original, cutout, exports) for an image.
        Ensures strict synchronization with database deletions.
        """
        safe_img_id = "".join(c for c in str(image_id) if c.isalnum() or c in "-_")
        entity_dir = self._get_entity_folder(user_id, guest_session_id)
        img_dir = os.path.join(entity_dir, safe_img_id)

        if os.path.exists(img_dir):
            success = _safe_rmtree(img_dir)
            if success:
                logger.info(f"Purged storage directory for image_id={image_id}")
            return success
        return True

    def clear_entity_history(
        self,
        user_id: Optional[str] = None,
        guest_session_id: Optional[str] = None
    ) -> bool:
        """Purges all files belonging to a specific user or guest session."""
        entity_dir = self._get_entity_folder(user_id, guest_session_id)
        if os.path.exists(entity_dir):
            success = _safe_rmtree(entity_dir)
            os.makedirs(entity_dir, exist_ok=True)
            if success:
                logger.info(f"Purged all persistent files for user={user_id}/guest={guest_session_id}")
            return success
        return True


# Global Singleton instance
storage_manager = StorageManager()
