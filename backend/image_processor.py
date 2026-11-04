"""
Image Processor Module
Handles image validation, format conversion, background compositing (solid/gradient/image),
and genuine raster-to-vector SVG vectorization.
"""

import io
import os
import time
import logging
from typing import Tuple, Optional
from PIL import Image, ImageOps, ImageDraw
import numpy as np

logger = logging.getLogger(__name__)

# Allowed MIME types and extensions
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
ALLOWED_MIMES = {'image/jpeg', 'image/png', 'image/webp'}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


def validate_image_file(file_storage, max_size: int = MAX_FILE_SIZE) -> Tuple[bool, str, Optional[Image.Image]]:
    """
    Validates uploaded file: checks file presence, extension, size limit,
    and verifies raster integrity using PIL.
    Returns (is_valid, error_message, pil_image_or_None).
    """
    if not file_storage or not file_storage.filename:
        return False, "No file uploaded or filename is empty.", None

    filename = file_storage.filename.lower()
    ext = os.path.splitext(filename)[1]
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file extension '{ext}'. Allowed: JPG, JPEG, PNG, WEBP.", None

    # Read bytes to check size and verify content
    try:
        content = file_storage.read()
    except Exception as e:
        return False, f"Failed to read file: {str(e)}", None

    if len(content) == 0:
        return False, "Uploaded file is empty.", None

    if len(content) > max_size:
        max_mb = max_size / (1024 * 1024)
        return False, f"File exceeds maximum allowed size of {max_mb:.0f} MB.", None

    # Verify PIL can open and parse it
    try:
        img_buffer = io.BytesIO(content)
        img = Image.open(img_buffer)
        img.verify()  # verify integrity
        # verify closes the file/buffer, so reopen for actual use
        img = Image.open(io.BytesIO(content))
        # Handle EXIF orientation if present
        img = ImageOps.exif_transpose(img)
        return True, "", img
    except Exception as e:
        logger.error(f"Image verification error: {e}")
        return False, "Uploaded file is not a valid or supported image file.", None


def parse_hex_color(hex_str: str, default: Tuple[int, int, int] = (255, 255, 255)) -> Tuple[int, int, int]:
    """Parses a hex color string like #FFFFFF or #FFF into RGB tuple."""
    if not hex_str:
        return default
    hex_clean = hex_str.strip().lstrip('#')
    try:
        if len(hex_clean) == 3:
            hex_clean = ''.join([c * 2 for c in hex_clean])
        if len(hex_clean) == 6:
            return (
                int(hex_clean[0:2], 16),
                int(hex_clean[2:4], 16),
                int(hex_clean[4:6], 16)
            )
    except Exception:
        pass
    return default


def generate_gradient_background(size: Tuple[int, int], color1: str, color2: str, direction: str = 'vertical') -> Image.Image:
    """Generates a smooth 2-color linear gradient image."""
    w, h = size
    rgb1 = parse_hex_color(color1, (59, 130, 246))
    rgb2 = parse_hex_color(color2, (147, 51, 234))

    base = Image.new('RGB', (w, h))
    if direction == 'horizontal':
        gradient = np.zeros((h, w, 3), dtype=np.uint8)
        for x in range(w):
            factor = x / max(w - 1, 1)
            gradient[:, x, 0] = int(rgb1[0] + factor * (rgb2[0] - rgb1[0]))
            gradient[:, x, 1] = int(rgb1[1] + factor * (rgb2[1] - rgb1[1]))
            gradient[:, x, 2] = int(rgb1[2] + factor * (rgb2[2] - rgb1[2]))
        return Image.fromarray(gradient)
    elif direction == 'diagonal':
        gradient = np.zeros((h, w, 3), dtype=np.uint8)
        max_dist = (w - 1) + (h - 1)
        for y in range(h):
            for x in range(w):
                factor = (x + y) / max(max_dist, 1)
                gradient[y, x, 0] = int(rgb1[0] + factor * (rgb2[0] - rgb1[0]))
                gradient[y, x, 1] = int(rgb1[1] + factor * (rgb2[1] - rgb1[1]))
                gradient[y, x, 2] = int(rgb1[2] + factor * (rgb2[2] - rgb1[2]))
        return Image.fromarray(gradient)
    else:
        # vertical (default)
        gradient = np.zeros((h, w, 3), dtype=np.uint8)
        for y in range(h):
            factor = y / max(h - 1, 1)
            gradient[y, :, 0] = int(rgb1[0] + factor * (rgb2[0] - rgb1[0]))
            gradient[y, :, 1] = int(rgb1[1] + factor * (rgb2[1] - rgb1[1]))
            gradient[y, :, 2] = int(rgb1[2] + factor * (rgb2[2] - rgb1[2]))
        return Image.fromarray(gradient)


