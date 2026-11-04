"""
Gunicorn Production WSGI Server Configuration.
Optimized for AI background removal workloads on multi-core Linux hosts.
"""

import os
import multiprocessing

bind = f"{os.environ.get('HOST', '0.0.0.0')}:{os.environ.get('PORT', '5000')}"

# Concurrency settings
# rembg and ONNX Runtime use multithreading internally; use gthread worker class
workers = int(os.environ.get('GUNICORN_WORKERS', 2))
threads = int(os.environ.get('GUNICORN_THREADS', 4))
worker_class = 'gthread'

# Timeout: Allow up to 120s for high-resolution AI processing & genuine vectorization
timeout = 120
keepalive = 5

# Memory and recycling: Recycle workers periodically to prevent memory fragmentation
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = '-'
errorlog = '-'
loglevel = os.environ.get('LOG_LEVEL', 'info')
capture_output = True

# Process naming
proc_name = 'lumina_bgremover'
preload_app = False  # Avoid ONNX runtime model fork deadlocks across workers
