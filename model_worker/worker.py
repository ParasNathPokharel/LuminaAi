"""
Lumina AI — Standalone Distributed Inference Microservice.
Can be deployed on any server (VPS, Cloud Run, Hugging Face Spaces, Render, Fly.io).
The main Flask web app dispatches background removal requests to this worker when MODEL_WORKER_URL is set.
"""

import io
import os
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image
from rembg import new_session, remove

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LuminaModelWorker")

app = FastAPI(title="Lumina AI Inference Worker", version="1.0.0")

# Model configuration
MODEL_NAME = os.environ.get("REMBG_MODEL", "u2netp")
logger.info(f"Loading rembg model session: {MODEL_NAME}...")
session = new_session(MODEL_NAME)
logger.info("Inference session successfully loaded.")

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "Lumina AI Distributed Model Worker",
        "model": MODEL_NAME
    }

@app.post("/remove")
async def remove_background_endpoint(file: UploadFile = File(...)):
    """Accepts multipart image upload and returns transparent PNG bytes."""
    try:
        content = await file.read()
        pil_img = Image.open(io.BytesIO(content))
        if pil_img.mode not in ('RGB', 'RGBA'):
            pil_img = pil_img.convert('RGBA')

        orig_w, orig_h = pil_img.size
        cutout = remove(pil_img, session=session)

        if cutout.mode != 'RGBA':
            cutout = cutout.convert('RGBA')

        if cutout.size != (orig_w, orig_h):
            cutout = cutout.resize((orig_w, orig_h), Image.Resampling.LANCZOS)

        out_buf = io.BytesIO()
        cutout.save(out_buf, format="PNG", optimize=True)
        out_buf.seek(0)

        return StreamingResponse(
            out_buf,
            media_type="image/png",
            headers={"Content-Disposition": "attachment; filename=cutout.png"}
        )
    except Exception as e:
        logger.error(f"Inference error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
