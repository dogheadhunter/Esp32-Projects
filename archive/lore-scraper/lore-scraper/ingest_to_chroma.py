"""
ChromaDB Ingestion Script for Fallout 76 Lore
Optimized for RTX 3060 GPU with all-mpnet-base-v2 embeddings
"""

import os
import json
import chromadb
from chromadb.utils import embedding_functions
from tqdm import tqdm

import argparse
import sys

# Configuration
BASE_DIR = r"c:\esp32-project\lore\fallout76_canon\entities"
CHROMA_DIR = r"c:\esp32-project\lore\julie_chroma_db"
COLLECTION_NAME = "fallout76_julie_v1"
BATCH_SIZE = 100
MIN_DESCRIPTION_LENGTH = 20

def build_contextual_text(data):
    """Build semantic-rich text blob for embedding."""
    name = data.get("name", "Unknown")
    entity_type = data.get("type", "entity")
    region = data.get("geography", {}).get("region", "Unknown")
    temporal = data.get("temporal", {}).get("active_during", [])
    description = data.get("description", "")
    
    # Format temporal
    time_str = f"Active during {', '.join(temporal)}." if temporal else ""
    
    # Build contextual text
    text = f'"{name}" is a {entity_type} in {region}. {time_str} {description}'
    
    return text.strip()

def extract_metadata(data):
    """Extract metadata for filtering."""
    return {
        "entity_id": data.get("id", ""),
        "name": data.get("name", ""),
        "type": data.get("type", ""),
        "region": data.get("geography", {}).get("region", ""),
        "specific_location": data.get("geography", {}).get("specific_location", ""),
        "temporal_start": data.get("temporal", {}).get("active_during", [""])[0],
        "julie_knowledge": data.get("knowledge_accessibility", {}).get("julie_2102", "unknown"),
        "confidence": str(data.get("verification", {}).get("confidence", 0.6)),
        "tags": ",".join(data.get("tags", []))
    }

def ingest_entities(reset_db=False):
    """Ingest all entities into ChromaDB."""
    
    # Initialize ChromaDB with GPU-accelerated embeddings
    print("Initializing ChromaDB with GPU embeddings (all-mpnet-base-v2)...")
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Use sentence-transformers with GPU
    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="sentence-transformers/all-mpnet-base-v2",
        device="cuda"  # Use GPU
    )

    # Handle Reset
    if reset_db:
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"Deleted existing collection: {COLLECTION_NAME}")
        except Exception:
            pass # Collection didn't exist

    # Create or get collection
    try:
        collection = client.create_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_function,
            metadata={"description": "Fallout 76 lore optimized for Julie AI (2102)"}
        )
        print(f"Created new collection: {COLLECTION_NAME}")
    except Exception as e:
        print(f"Collection exists, retrieving: {COLLECTION_NAME}")
        collection = client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_function
        )
    
    # Collect all JSON files
    all_files = []
    for root, dirs, files in os.walk(BASE_DIR):
        for filename in files:
            if filename.endswith(".json"):
                all_files.append(os.path.join(root, filename))
    
    print(f"\nFound {len(all_files)} entities to ingest...")
    
    # Process in batches
    batch_ids = []
    batch_texts = []
    batch_metadatas = []
    skipped = 0
    errors = 0
    
    for filepath in tqdm(all_files, desc="Processing entities"):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Skip if description too short
            description = data.get("description", "")
            if len(description) < MIN_DESCRIPTION_LENGTH:
                skipped += 1
                continue
            
            # Build contextual text and metadata
            text = build_contextual_text(data)
            metadata = extract_metadata(data)
            entity_id = data.get("id", os.path.basename(filepath).replace(".json", ""))
            
            # Add to batch
            batch_ids.append(entity_id)
            batch_texts.append(text)
            batch_metadatas.append(metadata)
            
            # Insert batch when full
            if len(batch_ids) >= BATCH_SIZE:
                collection.add(
                    ids=batch_ids,
                    documents=batch_texts,
                    metadatas=batch_metadatas
                )
                batch_ids = []
                batch_texts = []
                batch_metadatas = []
        
        except Exception as e:
            errors += 1
            tqdm.write(f"Error processing {filepath}: {e}")
    
    # Insert remaining batch
    if batch_ids:
        collection.add(
            ids=batch_ids,
            documents=batch_texts,
            metadatas=batch_metadatas
        )
    
    print(f"\n✓ Ingestion Complete:")
    print(f"  Ingested: {len(all_files) - skipped - errors}")
    print(f"  Skipped (stub descriptions): {skipped}")
    print(f"  Errors: {errors}")
    print(f"  Collection: {COLLECTION_NAME}")
    print(f"  Location: {CHROMA_DIR}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest Fallout 76 entities into ChromaDB")
    parser.add_argument("--reset", action="store_true", help="Delete existing collection before ingestion")
    args = parser.parse_args()
    
    ingest_entities(reset_db=args.reset)
