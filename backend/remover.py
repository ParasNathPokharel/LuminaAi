"""
AI Background Remover Module
Supports:
1. High-efficiency local AI inference using lightweight rembg models (u2netp: ~4.7MB, low RAM)
2. Distributed external inference worker via MODEL_WORKER_URL environment variable
"""

import io
import os
import gc
import logging
from typing import Optional
from PIL import Image

logger = logging.getLogger(__name__)

class BackgroundRemoverService:
    """
    Service wrapper around rembg background removal model.
    Supports persistent local sessions or distributed HTTP worker.
    """
    _instance: Optional['BackgroundRemoverService'] = None

    def __init__(self, model_name: Optional[str] = None):
        self.worker_url = os.environ.get("MODEL_WORKER_URL", "").strip().rstrip("/")
        if not model_name:
            model_name = os.environ.get("REMBG_MODEL", "u2netp")
        self.model_name = self._resolve_best_model(model_name)
        self.session = None
        self._is_loaded = False

        if self.worker_url:
            logger.info(f"Using remote distributed model worker at: {self.worker_url}")
            self._is_loaded = True
        else:
            self._initialize_session()

    @staticmethod
    def _resolve_best_model(preferred: str) -> str:
        """Determines best model while honoring low-memory environment defaults."""
        env_model = os.environ.get("REMBG_MODEL")
        if env_model:
            return env_model.strip()

        u2net_dir = os.path.expanduser(os.path.join("~", ".u2net"))
        full_u2net = os.path.join(u2net_dir, "u2net.onnx")
        portable_u2net = os.path.join(u2net_dir, "u2netp.onnx")

        # If lightweight portable model exists, prefer it in memory-constrained environments
        if os.path.exists(portable_u2net) and os.path.getsize(portable_u2net) > 3 * 1024 * 1024:
            return "u2netp"
        if os.path.exists(full_u2net) and os.path.getsize(full_u2net) > 100 * 1024 * 1024:
            return "u2net"

        return preferred or "u2netp"

    @classmethod
    def get_instance(cls, model_name: Optional[str] = None) -> 'BackgroundRemoverService':
        if cls._instance is None:
            cls._instance = BackgroundRemoverService(model_name)
        return cls._instance

    def _initialize_session(self):
        """Loads and caches the rembg session."""
        try:
            logger.info(f"Initializing AI Background Removal model: '{self.model_name}'...")
            from rembg import new_session
            self.session = new_session(self.model_name)
            self._is_loaded = True
            logger.info(f"AI Background Removal model '{self.model_name}' loaded successfully into memory.")
        except Exception as e:
            logger.error(f"Failed to pre-load rembg model '{self.model_name}': {e}")
            self.session = None
            self._is_loaded = False

    def is_ready(self) -> bool:
        if self.worker_url:
            return True
        return self._is_loaded and (self.session is not None)

    def _remove_via_remote_worker(self, image: Image.Image) -> Image.Image:
        """Offload background removal to a remote distributed worker via HTTP POST."""
        import requests
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        buf.seek(0)

        logger.info(f"Dispatching inference request to remote worker: {self.worker_url}/remove")
        resp = requests.post(
            f"{self.worker_url}/remove",
            files={"file": ("input.png", buf.getvalue(), "image/png")},
            timeout=120
        )
        resp.raise_for_status()
        result_img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
        return result_img

    def remove_background(
        self,
        image: Image.Image,
        alpha_matting: bool = False,
        alpha_matting_foreground_threshold: int = 240,
        alpha_matting_background_threshold: int = 10,
        alpha_matting_erode_size: int = 10
    ) -> Image.Image:
        """
        Removes the background from a PIL Image.
        Routes to remote worker if configured, or executes locally with persistent session.
        """
        # If external distributed worker is configured, delegate work
        if self.worker_url:
            return self._remove_via_remote_worker(image)

        from rembg import remove, new_session

        if self.session is None:
            logger.info(f"Session not initialized, initializing '{self.model_name}' now...")
            self.session = new_session(self.model_name)
            self._is_loaded = True

        # Ensure image is in RGB or RGBA mode
        if image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGBA')

        orig_w, orig_h = image.size

        # Run rembg inference using persistent session
        kwargs = {
            'session': self.session,
            'only_mask': False,
        }

        if alpha_matting:
            kwargs.update({
                'alpha_matting': True,
                'alpha_matting_foreground_threshold': alpha_matting_foreground_threshold,
                'alpha_matting_background_threshold': alpha_matting_background_threshold,
                'alpha_matting_erode_size': alpha_matting_erode_size,
            })

        result_image = remove(image, **kwargs)

        # Ensure result has RGBA mode and preserves exact original dimensions
        if result_image.mode != 'RGBA':
            result_image = result_image.convert('RGBA')

        if result_image.size != (orig_w, orig_h):
            result_image = result_image.resize((orig_w, orig_h), Image.Resampling.LANCZOS)

        # Explicit garbage collection to keep memory bounded on low-RAM hosts
        gc.collect()

        return result_image
