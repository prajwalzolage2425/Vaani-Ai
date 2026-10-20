"""
VaaniAI - Sanskrit Pronunciation & Phonetic Correction System
Grounded in Indian Knowledge Systems (Shiksha, Vedanga of Phonetics).

Main Flask Application.
"""

import os
import uuid
import logging
from pathlib import Path
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename

from config import Config
from services.db_service import db_service
from services.phonetics_service import PhoneticsService
from services.gemini_service import gemini_service

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("vaaniai.app")

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)
app.config.from_object(Config)
CORS(app)

# Ensure upload directory exists
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

# -------------------------------------------------------------
# Frontend Page Routes
# -------------------------------------------------------------

@app.route("/")
def index():
    """Home page: Choose language, level, and start practicing."""
    return render_template(
        "index.html",
        demo_mode=Config.DEMO_MODE,
        gemini_model=Config.GEMINI_MODEL
    )

@app.route("/practice")
def practice():
    """Practice page: Audio recording, Sthāna mouth cross-section, real-time feedback."""
    return render_template(
        "practice.html",
        demo_mode=Config.DEMO_MODE,
        gemini_model=Config.GEMINI_MODEL
    )

@app.route("/dashboard")
def dashboard():
    """Dashboard page: Attempt history, Chart.js progress graph, weak sounds by varga."""
    return render_template(
        "dashboard.html",
        demo_mode=Config.DEMO_MODE,
        gemini_model=Config.GEMINI_MODEL
    )

# -------------------------------------------------------------
# REST API Endpoints
# -------------------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health():
    """Health check: reports system status, MongoDB state, and Gemini configuration."""
    mongo_ok = db_service.is_mongo_connected()
    gemini_configured = bool(Config.GEMINI_API_KEY)
    
    return jsonify({
        "status": "healthy",
        "app": "VaaniAI",
        "version": "1.0.0",
        "iks_foundation": "Pāṇinīya Śikṣā (पाणिनीय शिक्षा)",
        "mongo_connected": mongo_ok,
        "gemini_model": Config.GEMINI_MODEL,
        "gemini_configured": gemini_configured,
        "demo_mode": Config.DEMO_MODE
    }), 200

@app.route("/api/items", methods=["GET"])
def get_items():
    """
    GET /api/items?level=&language=
    Fetches practice items matching criteria.
    """
    level = request.args.get("level", None)
    language = request.args.get("language", None)
    
    try:
        items = db_service.get_items(level=level, language=language)
        return jsonify({
            "success": True,
            "count": len(items),
            "items": items
        }), 200
    except Exception as e:
        logger.error(f"Error in GET /api/items: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/sounds/<symbol>", methods=["GET"])
def get_sound(symbol):
    """
    GET /api/sounds/<symbol>
    Fetches phonetic metadata for a specific character.
    """
    try:
        sound = db_service.get_sound(symbol)
        if not sound:
            return jsonify({
                "success": False,
                "error": f"Phonetic sound '{symbol}' not found in catalog"
            }), 404
            
        return jsonify({
            "success": True,
            "sound": sound
        }), 200
    except Exception as e:
        logger.error(f"Error in GET /api/sounds/{symbol}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/sounds", methods=["GET"])
def get_all_sounds():
    """
    GET /api/sounds
    Fetches complete catalog of sounds.
    """
    try:
        sounds = db_service.get_all_sounds()
        return jsonify({
            "success": True,
            "count": len(sounds),
            "sounds": sounds
        }), 200
    except Exception as e:
        logger.error(f"Error in GET /api/sounds: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/analyze", methods=["POST"])