def composite_image(
    foreground_rgba: Image.Image,
    bg_type: str = 'transparent',
    bg_color: str = '#ffffff',
    gradient_start: str = '#3b82f6',
    gradient_end: str = '#9333ea',
    gradient_direction: str = 'vertical',
    bg_custom_image: Optional[Image.Image] = None
) -> Image.Image:
    """
    Composites a transparent RGBA foreground image onto the chosen background.
    - 'transparent': returns original RGBA image.
    - 'color': returns RGB image composited over solid color.
    - 'gradient': returns RGB image composited over smooth linear gradient.
    - 'image': returns RGB image composited over resized/cropped custom background.
    """
    if foreground_rgba.mode != 'RGBA':
        foreground_rgba = foreground_rgba.convert('RGBA')

    w, h = foreground_rgba.size

    if bg_type == 'transparent':
        return foreground_rgba

    if bg_type == 'color':
        solid_rgb = parse_hex_color(bg_color)
        bg = Image.new('RGB', (w, h), solid_rgb)
        bg.paste(foreground_rgba, (0, 0), mask=foreground_rgba.split()[3])
        return bg

    if bg_type == 'gradient':
        bg = generate_gradient_background((w, h), gradient_start, gradient_end, gradient_direction)
        bg.paste(foreground_rgba, (0, 0), mask=foreground_rgba.split()[3])
        return bg

    if bg_type == 'image' and bg_custom_image is not None:
        # Fit custom background to foreground dimensions (crop & center)
        bg_fitted = ImageOps.fit(bg_custom_image.convert('RGB'), (w, h), Image.Resampling.LANCZOS)
        bg_fitted.paste(foreground_rgba, (0, 0), mask=foreground_rgba.split()[3])
        return bg_fitted

    # Default fallback to white solid
    bg = Image.new('RGB', (w, h), (255, 255, 255))
    bg.paste(foreground_rgba, (0, 0), mask=foreground_rgba.split()[3])
    return bg


def vectorize_image_to_svg(
    rgba_image: Image.Image,
    colormode: str = 'color',
    max_colors: int = 48,
    precision: int = 6
) -> str:
    """
    Performs genuine raster-to-vector SVG vectorization.
    Uses vtracer (VisionCortex raster-to-vector converter).
    If vtracer is unavailable, falls back to OpenCV multi-tone contour vectorizer.
    Does NOT simply embed base64 inside SVG; returns genuine XML vector paths.
    """
    w, h = rgba_image.size

    # Attempt vtracer first (high fidelity vectorizer)
    try:
        import vtracer

        # Save to temporary buffer or pass raw pixels
        # vtracer.convert_raw_image_to_svg takes (raw_pixels, width, height, colormode, etc.)
        # vtracer accepts RGB or RGBA bytearray
        if rgba_image.mode != 'RGBA':
            rgba_image = rgba_image.convert('RGBA')

        # Limit size for vector processing to avoid memory bloat on giant images
        max_vector_dim = 1000
        if w > max_vector_dim or h > max_vector_dim:
            scale = max_vector_dim / max(w, h)
            vec_img = rgba_image.resize((int(w * scale), int(h * scale)), Image.Resampling.BILINEAR)
        else:
            vec_img = rgba_image

        vw, vh = vec_img.size
        png_buf = io.BytesIO()
        vec_img.save(png_buf, format='PNG')
        png_bytes = png_buf.getvalue()

        # vtracer genuine raster-to-vector options
        svg_str = vtracer.convert_raw_image_to_svg(
            png_bytes,
            img_format='png',
            colormode=colormode,       # 'color' or 'binary'
            hierarchical='stacked',    # 'stacked' or 'cutout'
            mode='spline',             # 'spline' curves, 'polygon', or 'none'
            filter_speckle=4,          # discard small noise speckles
            color_precision=precision, # precision of color quantization
            layer_difference=16,
            corner_threshold=60,
            length_threshold=4.0,
            max_iterations=10,
            splice_threshold=45,
            path_precision=3
        )
        # Ensure viewBox matches original dimensions if scaled
        if (vw, vh) != (w, h):
            # inject/adjust width & height attributes for original size
            svg_str = svg_str.replace(f'width="{vw}"', f'width="{w}"', 1)
            svg_str = svg_str.replace(f'height="{vh}"', f'height="{h}"', 1)
        return svg_str

    except Exception as e:
        logger.warning(f"vtracer vectorization fell back to OpenCV contour vectorizer: {e}")

    # Fallback: Robust OpenCV contour/path vectorizer
    return _opencv_vectorize_fallback(rgba_image)


