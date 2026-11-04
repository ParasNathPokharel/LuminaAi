"""
AI Background Remover Module
Wraps rembg with a persistent model session for high performance.
Reuses the neural network session across requests to avoid model re-initialization.
"""

import io
import logging
from typing import Optional
from PIL import Image

logger = logging.getLogger(__name__)

class BackgroundRemoverService:
    """
    Service wrapper around rembg background removal model.
    Maintains a persistent session so the AI model is loaded only once.
    """
    _instance: Optional['BackgroundRemoverService'] = None

    def __init__(self, model_name: str = "u2net"):
        # Auto-detect best available local model
        self.model_name = self._resolve_best_model(model_name)
        self.session = None
        self._is_loaded = False
        self._initialize_session()

    @staticmethod
    def _resolve_best_model(preferred: str) -> str:
        """Checks for existing downloaded models in ~/.u2net to ensure immediate readiness."""
        import os
        u2net_dir = os.path.expanduser(os.path.join("~", ".u2net"))
        full_u2net = os.path.join(u2net_dir, "u2net.onnx")
        portable_u2net = os.path.join(u2net_dir, "u2netp.onnx")

        # If full u2net is present and complete (>100MB)
        if os.path.exists(full_u2net) and os.path.getsize(full_u2net) > 100 * 1024 * 1024:
            return "u2net"
        # If portable fast u2netp is present
        if os.path.exists(portable_u2net) and os.path.getsize(portable_u2net) > 3 * 1024 * 1024:
            return "u2netp"

        return preferred

    @classmethod
    def get_instance(cls, model_name: str = "u2net") -> 'BackgroundRemoverService':
        if cls._instance is None:
            cls._instance = BackgroundRemoverService(model_name)
        return cls._instance

    def _initialize_session(self):
        """Loads and caches the rembg session."""
        try:
            logger.info(f"Initializing AI Background Removal model: {self.model_name}...")
            from rembg import new_session
            self.session = new_session(self.model_name)
            self._is_loaded = True
            logger.info(f"AI Background Removal model '{self.model_name}' loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to pre-load rembg model '{self.model_name}': {e}")
            self.session = None
            self._is_loaded = False

    def is_ready(self) -> bool:
        return self._is_loaded and (self.session is not None)

    def remove_background(
        self,
        image: Image.Image,
        alpha_matting: bool = False,
        alpha_matting_foreground_threshold: int = 240,
        alpha_matting_background_threshold: int = 10,
        alpha_matting_erode_size: int = 10
    ) -> Image.Image:
        """
        Removes the background from a PIL Image using the loaded rembg session.
        Preserves original dimensions, fine edges, and aspect ratio.
        Returns a transparent RGBA PIL Image.
        """
        from rembg import remove, new_session

        if self.session is None:
            logger.info("Session not initialized, initializing now...")
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

        return result_image
