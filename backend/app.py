"""
AI Background Remover — Flask Backend Server with Persistent Storage & PostgreSQL DB.
Features:
- Full RESTful APIs for AI background removal, studio previews, compositing, and vector export.
- Persistent structured disk storage for originals, transparent cutouts, and exports.
- PostgreSQL database integration with SQLite fallback.
- Pagination, search, filtering, and audit history for Image Library.
- Production-grade logging, graceful error handling, and health monitoring.
"""

import os
import io
import time
import uuid
import base64
import logging
from datetime import datetime
from flask import Flask, request, jsonify, send_file, make_response, g
from flask_cors import CORS
from PIL import Image
from sqlalchemy import or_, desc, asc

from remover import BackgroundRemoverService
from image_processor import (
    validate_image_file,
    composite_image,
    vectorize_image_to_svg,
    MAX_FILE_SIZE
)
from database import init_db, get_db, User, ImageRecord, ProcessingHistoryRecord
from storage import storage_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("BackgroundRemoverApp")

# Base directory setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

# Initialize Flask app
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Initialize Database
try:
    init_db()
    logger.info("Database initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}", exc_info=True)

# In-memory LRU cache for ultra-fast recent image access
PROCESSED_CACHE = {}

# Initialize Background Remover singleton
remover_service = None
try:
    remover_service = BackgroundRemoverService.get_instance(model_name="u2net")
except Exception as e:
    logger.warning(f"Initial model loading deferred: {e}")


def _pil_to_base64_data_url(pil_img: Image.Image, format: str = "PNG", quality: int = 90) -> str:
    """Helper to convert a PIL Image to a Base64 data URL string."""
    buffered = io.BytesIO()
    if format.upper() == "PNG":
        pil_img.save(buffered, format="PNG", optimize=True)
        mime = "image/png"
    elif format.upper() in ("JPG", "JPEG"):
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")
        pil_img.save(buffered, format="JPEG", quality=quality, optimize=True)
        mime = "image/jpeg"
    elif format.upper() == "WEBP":
        pil_img.save(buffered, format="WEBP", quality=quality)
        mime = "image/webp"
    else:
        pil_img.save(buffered, format=format)
        mime = f"image/{format.lower()}"

    encoded = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def _base64_to_pil(data_url_or_base64: str) -> Image.Image:
    """Decodes a base64 string or data URL into a PIL Image."""
    if "," in data_url_or_base64:
        data_url_or_base64 = data_url_or_base64.split(",", 1)[1]
    decoded_bytes = base64.b64decode(data_url_or_base64)
    return Image.open(io.BytesIO(decoded_bytes))


def get_request_identity():
    """
    Extracts user_id or guest_session_id from headers/cookies.
    Supports persistent guest sessions across browser reloads.
    """
    user_id = request.headers.get("X-User-ID") or request.cookies.get("lumina_user_id")
    guest_id = request.headers.get("X-Session-ID") or request.cookies.get("lumina_session_id")

    if not user_id and not guest_id:
        guest_id = str(uuid.uuid4())

    return user_id, guest_id


@app.teardown_appcontext
def remove_db_session(exception=None):
    """Ensure database sessions are removed and returned to pool cleanly."""
    db = get_db()
    if db:
        db.remove()


# ==========================================
# Frontend Routes
# ==========================================
@app.route('/')
def serve_index():
    """Serves the frontend single page app."""
    return send_file(os.path.join(FRONTEND_DIR, 'index.html'))


@app.route('/<path:path>')
def serve_static(path):
    """Serves frontend static assets (CSS, JS, assets)."""
    full_path = os.path.join(FRONTEND_DIR, path)
    if os.path.exists(full_path) and os.path.isfile(full_path):
        return send_file(full_path)
    return send_file(os.path.join(FRONTEND_DIR, 'index.html'))


