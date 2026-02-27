#!/bin/bash

# Backup script for nyaya-ams project
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="nyaya-ams_backup_${TIMESTAMP}.tar.gz"
BACKUP_DIR="../backups"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create backup excluding unnecessary files
tar -czf "${BACKUP_DIR}/${BACKUP_NAME}" \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='data/faiss_store' \
    -C .. nyaya-ams

echo "Backup created: ${BACKUP_DIR}/${BACKUP_NAME}"
