#!/usr/bin/env python3
"""Quick script to sync new practice items into MongoDB."""
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import Config

def sync_items():
    seed_dir = Path(__file__).resolve().parent / "seed"
    practice_file = seed_dir / "practice_items.json"
    
    if not practice_file.exists():
        print("ERROR: practice_items.json not found!")
        return
    
    with open(practice_file, "r", encoding="utf-8") as f:
        items = json.load(f)
    
    print(f"Loaded {len(items)} items from practice_items.json")
    
    try:
        from pymongo import MongoClient
        client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=3000)
        client.admin.command('ping')
        db = client[Config.DB_NAME]
        
        updated = 0
        inserted = 0
        for item in items:
            result = db["practice_items"].update_one(
                {"_id": item["_id"]},
                {"$set": item},
                upsert=True
            )
            if result.upserted_id:
                inserted += 1
            elif result.modified_count > 0:
                updated += 1
        
        total = db["practice_items"].count_documents({})
        print(f"Sync complete: {inserted} new, {updated} updated, {total} total in DB")
        client.close()
        
    except Exception as e:
        print(f"MongoDB sync failed: {e}")
        print("Items will still be available from in-memory fallback.")

if __name__ == "__main__":
    sync_items()
