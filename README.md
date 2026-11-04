# Lumina AI â€” Enterprise AI Background Remover & Vector Studio

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/Flask-2.3+-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/ONNX_Runtime-1.15+-005CED?style=for-the-badge&logo=onnx&logoColor=white" alt="ONNX Runtime" />
  <img src="https://img.shields.io/badge/Docker-Enabled-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="MIT License" />
</p>

A commercial-grade, full-stack AI Background Remover web application engineered with a **dark luxury aesthetic**. Lumina AI executes high-precision background segmentation locally using offline deep neural networks (U2-Net), eliminating external cloud API dependencies, recurring costs, and data privacy leaks.

Includes **persistent PostgreSQL database integration**, structured file storage management, an interactive **"My Image Library" gallery**, and complete production deployment tooling with automated SSL for custom domains.

---

## ðŸŒŸ Key Features

### 1. Neural AI Background Removal (100% Offline)
- **Universal Subject Segmentation**: Accurately isolates humans, pets (cats, dogs, animal fur), vehicles, e-commerce products, jewelry, food, furniture, and general objects.
- **Deep U2-Net Architecture**: Dual-model support with automated fallback (flagship 176MB `u2net` and 4.5MB lightweight `u2netp`).
- **Sub-Pixel Alpha Matting**: Captures wispy hair, translucent fabrics, glass edges, and fine fur.
- **Memory-Resident Model Singleton**: Zero cold-start latency on subsequent requests.

### 2. Interactive Creative Studio
- **Split Comparison Slider**: Drag-to-compare original photo vs AI cutout.
- **Cutout & Side-by-Side Modes**: Instant view switching with checkerboard transparency.
- **Canvas Zoom & Pan**: Zoom in up to 300% or fit-to-screen with sub-pixel crispness.
- **Live Background Replacer**:
  - Transparent checkerboard.
  - Solid colors with quick presets or HEX color picker.
  - Linear gradients with direction control (vertical, horizontal, diagonal).
  - Custom user-uploaded backdrop images.

### 3. Multi-Format Export & Genuine SVG Vectorizer
- **PNG**: Lossless original resolution preserving alpha channel.
- **JPG / JPEG**: High-quality (95%) composite onto chosen background color or gradient.
- **SVG Vectorizer**: Genuine raster-to-vector conversion into scalable XML `<path>` bezier geometry (via VisionCortex `vtracer` / OpenCV contour fallback) â€” *not* an embedded bitmap pretending to be vector.

### 4. Database Integration & Image Storage Management
- **Primary Database**: PostgreSQL (production) with automatic fallback to SQLite (`storage/lumina_studio.db`) for zero-configuration local development.
- **Structured Schema**:
  - `users`: User profiles with optional registration/login.
  - `images`: Image dimensions, file size, original/output formats, storage paths, and processing status.
  - `processing_history`: Audit trail of processing durations, background replacements, and export events.
- **Persistent Storage Hierarchy**:
  ```text
  storage/
    â”œâ”€â”€ users/<user_id>/<image_id>/
    â”‚    â”œâ”€â”€ original.png
    â”‚    â”œâ”€â”€ cutout.png
    â”‚    â””â”€â”€ exports/
    â””â”€â”€ guests/<guest_session_id>/<image_id>/
         â”œâ”€â”€ original.jpg
         â”œâ”€â”€ cutout.png
         â””â”€â”€ exports/
  ```
- **Synchronized Deletion**: Purging an image or clearing history permanently deletes both database rows and physical disk directories simultaneously.
- **Backup & Recovery**: Built-in script (`backend/backup.py`) for automated zip archive generation.

### 5. "My Image Library" User Gallery
- View, compare, and manage past cutouts.
- Search by image filename and filter by format (All, PNG, JPG, WEBP).
- Sort by date or name with paginated browsing.
- "Open in Studio" button to reload any historical cutout back into the editor for further background adjustments.
- Instant single image deletion and "Clear Entire History" actions.

---

## ðŸ—ï¸ Architecture & Project Structure

