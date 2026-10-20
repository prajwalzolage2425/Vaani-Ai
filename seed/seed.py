#!/usr/bin/env python3
"""
Seed script for VaaniAI MongoDB Database.
Seeds:
- sounds: 25 sparsha consonants, antastha, ushma, and vowels with Paninian Sthāna & Prayatna
- practice_items: Minimal pairs, words, and shlokas
- users: Default demo student account
"""

import os
import sys
import json
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import Config
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

def load_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def run_seed():
    print("=" * 60)
    print("  VaaniAI - Indian Knowledge Systems Database Seeder")
    print("=" * 60)
    print(f"Connecting to MongoDB at: {Config.MONGO_URI} (Database: {Config.DB_NAME})")
    
    try:
        client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=3000)
        # Test connection
        client.admin.command('ping')
        db = client[Config.DB_NAME]
        print("Connected to MongoDB successfully!")
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"\n[WARNING] Could not connect to MongoDB: {e}")
        print("Note: The VaaniAI application includes a built-in memory/JSON fallback")
        print("so you can still run the web app and demo without a local MongoDB service.\n")
        return False

    seed_dir = BASE_DIR / "seed"
    sounds_file = seed_dir / "sounds.json"
    practice_file = seed_dir / "practice_items.json"
    
    # 1. Seed Sounds
    if sounds_file.exists():
        sounds_data = load_json(sounds_file)
        sounds_col = db["sounds"]
        sounds_col.delete_many({})
        for sound in sounds_data:
            sounds_col.update_one({"symbol": sound["symbol"]}, {"$set": sound}, upsert=True)
        print(f"  [OK] Seeded {len(sounds_data)} Sanskrit sounds into 'sounds' collection.")
    else:
        print(f"  [ERROR] File not found: {sounds_file}")

    # 2. Seed Practice Items
    if practice_file.exists():
        practice_data = load_json(practice_file)
        practice_col = db["practice_items"]
        practice_col.delete_many({})
        for item in practice_data:
            practice_col.update_one({"_id": item["_id"]}, {"$set": item}, upsert=True)
        print(f"  [OK] Seeded {len(practice_data)} items into 'practice_items' collection.")
    else:
        print(f"  [ERROR] File not found: {practice_file}")

    # 3. Seed Default Demo User
    users_col = db["users"]
    demo_user = {
        "_id": "student_demo",
        "name": "Arya Sharma",
        "language": "sanskrit",
        "level": "beginner"
    }
    users_col.update_one({"_id": demo_user["_id"]}, {"$set": demo_user}, upsert=True)
    print("  [OK] Seeded default user 'Arya Sharma' (student_demo) into 'users' collection.")

    print("\nDatabase seeding completed successfully!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    run_seed()