# ==========================================
# Core API Endpoints
# ==========================================
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify backend status, DB, and model readiness."""
    global remover_service
    is_ready = remover_service.is_ready() if remover_service else False

    db_ok = False
    try:
        db = get_db()
        db.execute(text("SELECT 1") if 'text' in globals() else "SELECT 1")
        db_ok = True
    except Exception:
        # Fallback raw check
        try:
            db = get_db()
            db.query(ImageRecord).first()
            db_ok = True
        except Exception as e:
            logger.warning(f"DB health ping error: {e}")

    return jsonify({
        "status": "ok" if (is_ready and db_ok) else "degraded",
        "service": "Lumina AI Background Remover Backend",
        "model_name": "u2net",
        "model_loaded": is_ready,
        "database_connected": db_ok,
        "max_upload_size_mb": MAX_FILE_SIZE // (1024 * 1024),
        "version": "2.0.0"
    }), 200


@app.route('/api/remove-background', methods=['POST'])
def remove_background_endpoint():
    """
    Main background removal endpoint.
    - Saves uploaded original to persistent storage.
    - Executes rembg AI model inference.
    - Saves transparent PNG cutout to persistent storage.
    - Records metadata in PostgreSQL / SQLite Images and ProcessingHistory tables.
    - Returns preview URLs and image identity.
    """
    start_time = time.time()
    global remover_service
    if remover_service is None:
        remover_service = BackgroundRemoverService.get_instance("u2net")

    user_id, guest_session_id = get_request_identity()
    pil_input_img = None
    original_filename = "image.png"

    # 1. Parse Input: Multipart or JSON
    if 'file' in request.files or 'image' in request.files:
        file_obj = request.files.get('file') or request.files.get('image')
        original_filename = file_obj.filename or "image.png"
        is_valid, err_msg, pil_input_img = validate_image_file(file_obj, max_size=MAX_FILE_SIZE)
        if not is_valid:
            return jsonify({"success": False, "error": err_msg}), 400
    elif request.is_json:
        data = request.get_json()
        b64_str = data.get('image')
        if not b64_str:
            return jsonify({"success": False, "error": "No image payload found in JSON body."}), 400
        try:
            pil_input_img = _base64_to_pil(b64_str)
            original_filename = data.get('filename', 'uploaded_image.png')
        except Exception as e:
            return jsonify({"success": False, "error": f"Invalid base64 image data: {str(e)}"}), 400
    else:
        return jsonify({"success": False, "error": "Missing image file or payload. Send multipart/form-data or JSON."}), 400

    # 2. Extract options
    alpha_matting = False
    if request.form.get('alpha_matting') in ('true', '1', True):
        alpha_matting = True
    elif request.is_json and request.get_json().get('alpha_matting'):
        alpha_matting = True

    image_id = str(uuid.uuid4())
    orig_w, orig_h = pil_input_img.size
    _, file_ext = os.path.splitext(original_filename.lower())
    orig_format = file_ext.lstrip('.') or 'png'

    # 3. Save original image to persistent storage
    try:
        rel_orig_path, file_size = storage_manager.save_original(
            pil_input_img,
            image_id=image_id,
            original_filename=original_filename,
            user_id=user_id,
            guest_session_id=guest_session_id
        )
    except Exception as e:
        logger.error(f"Failed to persist original image: {e}", exc_info=True)
        return jsonify({"success": False, "error": f"Storage error: {str(e)}"}), 500

    # 4. Perform AI Background Removal
    try:
        logger.info(f"Inference: {original_filename} ({orig_w}x{orig_h}) | Matting: {alpha_matting}")
        transparent_img = remover_service.remove_background(
            pil_input_img,
            alpha_matting=alpha_matting
        )
        elapsed_sec = time.time() - start_time
        elapsed_ms = int(elapsed_sec * 1000)

        # 5. Save transparent cutout to persistent storage
        rel_proc_path = storage_manager.save_cutout(
            transparent_img,
            image_id=image_id,
            user_id=user_id,
            guest_session_id=guest_session_id
        )

        # Cache in memory for quick follow-up export operations
        PROCESSED_CACHE[image_id] = {
            'img': transparent_img,
            'orig': pil_input_img,
            'filename': original_filename,
            'user_id': user_id,
            'guest_id': guest_session_id,
            'time': time.time()
        }

        # 6. Record metadata in PostgreSQL Database
        db = get_db()
        db_image = ImageRecord(
            image_id=image_id,
            user_id=user_id,
            guest_session_id=guest_session_id,
            original_filename=original_filename,
            original_image_path=rel_orig_path,
            processed_image_path=rel_proc_path,
            original_format=orig_format,
            output_format='png',
            file_size=file_size,
            image_width=orig_w,
            image_height=orig_h,
            processing_status='completed'
        )
        db.add(db_image)

        # Record processing history
        history_entry = ProcessingHistoryRecord(
            image_id=image_id,
            processing_time=elapsed_sec,
            selected_output_format='png',
            background_type='transparent'
        )
        db.add(history_entry)
        db.commit()

        # 7. Generate base64 previews
        processed_data_url = _pil_to_base64_data_url(transparent_img, format="PNG")
        original_data_url = _pil_to_base64_data_url(pil_input_img, format="JPEG", quality=85)

        response = make_response(jsonify({
            "success": True,
            "image_id": image_id,
            "filename": original_filename,
            "width": orig_w,
            "height": orig_h,
            "file_size": file_size,
            "processed_image": processed_data_url,
            "original_image": original_data_url,
            "processing_time_ms": elapsed_ms,
            "guest_session_id": guest_session_id
        }), 200)

        # Set persistent guest cookie if not set
        if not request.cookies.get("lumina_session_id") and guest_session_id:
            response.set_cookie(
                "lumina_session_id",
                guest_session_id,
                max_age=30 * 24 * 3600,
                httponly=False,
                samesite="Lax"
            )

        return response

    except Exception as e:
        logger.error(f"Error during AI background removal: {e}", exc_info=True)
        # Attempt to mark as failed in DB if created
        try:
            db = get_db()
            failed_rec = ImageRecord(
                image_id=image_id,
                user_id=user_id,
                guest_session_id=guest_session_id,
                original_filename=original_filename,
                original_image_path=rel_orig_path if 'rel_orig_path' in locals() else '',
                processed_image_path='',
                original_format=orig_format,
                output_format='png',
                file_size=file_size if 'file_size' in locals() else 0,
                image_width=orig_w,
                image_height=orig_h,
                processing_status='failed'
            )
            db.add(failed_rec)
            db.commit()
        except Exception:
            pass

        return jsonify({
            "success": False,
            "error": f"AI background removal processing failed: {str(e)}"
        }), 500


@app.route('/api/export', methods=['POST'])
def export_endpoint():
    """
    Exports the processed image with selected background and format.
    - Saves export to persistent storage.
    - Records export event in processing_history.
    - Streams downloadable file attachment.
    """
    start_time = time.time()
    try:
        data = request.get_json(silent=True) or request.form.to_dict()

        image_id = data.get('image_id')
        export_format = (data.get('format') or 'png').lower().strip()
        bg_type = (data.get('bg_type') or 'transparent').lower().strip()
        bg_color = data.get('bg_color') or '#ffffff'
        gradient_start = data.get('gradient_start') or '#3b82f6'
        gradient_end = data.get('gradient_end') or '#9333ea'
        gradient_direction = data.get('gradient_direction') or 'vertical'
        bg_custom_image_b64 = data.get('bg_custom_image')
        image_base64 = data.get('image')

        user_id, guest_session_id = get_request_identity()
        transparent_img = None
        orig_filename = "result"

        # 1. Fetch image from memory cache or persistent storage
        if image_id and image_id in PROCESSED_CACHE:
            transparent_img = PROCESSED_CACHE[image_id]['img']
            orig_filename = os.path.splitext(PROCESSED_CACHE[image_id]['filename'])[0]
        elif image_id:
            db = get_db()
            record = db.query(ImageRecord).filter(ImageRecord.image_id == image_id).first()
            if record:
                orig_filename = os.path.splitext(record.original_filename)[0]
                user_id = record.user_id
                guest_session_id = record.guest_session_id
                abs_path = storage_manager.resolve_path(record.processed_image_path)
                if abs_path and os.path.exists(abs_path):
                    with Image.open(abs_path) as im:
                        transparent_img = im.copy()

        if transparent_img is None and image_base64:
            transparent_img = _base64_to_pil(image_base64)

        if transparent_img is None:
            return jsonify({"success": False, "error": "Image not found. Please upload and process an image first."}), 404

        # Custom background image if provided
        custom_bg_img = None
        if bg_type == 'image' and bg_custom_image_b64:
            try:
                custom_bg_img = _base64_to_pil(bg_custom_image_b64)
            except Exception as e:
                logger.warning(f"Could not decode custom background image: {e}")

        # 2. Render export format
        export_bytes = None
        mimetype = "image/png"
        download_name = f"{orig_filename}_no_bg.png"

        if export_format in ('jpeg', 'jpg'):
            effective_bg_type = 'color' if bg_type == 'transparent' else bg_type
            final_img = composite_image(
                transparent_img,
                bg_type=effective_bg_type,
                bg_color=bg_color,
                gradient_start=gradient_start,
                gradient_end=gradient_end,
                gradient_direction=gradient_direction,
                bg_custom_image=custom_bg_img
            )
            buf = io.BytesIO()
            final_img.convert('RGB').save(buf, format='JPEG', quality=95, optimize=True)
            export_bytes = buf.getvalue()
            mimetype = 'image/jpeg'
            download_name = f"{orig_filename}_no_bg.jpg"

        elif export_format == 'png':
            final_img = composite_image(
                transparent_img,
                bg_type=bg_type,
                bg_color=bg_color,
                gradient_start=gradient_start,
                gradient_end=gradient_end,
                gradient_direction=gradient_direction,
                bg_custom_image=custom_bg_img
            )
            buf = io.BytesIO()
            final_img.save(buf, format='PNG', optimize=True)
            export_bytes = buf.getvalue()
            mimetype = 'image/png'
            download_name = f"{orig_filename}_no_bg.png"

        elif export_format == 'svg':
            # Genuine vectorization
            logger.info(f"Vectorizing image to SVG for {orig_filename}...")
            comp_for_svg = composite_image(
                transparent_img,
                bg_type=bg_type,
                bg_color=bg_color,
                gradient_start=gradient_start,
                gradient_end=gradient_end,
                gradient_direction=gradient_direction,
                bg_custom_image=custom_bg_img
            ) if bg_type != 'transparent' else transparent_img

            svg_content = vectorize_image_to_svg(comp_for_svg, colormode='color')
            export_bytes = svg_content.encode('utf-8')
            mimetype = 'image/svg+xml'
            download_name = f"{orig_filename}_vector.svg"

        else:
            return jsonify({
                "success": False,
                "error": f"Unsupported export format '{export_format}'. Allowed: png, jpg, svg."
            }), 400

        # 3. Persist export file & register audit history if image_id exists
        if image_id and export_bytes:
            try:
                storage_manager.save_export(
                    export_bytes,
                    image_id=image_id,
                    file_ext=export_format,
                    user_id=user_id,
                    guest_session_id=guest_session_id
                )
                db = get_db()
                audit_rec = ProcessingHistoryRecord(
                    image_id=image_id,
                    processing_time=time.time() - start_time,
                    selected_output_format=export_format,
                    background_type=bg_type
                )
                db.add(audit_rec)
                db.commit()
            except Exception as ex:
                logger.warning(f"Could not audit export record: {ex}")

        # 4. Stream response
        return send_file(
            io.BytesIO(export_bytes),
            mimetype=mimetype,
            as_attachment=True,
            download_name=download_name
        )

    except Exception as e:
        logger.error(f"Error during export: {e}", exc_info=True)
        return jsonify({"success": False, "error": f"Export failed: {str(e)}"}), 500


# ==========================================
# Image Library & History APIs
# ==========================================
@app.route('/api/images', methods=['GET'])
def get_images_library():
    """
    Retrieves paginated image history for current user or guest session.
    Supports filtering by query ('q'), format, and sort order.
    """
    user_id, guest_session_id = get_request_identity()
    page = max(1, int(request.args.get('page', 1)))
    limit = min(50, max(1, int(request.args.get('limit', 12))))
    search_q = request.args.get('q', '').strip()
    format_filter = request.args.get('format', '').strip().lower()
    sort_by = request.args.get('sort', 'newest')

    db = get_db()
    # Filter by user or guest session
    if user_id:
        query = db.query(ImageRecord).filter(ImageRecord.user_id == user_id)
    else:
        query = db.query(ImageRecord).filter(ImageRecord.guest_session_id == guest_session_id)

    # Search filter
    if search_q:
        query = query.filter(ImageRecord.original_filename.ilike(f"%{search_q}%"))

    # Format filter
    if format_filter and format_filter != 'all':
        query = query.filter(
            or_(
                ImageRecord.original_format == format_filter,
                ImageRecord.output_format == format_filter
            )
        )

    # Sort order
    if sort_by == 'oldest':
        query = query.order_by(asc(ImageRecord.created_at))
    elif sort_by == 'name':
        query = query.order_by(asc(ImageRecord.original_filename))
    else:
        query = query.order_by(desc(ImageRecord.created_at))

    total_count = query.count()
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1
    offset = (page - 1) * limit
    images = query.offset(offset).limit(limit).all()

    items = []
    for img in images:
        data = img.to_dict()
        data["original_url"] = f"/api/images/{img.image_id}/preview/original"
        data["processed_url"] = f"/api/images/{img.image_id}/preview/cutout"
        items.append(data)

    return jsonify({
        "success": True,
        "images": items,
        "pagination": {
            "current_page": page,
            "limit": limit,
            "total_items": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }), 200


@app.route('/api/images/<image_id>', methods=['GET'])
def get_image_details(image_id):
    """Returns detailed image metadata and processing history."""
    db = get_db()
    image = db.query(ImageRecord).filter(ImageRecord.image_id == image_id).first()
    if not image:
        return jsonify({"success": False, "error": "Image not found"}), 404

    history = [h.to_dict() for h in image.history_entries]
    data = image.to_dict()
    data["history"] = history
    data["original_url"] = f"/api/images/{image.image_id}/preview/original"
    data["processed_url"] = f"/api/images/{image.image_id}/preview/cutout"

    return jsonify({"success": True, "image": data}), 200


@app.route('/api/images/<image_id>/preview/<view_type>', methods=['GET'])
def stream_image_preview(image_id, view_type):
    """
    Streams original or cutout image directly from persistent storage.
    Includes browser caching headers for high responsiveness.
    """
    db = get_db()
    image = db.query(ImageRecord).filter(ImageRecord.image_id == image_id).first()
    if not image:
        return jsonify({"error": "Image not found"}), 404

    rel_path = image.original_image_path if view_type == 'original' else image.processed_image_path
    abs_path = storage_manager.resolve_path(rel_path)

    if not abs_path or not os.path.exists(abs_path):
        return jsonify({"error": "Image file not found on disk storage"}), 404

    mimetype = 'image/png'
    if view_type == 'original' and image.original_format in ('jpg', 'jpeg'):
        mimetype = 'image/jpeg'

    with open(abs_path, 'rb') as f:
        file_bytes = f.read()

    resp = make_response(send_file(io.BytesIO(file_bytes), mimetype=mimetype))
    resp.headers['Cache-Control'] = 'public, max-age=86400'
    return resp


@app.route('/api/images/<image_id>', methods=['DELETE'])
def delete_image(image_id):
    """
    Deletes an individual image record and removes its physical files from storage.
    Strictly synchronizes database and disk state.
    """
    db = get_db()
    image = db.query(ImageRecord).filter(ImageRecord.image_id == image_id).first()
    if not image:
        return jsonify({"success": False, "error": "Image not found"}), 404

    user_id = image.user_id
    guest_session_id = image.guest_session_id

    # 1. Delete physical files from disk
    storage_manager.delete_image_files(image_id, user_id=user_id, guest_session_id=guest_session_id)

    # 2. Remove from LRU memory cache
    PROCESSED_CACHE.pop(image_id, None)

    # 3. Delete database record (cascades to processing_history)
    db.delete(image)
    db.commit()

    return jsonify({"success": True, "message": "Image deleted successfully."}), 200


@app.route('/api/images', methods=['DELETE'])
def clear_all_history():
    """
    Clears all images belonging to the current user or guest session.
    Purges both database rows and persistent disk files.
    """
    user_id, guest_session_id = get_request_identity()
    db = get_db()

    if user_id:
        images = db.query(ImageRecord).filter(ImageRecord.user_id == user_id).all()
    else:
        images = db.query(ImageRecord).filter(ImageRecord.guest_session_id == guest_session_id).all()

    # Purge physical files
    storage_manager.clear_entity_history(user_id=user_id, guest_session_id=guest_session_id)

    # Clean in-memory cache
    for img in images:
        PROCESSED_CACHE.pop(img.image_id, None)
        db.delete(img)

    db.commit()

    return jsonify({
        "success": True,
        "message": f"Successfully deleted {len(images)} images and cleared persistent history."
    }), 200


# ==========================================
# User Account Endpoints (Optional Auth)
# ==========================================
@app.route('/api/auth/register', methods=['POST'])
def register_user():
    """Simple user registration for image persistence across devices."""
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower() or None

    if not username:
        return jsonify({"success": False, "error": "Username is required."}), 400

    db = get_db()
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return jsonify({"success": False, "error": "Username already exists."}), 409

    new_user = User(username=username, email=email)
    db.add(new_user)
    db.commit()

    return jsonify({
        "success": True,
        "user": new_user.to_dict(),
        "message": "User registered successfully."
    }), 201


@app.route('/api/auth/login', methods=['POST'])
def login_user():
    """Simple user login/lookup endpoint."""
    data = request.get_json() or {}
    username = data.get('username', '').strip()

    db = get_db()
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return jsonify({"success": False, "error": "User not found."}), 404

    return jsonify({
        "success": True,
        "user": user.to_dict()
    }), 200


# ==========================================
# Error Handlers
# ==========================================
@app.errorhandler(413)
def request_entity_too_large(error):
    max_mb = MAX_FILE_SIZE // (1024 * 1024)
    return jsonify({
        "success": False,
        "error": f"Image file is too large. Maximum allowed size is {max_mb} MB."
    }), 413


@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "The requested resource was not found."}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({"success": False, "error": "Internal server error."}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    logger.info(f"Starting Lumina AI Background Remover at http://127.0.0.1:{port}")
    app.run(host=host, port=port, debug=False, threaded=True)
