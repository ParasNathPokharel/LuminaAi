-- ====================================================================
-- Lumina AI — Background Remover Production PostgreSQL Database Schema
-- Compatible with PostgreSQL 13+ (tested on PostgreSQL 16)
-- ====================================================================

-- 1. Enable UUID Extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(100) UNIQUE,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 3. Images Table
-- Stores metadata and persistent file paths.
-- Raw binary blob data is NOT stored directly in this table.
CREATE TABLE IF NOT EXISTS images (
    image_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(user_id) ON DELETE SET NULL,
    guest_session_id VARCHAR(64),
    original_filename VARCHAR(255) NOT NULL,
    original_image_path VARCHAR(512) NOT NULL,
    processed_image_path VARCHAR(512) NOT NULL,
    original_format VARCHAR(32) NOT NULL DEFAULT 'png',
    output_format VARCHAR(32) NOT NULL DEFAULT 'png',
    file_size INTEGER NOT NULL DEFAULT 0,
    image_width INTEGER NOT NULL DEFAULT 0,
    image_height INTEGER NOT NULL DEFAULT 0,
    processing_status VARCHAR(32) NOT NULL DEFAULT 'completed',
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

CREATE INDEX IF NOT EXISTS idx_images_user_id ON images(user_id);
CREATE INDEX IF NOT EXISTS idx_images_guest_session ON images(guest_session_id);
CREATE INDEX IF NOT EXISTS idx_images_created_at ON images(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_images_status ON images(processing_status);
CREATE INDEX IF NOT EXISTS idx_images_guest_created ON images(guest_session_id, created_at DESC);

-- 4. Processing History Table
-- Audits each processing step, background replacement, or vector export.
CREATE TABLE IF NOT EXISTS processing_history (
    history_id VARCHAR(36) PRIMARY KEY,
    image_id VARCHAR(36) NOT NULL REFERENCES images(image_id) ON DELETE CASCADE,
    processing_time DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    selected_output_format VARCHAR(32) NOT NULL DEFAULT 'png',
    background_type VARCHAR(32) NOT NULL DEFAULT 'transparent',
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

CREATE INDEX IF NOT EXISTS idx_history_image_id ON processing_history(image_id);
CREATE INDEX IF NOT EXISTS idx_history_created_at ON processing_history(created_at DESC);