```text
BackgroundRemover/
â”œâ”€â”€ backend/
â”‚   â”œâ”€â”€ app.py                 # RESTful Flask backend & routing
â”‚   â”œâ”€â”€ remover.py             # U2-Net ONNX model inference engine
â”‚   â”œâ”€â”€ image_processor.py     # Pillow compositing & vtracer vectorizer
â”‚   â”œâ”€â”€ database.py            # SQLAlchemy models & PostgreSQL/SQLite engine
â”‚   â”œâ”€â”€ storage.py             # Persistent disk storage manager
â”‚   â”œâ”€â”€ migrations.py          # Automatic schema migration runner
â”‚   â”œâ”€â”€ backup.py              # Storage and database backup & recovery utility
â”‚   â””â”€â”€ requirements.txt       # Backend dependencies
â”œâ”€â”€ frontend/
â”‚   â”œâ”€â”€ index.html             # Single-page application UI with Studio & Library
â”‚   â”œâ”€â”€ style.css              # Dark luxury aesthetic design system
â”‚   â””â”€â”€ script.js              # State manager, split slider, API client, & gallery
â”œâ”€â”€ storage/                   # Persistent files (excluded from git)
â”œâ”€â”€ uploads/                   # Temporary upload buffer
â”œâ”€â”€ outputs/                   # Temporary output cache
â”œâ”€â”€ schema.sql                 # PostgreSQL DDL production schema
â”œâ”€â”€ gunicorn.conf.py           # Multi-threaded production WSGI configuration
â”œâ”€â”€ Dockerfile                 # Multi-stage production container build
â”œâ”€â”€ docker-compose.yml         # Compose stack: App + PostgreSQL 16 + Caddy SSL
â”œâ”€â”€ Caddyfile                  # Automatic Zero-Config Let's Encrypt HTTPS
â”œâ”€â”€ nginx.conf                 # Alternative production Nginx reverse proxy config
â”œâ”€â”€ deploy.sh                  # One-command Linux deployment script
â”œâ”€â”€ start_production.bat       # Windows production launcher (Waitress)
â”œâ”€â”€ start_server.bat           # Windows development launcher
â”œâ”€â”€ .env.example               # Environment variables template
â”œâ”€â”€ .gitignore                 # Excludes venv, runtime storage, secrets, models
â”œâ”€â”€ requirements.txt           # Root dependency manifest
â””â”€â”€ LICENSE                    # MIT License
```

---

## âš¡ Quick Start (Local Development)

### 1. Prerequisites
- Python 3.10+ (Python 3.11 recommended)
- Git

### 2. Setup Virtual Environment
```bash
# Clone or navigate into directory
cd BackgroundRemover

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run Database Migrations
```bash
python -m backend.migrations
```
*Note: If `DATABASE_URL` is omitted, the app automatically initializes SQLite at `storage/lumina_studio.db`.*

### 4. Launch Development Server
```bash
# Windows quick launcher:
start_server.bat

# Or run directly:
python backend/app.py
```
Open **`http://127.0.0.1:5000`** in your browser.

---

## ðŸ³ Production Deployment with Docker & Custom Domain

### 1. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` with your domain and database credentials:
```env
DOMAIN_NAME=parasnathpokharel.com.np
LETSENCRYPT_EMAIL=admin@parasnathpokharel.com.np
POSTGRES_PASSWORD=your_super_secret_password_here
SECRET_KEY=generate_with_openssl_rand_hex_32
```

### 2. Configure DNS Records for Your Domain
At your domain registrar or DNS provider (Cloudflare, Namecheap, GoDaddy, Route53, etc.), create two records:

| Type | Name / Host | Value / Target | TTL | Description |
|---|---|---|---|---|
| **A** | `@` (or apex domain) | `<Your_Server_IPv4_Address>` | Auto / 300 | Directs root domain `parasnathpokharel.com.np` to your VPS |
| **CNAME** | `www` | `parasnathpokharel.com.np` | Auto / 300 | Directs `www.parasnathpokharel.com.np` to your root domain |