def analyze_pronunciation():
    """
    POST /api/analyze
    Multipart form:
    - audio: WebM / WAV audio blob from MediaRecorder
    - item_id: practice item ID
    - user_id: student username or ID
    - force_demo: (optional 'true'/'false')
    """
    item_id = request.form.get("item_id")
    user_id = request.form.get("user_id", "student_demo")
    force_demo = request.form.get("force_demo", "false").lower() in ("true", "1")

    if not item_id:
        return jsonify({"success": False, "error": "Missing required field: item_id"}), 400

    target_item = db_service.get_item_by_id(item_id)
    if not target_item:
        return jsonify({"success": False, "error": f"Target item '{item_id}' not found"}), 404

    # Handle audio upload
    audio_file = request.files.get("audio")
    temp_path = None
    
    if audio_file and audio_file.filename != "":
        filename = secure_filename(audio_file.filename)
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        temp_path = Path(Config.UPLOAD_FOLDER) / unique_name
        audio_file.save(str(temp_path))
        logger.info(f"Saved uploaded audio to: {temp_path}")

    try:
        # Run phonetic evaluation
        analysis_result = gemini_service.analyze_audio(
            audio_path=temp_path,
            target_item=target_item,
            is_demo_requested=force_demo
        )

        # Persist attempt to MongoDB or memory store with full diagnostics
        saved_attempt = db_service.save_attempt(
            user_id=user_id,
            item_id=item_id,
            score=analysis_result["score"],
            errors=analysis_result["errors"],
            recognized_text=analysis_result.get("recognized_text", ""),
            target_text=target_item.get("text", "") or target_item.get("title", ""),
            char_results=analysis_result.get("char_results", []),
            tip=analysis_result.get("tip", "")
        )

        response_payload = {
            "success": True,
            "attempt_id": saved_attempt.get("_id"),
            "target_item": target_item,
            "score": analysis_result["score"],
            "overall_clarity": analysis_result.get("overall_clarity", 95),
            "recognized_text": analysis_result.get("recognized_text", ""),
            "recognized_transliteration": analysis_result.get("recognized_transliteration", ""),
            "tip": analysis_result["tip"],
            "errors": analysis_result["errors"],
            "char_results": analysis_result["char_results"],
            "demo_mode": analysis_result.get("demo_mode", Config.DEMO_MODE)
        }

        return jsonify(response_payload), 200

    except Exception as e:
        logger.error(f"Error during pronunciation analysis: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "Failed to analyze pronunciation. Please try again.",
            "details": str(e)
        }), 500

    finally:
        # Clean up temporary audio file to preserve disk space
        if temp_path and temp_path.exists():
            try:
                os.remove(temp_path)
            except Exception:
                pass

@app.route("/api/progress/<user_id>", methods=["GET"])
def get_progress(user_id):
    """
    GET /api/progress/<user_id>
    Fetches attempt history and weak sounds grouped by varga for the student.
    """
    try:
        progress = db_service.get_user_progress(user_id)
        return jsonify({
            "success": True,
            "progress": progress
        }), 200
    except Exception as e:
        logger.error(f"Error in GET /api/progress/{user_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/progress/<user_id>", methods=["DELETE"])
def clear_user_history(user_id):
    """
    DELETE /api/progress/<user_id>
    Clears all session attempt history for a student.
    """
    try:
        deleted_count = db_service.delete_all_attempts(user_id)
        return jsonify({
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Successfully deleted {deleted_count} session history records."
        }), 200
    except Exception as e:
        logger.error(f"Error in DELETE /api/progress/{user_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/attempts/<attempt_id>", methods=["GET"])
def get_attempt_details(attempt_id):
    """
    GET /api/attempts/<attempt_id>
    Fetches full diagnostic details for a single attempt.
    """
    try:
        attempt = db_service.get_attempt_by_id(attempt_id)
        if not attempt:
            return jsonify({"success": False, "error": f"Attempt '{attempt_id}' not found"}), 404
        return jsonify({"success": True, "attempt": attempt}), 200
    except Exception as e:
        logger.error(f"Error in GET /api/attempts/{attempt_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/attempts/<attempt_id>", methods=["DELETE"])
