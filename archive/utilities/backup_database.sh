#!/bin/bash
# Phase 6 Pre-Safety: Database Backup Script for Linux
# Creates timestamped backup of ChromaDB before Phase 6 modifications

set -e  # Exit on error

# Configuration
CHROMA_DB_DIR="chroma_db"
ARCHIVE_DIR="archive"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="chromadb_backup_${TIMESTAMP}"
BACKUP_DIR="${ARCHIVE_DIR}/${BACKUP_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Phase 6: Pre-Safety Database Backup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if ChromaDB exists
if [ ! -d "$CHROMA_DB_DIR" ]; then
    echo -e "${RED}Error: ChromaDB directory not found at $CHROMA_DB_DIR${NC}"
    echo "This backup script should be run from the project root directory."
    exit 1
fi

# Create archive directory if it doesn't exist
mkdir -p "$ARCHIVE_DIR"

# Check available disk space
DB_SIZE=$(du -sm "$CHROMA_DB_DIR" | cut -f1)
AVAILABLE_SPACE=$(df -m "$ARCHIVE_DIR" | tail -1 | awk '{print $4}')

echo "Database size: ${DB_SIZE}MB"
echo "Available space: ${AVAILABLE_SPACE}MB"

if [ "$AVAILABLE_SPACE" -lt "$((DB_SIZE + 100))" ]; then
    echo -e "${RED}Warning: Low disk space!${NC}"
    echo "Need at least $((DB_SIZE + 100))MB, but only ${AVAILABLE_SPACE}MB available."
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Stop any running processes (optional)
echo -e "${YELLOW}Checking for running ingestion processes...${NC}"
RUNNING_PROCS=$(pgrep -f "process_wiki.py\|chromadb_ingest.py" || true)
if [ -n "$RUNNING_PROCS" ]; then
    echo -e "${YELLOW}Warning: Found running processes:${NC}"
    ps -f -p $RUNNING_PROCS || true
    read -p "Stop these processes? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kill $RUNNING_PROCS
        sleep 2
    fi
fi

# Perform backup
echo ""
echo "Creating backup: $BACKUP_DIR"
echo "This may take a minute..."

# Use rsync for efficient copying
if command -v rsync &> /dev/null; then
    rsync -av --progress "$CHROMA_DB_DIR/" "$BACKUP_DIR/"
else
    # Fallback to cp
    cp -r "$CHROMA_DB_DIR" "$BACKUP_DIR"
fi

# Verify backup
echo ""
echo "Verifying backup integrity..."
BACKUP_SIZE=$(du -sm "$BACKUP_DIR" | cut -f1)
SIZE_DIFF=$((DB_SIZE - BACKUP_SIZE))
SIZE_DIFF_ABS=${SIZE_DIFF#-}  # Absolute value

if [ "$SIZE_DIFF_ABS" -gt "$((DB_SIZE / 20))" ]; then
    echo -e "${RED}Error: Backup size mismatch!${NC}"
    echo "Original: ${DB_SIZE}MB, Backup: ${BACKUP_SIZE}MB"
    exit 1
fi

# Count files
ORIGINAL_FILES=$(find "$CHROMA_DB_DIR" -type f | wc -l)
BACKUP_FILES=$(find "$BACKUP_DIR" -type f | wc -l)

if [ "$ORIGINAL_FILES" != "$BACKUP_FILES" ]; then
    echo -e "${YELLOW}Warning: File count mismatch${NC}"
    echo "Original: ${ORIGINAL_FILES} files, Backup: ${BACKUP_FILES} files"
fi

# Create metadata file
METADATA_FILE="${BACKUP_DIR}/backup_metadata.json"
cat > "$METADATA_FILE" << EOF
{
  "backup_timestamp": "$(date -Iseconds)",
  "backup_name": "$BACKUP_NAME",
  "original_db_path": "$CHROMA_DB_DIR",
  "backup_path": "$BACKUP_DIR",
  "database_size_mb": $DB_SIZE,
  "backup_size_mb": $BACKUP_SIZE,
  "file_count": $ORIGINAL_FILES,
  "backup_reason": "Pre-Phase 6 safety archive",
  "phase": "Phase 6: RAG Metadata Enhancement",
  "hostname": "$(hostname)",
  "user": "$(whoami)"
}
EOF

# Success message
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Backup completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Backup location: $BACKUP_DIR"
echo "Backup size: ${BACKUP_SIZE}MB (Original: ${DB_SIZE}MB)"
echo "File count: $BACKUP_FILES files"
echo ""
echo "Backup metadata saved to: $METADATA_FILE"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "1. Verify backup by checking $BACKUP_DIR"
echo "2. Proceed with Phase 6 implementation"
echo "3. If issues occur, restore with: bash restore_database.sh $BACKUP_NAME"
echo ""

# Update BACKUP_GUIDE.md
if [ -f "BACKUP_GUIDE.md" ]; then
    echo "<!-- Last backup: $BACKUP_NAME at $(date) -->" >> BACKUP_GUIDE.md
fi

exit 0
