#!/bin/bash
# Phase 6: Database Restore Script for Linux
# Restores ChromaDB from backup

set -e  # Exit on error

# Configuration
ARCHIVE_DIR="archive"
CHROMA_DB_DIR="chroma_db"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ChromaDB Database Restore${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check for backup name argument
if [ -z "$1" ]; then
    echo "Available backups in $ARCHIVE_DIR:"
    ls -lhd "$ARCHIVE_DIR"/chromadb_backup_* 2>/dev/null || echo "No backups found"
    echo ""
    echo "Usage: $0 <backup_name>"
    echo "Example: $0 chromadb_backup_20260117_143000"
    exit 1
fi

BACKUP_NAME="$1"
BACKUP_DIR="${ARCHIVE_DIR}/${BACKUP_NAME}"

# Verify backup exists
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${RED}Error: Backup not found at $BACKUP_DIR${NC}"
    exit 1
fi

# Show backup info
if [ -f "${BACKUP_DIR}/backup_metadata.json" ]; then
    echo "Backup metadata:"
    cat "${BACKUP_DIR}/backup_metadata.json"
    echo ""
fi

# Confirm restore
echo -e "${YELLOW}WARNING: This will replace the current database!${NC}"
echo "Current database: $CHROMA_DB_DIR"
echo "Restore from: $BACKUP_DIR"
echo ""
read -p "Are you sure you want to restore? (yes/NO) " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Restore cancelled."
    exit 0
fi

# Backup current database if it exists
if [ -d "$CHROMA_DB_DIR" ]; then
    CURRENT_BACKUP="${CHROMA_DB_DIR}_before_restore_$(date +%Y%m%d_%H%M%S)"
    echo "Backing up current database to: $CURRENT_BACKUP"
    mv "$CHROMA_DB_DIR" "$CURRENT_BACKUP"
fi

# Restore from backup
echo "Restoring database..."
if command -v rsync &> /dev/null; then
    rsync -av --progress "$BACKUP_DIR/" "$CHROMA_DB_DIR/"
else
    cp -r "$BACKUP_DIR" "$CHROMA_DB_DIR"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Restore completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Database restored to: $CHROMA_DB_DIR"
echo "From backup: $BACKUP_DIR"
echo ""

exit 0