def delete_attempt_record(attempt_id):
    """
    DELETE /api/attempts/<attempt_id>
    Deletes an individual attempt from session history.
    """
    try:
        user_id = request.args.get("user_id")
        deleted = db_service.delete_attempt(attempt_id, user_id=user_id)
        if not deleted:
            return jsonify({"success": False, "error": f"Attempt '{attempt_id}' not found or already deleted"}), 404
        return jsonify({"success": True, "message": "Attempt deleted successfully"}), 200
    except Exception as e:
        logger.error(f"Error in DELETE /api/attempts/{attempt_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# -------------------------------------------------------------
# Free Mode Page Route
# -------------------------------------------------------------

@app.route("/free")
def free_mode():
    """Free Mode page: Record any shloka, 3-pass AI analysis."""
    return render_template(
        "free.html",
        demo_mode=Config.DEMO_MODE,
        gemini_model=Config.GEMINI_MODEL
    )

# -------------------------------------------------------------
# Free Mode API Endpoints (3-Pass Pipeline)
# -------------------------------------------------------------

@app.route("/api/free/transcribe", methods=["POST"])
def free_transcribe():
    """
    FREE MODE Pass 1: Upload audio → Gemini transcribes to Devanagari.
    Returns: { heard_text, heard_transliteration, clarity }
    """
    audio_file = request.files.get("audio")
    if not audio_file or audio_file.filename == "":
        return jsonify({"success": False, "error": "No audio file provided"}), 400

    filename = secure_filename(audio_file.filename)
    unique_name = f"free_{uuid.uuid4().hex}_{filename}"
    temp_path = Path(Config.UPLOAD_FOLDER) / unique_name
    audio_file.save(str(temp_path))
    logger.info(f"Free Mode: saved audio to {temp_path}")

    try:
        result = gemini_service.transcribe_audio_free(temp_path)

        if result.get("error"):
            return jsonify({
                "success": False,
                "error": result["error"]
            }), 500

        # Keep the audio file for subsequent passes (Pass 2 & 3)
        # Store the path in session-like manner via response
        return jsonify({
            "success": True,
            "heard_text": result.get("heard_text", ""),
            "heard_transliteration": result.get("heard_transliteration", ""),
            "clarity": result.get("clarity", 0),
            "audio_token": unique_name  # client sends this back for pass 2 & 3
        }), 200

    except Exception as e:
        logger.error(f"Free Mode Pass 1 error: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/free/identify", methods=["POST"])
def free_identify():
    """
    FREE MODE Pass 2: Identify the shloka from transcribed text.
    Body JSON: { heard_text, audio_token }
    Returns: { source, standard_text, standard_transliteration, meaning, iks_analysis }
    """
    data = request.get_json(force=True, silent=True) or {}
    heard_text = data.get("heard_text", "")
    audio_token = data.get("audio_token", "")

    if not heard_text:
        return jsonify({"success": False, "error": "No heard_text provided"}), 400

    # Resolve audio path if token provided
    audio_path = None
    if audio_token:
        candidate = Path(Config.UPLOAD_FOLDER) / audio_token
        if candidate.exists():
            audio_path = candidate

    try:
        result = gemini_service.identify_shloka(heard_text, audio_path)

        return jsonify({
            "success": True,
            "source": result.get("source", "Unknown"),
            "standard_text": result.get("standard_text", heard_text),
            "standard_transliteration": result.get("standard_transliteration", ""),
            "meaning": result.get("meaning", ""),
            "iks_analysis": result.get("iks_analysis", {})
        }), 200

    except Exception as e:
        logger.error(f"Free Mode Pass 2 error: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/free/analyze", methods=["POST"])
def free_analyze():
    """
    FREE MODE Pass 3: Full phonetic analysis.
    Body JSON: { heard_text, intended_text, audio_token }
    Returns: full Shiksha analysis report
    """
    from services.free_mode_service import analyze_free_mode

    data = request.get_json(force=True, silent=True) or {}
    heard_text = data.get("heard_text", "")
    intended_text = data.get("intended_text", "")
    audio_token = data.get("audio_token", "")
    user_id = data.get("user_id", "student_demo")

    if not heard_text or not intended_text:
        return jsonify({"success": False, "error": "Both heard_text and intended_text are required"}), 400

    # Resolve audio path
    audio_path = None
    if audio_token:
        candidate = Path(Config.UPLOAD_FOLDER) / audio_token
        if candidate.exists():
            audio_path = candidate

    try:
        # Gemini re-check for subtle errors (Pass 3 AI component)
        recheck_segments = []
        if audio_path:
            recheck_segments = gemini_service.recheck_audio_detailed(
                audio_path, heard_text, intended_text
            )

        # Deterministic character-level diff + Shiksha analysis
        analysis = analyze_free_mode(heard_text, intended_text, recheck_segments)

        # Save attempt to DB with full diagnostics
        saved_attempt = db_service.save_attempt(
            user_id=user_id,
            item_id="free_mode",
            score=analysis["score"],
            errors=analysis["errors"],
            recognized_text=heard_text,
            target_text=intended_text,
            char_results=analysis.get("char_results", []),
            tip=analysis.get("tip", "")
        )

        # Clean up audio file
        if audio_path and audio_path.exists():
            try:
                os.remove(audio_path)
                # Also remove any converted wav
                wav_path = audio_path.with_suffix(".wav")
                if wav_path.exists():
                    os.remove(wav_path)
            except Exception:
                pass

        return jsonify({
            "success": True,
            "score": analysis["score"],
            "raw_accuracy": analysis["raw_accuracy"],
            "total_phonemes": analysis["total_phonemes"],
            "matched_phonemes": analysis["matched_phonemes"],
            "error_count": analysis["error_count"],
            "char_results": analysis["char_results"],
            "errors": analysis["errors"],
            "tip": analysis["tip"],
            "heard_text": heard_text,
            "intended_text": intended_text,
            "attempt_id": saved_attempt.get("_id")
        }), 200

    except Exception as e:
        logger.error(f"Free Mode Pass 3 error: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------------------
# Main Runner
# -------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 65)
    print("  VaaniAI - Sanskrit Pronunciation & Phonetic Correction System")
    print(f"  Running on: http://127.0.0.1:{Config.PORT}")
    print(f"  Demo Mode: {'ENABLED' if Config.DEMO_MODE else 'DISABLED'}")
    print(f"  Gemini Model: {Config.GEMINI_MODEL}")
    print("=" * 65)
    app.run(
        host="0.0.0.0",
        port=Config.PORT,
        debug=Config.DEBUG,
        use_reloader=False
    )