def _opencv_vectorize_fallback(rgba_image: Image.Image) -> str:
    """
    Fallback vectorizer using OpenCV contour extraction and SVG path generation.
    Generates genuine SVG paths with color fills.
    """
    import cv2

    if rgba_image.mode != 'RGBA':
        rgba_image = rgba_image.convert('RGBA')

    w, h = rgba_image.size
    max_dim = 800
    if max(w, h) > max_dim:
        scale = max_dim / max(w, h)
        proc_img = rgba_image.resize((int(w * scale), int(h * scale)), Image.Resampling.BILINEAR)
    else:
        scale = 1.0
        proc_img = rgba_image

    pw, ph = proc_img.size
    np_img = np.array(proc_img)
    alpha = np_img[:, :, 3]
    rgb = np_img[:, :, :3]

    # Mask foreground
    fg_mask = alpha > 30

    svg_paths = []
    svg_paths.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">')
    svg_paths.append(f'  <!-- Generated by AI Background Remover (Genuine Vector Paths) -->')

    # Quantize colors using K-Means for multi-tone vectorization
    pixels = rgb[fg_mask]
    if len(pixels) > 50:
        n_colors = min(16, len(pixels))
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        flags = cv2.KMEANS_RANDOM_CENTERS
        compactness, labels, centers = cv2.kmeans(pixels.astype(np.float32), n_colors, None, criteria, 10, flags)
        centers = np.uint8(centers)

        # Create quantized mask layer for each color cluster
        quantized_cluster = np.zeros((ph, pw), dtype=np.int32) - 1
        quantized_cluster[fg_mask] = labels.flatten()

        for c_idx in range(n_colors):
            c_rgb = centers[c_idx]
            hex_col = f"#{c_rgb[0]:02x}{c_rgb[1]:02x}{c_rgb[2]:02x}"
            mask_c = (quantized_cluster == c_idx).astype(np.uint8) * 255

            contours, _ = cv2.findContours(mask_c, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_KCOS)
            for cnt in contours:
                if cv2.contourArea(cnt) < 15:
                    continue
                # Approximate polygon
                epsilon = 0.005 * cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, epsilon, True)
                if len(approx) < 3:
                    continue

                d_str = "M "
                for i, pt in enumerate(approx):
                    px = pt[0][0] / scale
                    py = pt[0][1] / scale
                    if i == 0:
                        d_str += f"{px:.1f} {py:.1f}"
                    else:
                        d_str += f" L {px:.1f} {py:.1f}"
                d_str += " Z"
                svg_paths.append(f'  <path d="{d_str}" fill="{hex_col}" opacity="0.95" />')
    else:
        # Simple silhouette path
        mask = (alpha > 30).astype(np.uint8) * 255
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            if cv2.contourArea(cnt) < 20:
                continue
            approx = cv2.approxPolyDP(cnt, 2.0, True)
            d_str = "M "
            for i, pt in enumerate(approx):
                px = pt[0][0] / scale
                py = pt[0][1] / scale
                d_str += f"{px:.1f} {py:.1f} " if i == 0 else f"L {px:.1f} {py:.1f} "
            d_str += "Z"
            svg_paths.append(f'  <path d="{d_str}" fill="#333333" />')

    svg_paths.append('</svg>')
    return '\n'.join(svg_paths)


def cleanup_temporary_directory(directory_path: str, max_age_seconds: int = 1800):
    """Deletes files in directory older than max_age_seconds."""
    if not os.path.exists(directory_path):
        return
    now = time.time()
    try:
        for fname in os.listdir(directory_path):
            if fname.startswith('.'):
                continue
            fpath = os.path.join(directory_path, fname)
            if os.path.isfile(fpath):
                if now - os.path.getmtime(fpath) > max_age_seconds:
                    try:
                        os.remove(fpath)
                    except Exception:
                        pass
    except Exception as e:
        logger.warning(f"Error cleaning directory {directory_path}: {e}")