### 3. Deploy Stack with Docker Compose
Run the automated deployment script:
```bash
chmod +x deploy.sh
./deploy.sh
```
Or run Docker Compose manually:
```bash
docker compose up -d --build
```

**What happens automatically:**
1. PostgreSQL 16 container starts and mounts persistent volume `postgres_data`.
2. Database schema migrations execute automatically (`schema.sql` and `migrations.py`).
3. Flask app starts with Gunicorn multi-threaded workers on port 5000.
4. Caddy reverse proxy automatically provisions a free, valid **Let's Encrypt / ZeroSSL** HTTPS certificate for `parasnathpokharel.com.np` and `www.parasnathpokharel.com.np`.
5. All images uploaded and cut out are stored in persistent volume `persistent_storage`.

---

## ðŸ–¥ï¸ Alternative Production Deployment (Native Systemd + Nginx)

If deploying directly on an Ubuntu/Debian VPS without Docker:

### 1. Install System Packages & PostgreSQL
```bash
sudo apt update && sudo apt install -y python3-pip python3-venv postgresql postgresql-contrib nginx certbot python3-certbot-nginx
```

### 2. Create PostgreSQL Database
```bash
sudo -u postgres psql
postgres=# CREATE DATABASE lumina_bgremover;
postgres=# CREATE USER lumina_user WITH ENCRYPTED PASSWORD 'StrongPasswordHere';
postgres=# GRANT ALL PRIVILEGES ON DATABASE lumina_bgremover TO lumina_user;
postgres=# \q
```

### 3. Create Systemd Service (`/etc/systemd/system/lumina.service`)
```ini
[Unit]
Description=Lumina AI Background Remover Gunicorn Service
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/BackgroundRemover
Environment="PATH=/var/www/BackgroundRemover/venv/bin"
Environment="DATABASE_URL=postgresql://lumina_user:StrongPasswordHere@localhost:5432/lumina_bgremover"
Environment="STORAGE_DIR=/var/www/BackgroundRemover/storage"
ExecStart=/var/www/BackgroundRemover/venv/bin/gunicorn -c gunicorn.conf.py backend.app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

### 4. Configure Nginx & SSL
Copy `nginx.conf` to `/etc/nginx/sites-available/lumina.conf`:
```bash
sudo ln -s /etc/nginx/sites-available/lumina.conf /etc/nginx/sites-enabled/
sudo certbot --nginx -d parasnathpokharel.com.np -d www.parasnathpokharel.com.np
sudo systemctl restart nginx
sudo systemctl enable --now lumina
```

---

## ðŸ—„ï¸ Database Backup & Restore

To take a snapshot of database records and stored images:
```bash
# Create a timestamped backup archive
python backend/backup.py

# Restore from a backup archive
python backend/backup.py restore backups/lumina_backup_YYYYMMDD_HHMMSS.zip
```

---

## ðŸ™ Push to GitHub Repository

To upload this project to your GitHub repository:

```bash
# 1. Initialize git if not already initialized
git init

# 2. Stage all project files (safe .gitignore prevents committing .env, venv, or uploads)
git add .

# 3. Commit changes
git commit -m "feat: complete AI background remover with PostgreSQL DB, storage, and production deploy"

# 4. Set default branch to main
git branch -M main

# 5. Link to your GitHub repository (replace with your repository URL)
git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPOSITORY_NAME>.git

# 6. Push to GitHub
git push -u origin main
```

*(If your remote repository already contains existing commits or a default README, run `git pull origin main --rebase` before pushing).*

---

## ðŸ”’ Privacy & Data Governance

- **Zero Third-Party Telemetry**: Images are processed directly on your server via local ONNX runtime neural inference.
- **Private Storage**: Stored images are isolated by user or guest session token.
- **Instant Erasure**: Users can permanently delete individual images or clear their entire library at any time via the frontend UI or `DELETE /api/images`.

---

## ðŸ“„ License
This project is licensed under the [MIT License](LICENSE).
