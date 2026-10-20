"""
Database Service for VaaniAI.
Provides unified access to MongoDB collections (sounds, practice_items, attempts, users)
with automatic fallback to JSON seed files if MongoDB is not running locally.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from config import Config

logger = logging.getLogger("vaaniai.db")

class DatabaseService:
    def __init__(self):
        self.client = None
        self.db = None
        self.use_mongo = False
        
        # In-memory storage fallback
        self._sounds_cache = {}
        self._practice_items = []
        self._attempts = []
        self._users = {}
        
        # Load local JSON seed files into memory first
        self._load_local_seeds()
        # Attempt MongoDB connection
        self._init_mongo()

    def _load_local_seeds(self):
        """Loads seed data from disk to ensure fallback availability."""
        seed_dir = Path(__file__).resolve().parent.parent / "seed"
        sounds_file = seed_dir / "sounds.json"
        practice_file = seed_dir / "practice_items.json"
        
        if sounds_file.exists():
            try:
                with open(sounds_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for s in data:
                        self._sounds_cache[s["symbol"]] = s
                logger.info(f"Loaded {len(self._sounds_cache)} sounds from seed JSON.")
            except Exception as e:
                logger.error(f"Error loading sounds.json: {e}")
                
        if practice_file.exists():
            try:
                with open(practice_file, "r", encoding="utf-8") as f:
                    self._practice_items = json.load(f)
                logger.info(f"Loaded {len(self._practice_items)} practice items from seed JSON.")
            except Exception as e:
                logger.error(f"Error loading practice_items.json: {e}")
                
        # Default demo user
        self._users["student_demo"] = {
            "_id": "student_demo",
            "name": "Arya Sharma",
            "language": "sanskrit",
            "level": "beginner"
        }

    def _init_mongo(self):
        """Attempt to connect to MongoDB; gracefully handle absence."""
        try:
            from pymongo import MongoClient
            self.client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=1500)
            # Test ping
            self.client.admin.command('ping')
            self.db = self.client[Config.DB_NAME]
            self.use_mongo = True
            logger.info(f"Connected to MongoDB at {Config.MONGO_URI} (DB: {Config.DB_NAME})")
            
            # Sync memory to Mongo if Mongo collections are empty
            if self.db["sounds"].count_documents({}) == 0 and self._sounds_cache:
                for sound in self._sounds_cache.values():
                    self.db["sounds"].update_one({"symbol": sound["symbol"]}, {"$set": sound}, upsert=True)
            if self.db["practice_items"].count_documents({}) == 0 and self._practice_items:
                for item in self._practice_items:
                    self.db["practice_items"].update_one({"_id": item["_id"]}, {"$set": item}, upsert=True)
            if self.db["users"].count_documents({"_id": "student_demo"}) == 0:
                self.db["users"].update_one({"_id": "student_demo"}, {"$set": self._users["student_demo"]}, upsert=True)
                
        except Exception as e:
            self.use_mongo = False
            logger.warning(f"MongoDB not available ({e}). Using in-memory fallback store.")

    def is_mongo_connected(self):
        if not self.use_mongo or not self.client:
            return False
        try:
            self.client.admin.command('ping')
            return True
        except Exception:
            return False

    def get_sound(self, symbol):
        """Fetch sound characteristics by Devanagari character."""
        if not symbol:
            return None
            
        if self.use_mongo:
            try:
                sound = self.db["sounds"].find_one({"symbol": symbol}, {"_id": 0})
                if sound:
                    return sound
            except Exception as e:
                logger.error(f"Mongo error in get_sound: {e}")
                
        # Fallback to in-memory dictionary
        return self._sounds_cache.get(symbol)

    def get_all_sounds(self):
        """Fetch all sounds."""
        if self.use_mongo:
            try:
                sounds = list(self.db["sounds"].find({}, {"_id": 0}))
                if sounds:
                    return sounds
            except Exception as e:
                logger.error(f"Mongo error in get_all_sounds: {e}")
        return list(self._sounds_cache.values())

    def get_items(self, level=None, language=None):
        """Fetch practice items filtered by level and language."""
        query = {}
        if level:
            query["level"] = level.lower()
        if language:
            query["language"] = language.lower()

        if self.use_mongo:
            try:
                items = list(self.db["practice_items"].find(query))
                for item in items:
                    item["_id"] = str(item["_id"])
                if items:
                    return items
            except Exception as e:
                logger.error(f"Mongo error in get_items: {e}")

        # In-memory filter
        res = []
        for item in self._practice_items:
            match = True
            if level and item.get("level", "").lower() != level.lower():
                match = False
            if language and item.get("language", "").lower() != language.lower():
                match = False
            if match:
                res.append(item)
        return res

    def get_item_by_id(self, item_id):
        """Fetch single practice item by ID."""
        if not item_id:
            return None
        if self.use_mongo:
            try:
                item = self.db["practice_items"].find_one({"_id": item_id})
                if item:
                    item["_id"] = str(item["_id"])
                    return item
            except Exception as e:
                logger.error(f"Mongo error in get_item_by_id: {e}")

        for item in self._practice_items:
            if item.get("_id") == item_id:
                return item
        return None

    def save_attempt(self, user_id, item_id, score, errors, recognized_text="", target_text="", char_results=None, tip=""):
        """Record an articulation attempt with detected errors."""
        doc = {
            "user_id": user_id or "student_demo",
            "item_id": item_id,
            "target_text": target_text or "",
            "score": int(score),
            "errors": errors or [],
            "char_results": char_results or [],
            "tip": tip or "",
            "recognized_text": recognized_text or "",
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        
        if self.use_mongo:
            try:
                res = self.db["attempts"].insert_one(doc)
                doc["_id"] = str(res.inserted_id)
                return doc
            except Exception as e:
                logger.error(f"Mongo error in save_attempt: {e}")

        doc["_id"] = f"att_{len(self._attempts) + 1}"
        self._attempts.append(doc)
        return doc

    def get_attempt_by_id(self, attempt_id):
        """Fetch a single attempt document by ID."""
        if not attempt_id:
            return None

        att = None
        if self.use_mongo:
            try:
                from bson.objectid import ObjectId
                try:
                    att = self.db["attempts"].find_one({"_id": ObjectId(attempt_id)})
                except Exception:
                    att = self.db["attempts"].find_one({"_id": attempt_id})
                if att:
                    att["_id"] = str(att["_id"])
            except Exception as e:
                logger.error(f"Mongo error in get_attempt_by_id: {e}")

        if not att:
            for a in self._attempts:
                if str(a.get("_id")) == str(attempt_id):
                    att = a
                    break

        if att:
            self._enrich_attempt_item_info(att)
        return att

    def _enrich_attempt_item_info(self, att):
        """Enriches an attempt with metadata from the practice item catalog."""
        item_id = att.get("item_id")
        if item_id == "free_mode":
            att.setdefault("target_text", att.get("recognized_text", "Free Practice"))
            att.setdefault("target_title", "Free Mode Shloka")
            att.setdefault("item_type", "shloka")
        elif item_id:
            item = self.get_item_by_id(item_id)
            if item:
                if not att.get("target_text"):
                    att["target_text"] = item.get("text", "")
                att.setdefault("target_title", item.get("title") or item.get("text", ""))
                att.setdefault("target_transliteration", item.get("transliteration", ""))
                att.setdefault("target_meaning", item.get("meaning", ""))
                att.setdefault("item_type", item.get("type", "letter"))

    def delete_attempt(self, attempt_id, user_id=None):
        """Deletes a single attempt record by ID."""
        if not attempt_id:
            return False

        deleted = False
        if self.use_mongo:
            try:
                from bson.objectid import ObjectId
                query = {}
                try:
                    query["_id"] = ObjectId(attempt_id)
                except Exception:
                    query["_id"] = attempt_id
                if user_id:
                    query["user_id"] = user_id

                res = self.db["attempts"].delete_one(query)
                deleted = res.deleted_count > 0
            except Exception as e:
                logger.error(f"Mongo error in delete_attempt: {e}")

        # Also purge from in-memory fallback list
        before = len(self._attempts)
        self._attempts = [
            a for a in self._attempts 
            if not (str(a.get("_id")) == str(attempt_id) and (not user_id or a.get("user_id") == user_id))
        ]
        if len(self._attempts) < before:
            deleted = True

        return deleted

    def delete_all_attempts(self, user_id="student_demo"):
        """Deletes all session history records for a student."""
        user_id = user_id or "student_demo"
        deleted_count = 0

        if self.use_mongo:
            try:
                query = {"user_id": user_id} if user_id else {}
                res = self.db["attempts"].delete_many(query)
                deleted_count = res.deleted_count
            except Exception as e:
                logger.error(f"Mongo error in delete_all_attempts: {e}")

        before = len(self._attempts)
        if user_id:
            self._attempts = [a for a in self._attempts if a.get("user_id") != user_id]
        else:
            self._attempts = []
        deleted_count = max(deleted_count, before - len(self._attempts))

        return deleted_count

    def get_user_progress(self, user_id):
        """
        Fetch attempts and compute weak sounds aggregated by varga.
        """
        user_id = user_id or "student_demo"
        attempts = []
        
        if self.use_mongo:
            try:
                cursor = self.db["attempts"].find({"user_id": user_id}).sort("created_at", 1)
                for a in cursor:
                    a["_id"] = str(a["_id"])
                    self._enrich_attempt_item_info(a)
                    attempts.append(a)
            except Exception as e:
                logger.error(f"Mongo error in get_user_progress: {e}")
                
        if not attempts:
            mem_attempts = [a for a in self._attempts if a.get("user_id") == user_id]
            for a in mem_attempts:
                self._enrich_attempt_item_info(a)
            attempts = mem_attempts

        # Calculate weak sounds grouped by varga
        weak_counts = {}
        for att in attempts:
            for err in att.get("errors", []):
                sym = err.get("expected_char") or err.get("target_symbol")
                if not sym:
                    continue
                sound_meta = self.get_sound(sym)
                varga = sound_meta.get("varga", "other") if sound_meta else "other"
                
                if varga not in weak_counts:
                    weak_counts[varga] = {
                        "varga": varga,
                        "error_count": 0,
                        "sounds": {}
                    }
                weak_counts[varga]["error_count"] += 1
                sound_entry = weak_counts[varga]["sounds"].setdefault(sym, {
                    "symbol": sym,
                    "roman": sound_meta.get("roman", "") if sound_meta else "",
                    "count": 0,
                    "sthana": sound_meta.get("sthana", "") if sound_meta else "",
                    "tip": sound_meta.get("anatomical_tip", "") if sound_meta else ""
                })
                sound_entry["count"] += 1

        return {
            "user_id": user_id,
            "total_attempts": len(attempts),
            "attempts": attempts,
            "weak_sounds": weak_counts
        }

# Singleton instance
db_service = DatabaseService()
