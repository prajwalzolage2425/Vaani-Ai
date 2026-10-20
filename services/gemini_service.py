"""
Gemini AI Integration Service for VaaniAI.
Uses the official google-genai Python SDK to analyze Sanskrit/Hindi audio pronunciation.
Includes strict Shiksha system prompting, JSON parsing with retry,
graceful audio handling, and robust DEMO_MODE fallback for live exhibitions.
"""

import os
import json
import logging
import subprocess
import shutil
from pathlib import Path

from config import Config
from services.phonetics_service import PhoneticsService
from services.scoring import ScoringService

logger = logging.getLogger("vaaniai.gemini")

# System prompt enforcing strict Paninian Shiksha phonetics without auto-correction
SHIKSHA_SYSTEM_INSTRUCTION = """
You are a classical Sanskrit phonetician and teacher trained in Paninian Shiksha (पाणिनीय शिक्षा) and Pratisakhya.
Your task is to listen to the user's audio recording attempting to articulate a specific target Sanskrit or Hindi text.

CRITICAL INSTRUCTIONS:
1. DO NOT AUTO-CORRECT. Do NOT assume what the speaker "meant" to say.
2. Report the EXACT sounds you phonetically hear. If the target is dental 'त' (Dantya) but the speaker articulated retroflex 'ट' (Mūrdhanya), you MUST report 'ट'.
3. Distinguish carefully between:
   - Dental (त, थ, द, ध, न) vs Retroflex (ट, ठ, ड, ढ, ण)
   - Unaspirated Alpaprāṇa (क, ग, च, ज, ट, ड, त, द, प, ब) vs Aspirated Mahāprāṇa (ख, घ, छ, झ, ठ, ढ, थ, ध, फ, भ)
   - Voiceless Aghoṣa (क, ख, च, छ, ट, ठ, त, थ, प, फ) vs Voiced Ghoṣa (ग, घ, ज, झ, ड, ढ, द, ध, ब, भ)
   - Palatal sibilant 'श' vs Retroflex sibilant 'ष' vs Dental sibilant 'स'
   - Labial 'फ' (both lips) vs English labiodental 'f' (teeth + lip).

OUTPUT REQUIREMENT:
You must output ONLY a valid JSON object (no markdown, no backticks, no explanations outside JSON):
{
  "recognized_text": "<exact string of what was heard in Devanagari>",
  "recognized_transliteration": "<IAST transliteration of heard sounds>",
  "overall_clarity": <integer 0-100 indicating recording clarity>,
  "detected_segments": [
    {
      "expected_char": "<target Devanagari character>",
      "heard_char": "<phonetically heard Devanagari character>",
      "is_match": <true or false>,
      "confidence": <float 0.0-1.0>
    }
  ]
}
"""

def _build_demo_response(item_id, target_text, target_item):
    """
    Build a realistic demo response for a given item.
    For known items, returns curated phonetic analysis with deliberate errors.
    For unknown items, generates a generic correct match.
    """
    known_demos = {
        "pair_ta_ta": {
            "recognized_text": "ट vs ट",
            "recognized_transliteration": "ṭa vs ṭa",
            "overall_clarity": 94,
            "detected_segments": [
                {"expected_char": "त", "heard_char": "ट", "is_match": False, "confidence": 0.95},
                {"expected_char": "ट", "heard_char": "ट", "is_match": True, "confidence": 0.98}
            ]
        },
        "pair_da_da": {
            "recognized_text": "ड vs ड",
            "recognized_transliteration": "ḍa vs ḍa",
            "overall_clarity": 92,
            "detected_segments": [
                {"expected_char": "द", "heard_char": "ड", "is_match": False, "confidence": 0.93},
                {"expected_char": "ड", "heard_char": "ड", "is_match": True, "confidence": 0.96}
            ]
        },
        "pair_ga_gha": {
            "recognized_text": "घ vs घ",
            "recognized_transliteration": "gha vs gha",
            "overall_clarity": 90,
            "detected_segments": [
                {"expected_char": "ग", "heard_char": "घ", "is_match": False, "confidence": 0.91},
                {"expected_char": "घ", "heard_char": "घ", "is_match": True, "confidence": 0.95}
            ]
        },
        "pair_ka_kha": {
            "recognized_text": "ख vs ख",
            "recognized_transliteration": "kha vs kha",
            "overall_clarity": 93,
            "detected_segments": [
                {"expected_char": "क", "heard_char": "ख", "is_match": False, "confidence": 0.94},
                {"expected_char": "ख", "heard_char": "ख", "is_match": True, "confidence": 0.96}
            ]
        },
        "pair_pa_pha": {
            "recognized_text": "प vs फ",
            "recognized_transliteration": "pa vs pha",
            "overall_clarity": 88,
            "detected_segments": [
                {"expected_char": "प", "heard_char": "प", "is_match": True, "confidence": 0.97},
                {"expected_char": "फ", "heard_char": "फ", "is_match": True, "confidence": 0.92}
            ]
        },
        "pair_sha_sha_sa": {
            "recognized_text": "स vs ष vs स",
            "recognized_transliteration": "sa vs ṣa vs sa",
            "overall_clarity": 91,
            "detected_segments": [
                {"expected_char": "श", "heard_char": "स", "is_match": False, "confidence": 0.92},
                {"expected_char": "ष", "heard_char": "ष", "is_match": True, "confidence": 0.94},
                {"expected_char": "स", "heard_char": "स", "is_match": True, "confidence": 0.98}
            ]
        },
        "word_ganesha": {
            "recognized_text": "गनेश",
            "recognized_transliteration": "ganeśa",
            "overall_clarity": 95,
            "detected_segments": [
                {"expected_char": "ग", "heard_char": "ग", "is_match": True, "confidence": 0.98},
                {"expected_char": "ण", "heard_char": "न", "is_match": False, "confidence": 0.91},
                {"expected_char": "श", "heard_char": "श", "is_match": True, "confidence": 0.97}
            ]
        },
        "word_vidya": {
            "recognized_text": "विद्या",
            "recognized_transliteration": "vidyā",
            "overall_clarity": 96,
            "detected_segments": [
                {"expected_char": "व", "heard_char": "व", "is_match": True, "confidence": 0.97},
                {"expected_char": "द", "heard_char": "द", "is_match": True, "confidence": 0.96},
                {"expected_char": "य", "heard_char": "य", "is_match": True, "confidence": 0.95}
            ]
        },
        "word_sanskrit": {
            "recognized_text": "संस्कृत",
            "recognized_transliteration": "saṃskṛta",
            "overall_clarity": 94,
            "detected_segments": [
                {"expected_char": "स", "heard_char": "स", "is_match": True, "confidence": 0.96},
                {"expected_char": "क", "heard_char": "क", "is_match": True, "confidence": 0.97},
                {"expected_char": "ऋ", "heard_char": "ऋ", "is_match": True, "confidence": 0.93},
                {"expected_char": "त", "heard_char": "त", "is_match": True, "confidence": 0.98}
            ]
        },
        "word_dharma": {
            "recognized_text": "धर्म",
            "recognized_transliteration": "dharma",
            "overall_clarity": 96,
            "detected_segments": [
                {"expected_char": "ध", "heard_char": "ध", "is_match": True, "confidence": 0.95},
                {"expected_char": "र", "heard_char": "र", "is_match": True, "confidence": 0.97},
                {"expected_char": "म", "heard_char": "म", "is_match": True, "confidence": 0.99}
            ]
        },
        "word_shanti": {
            "recognized_text": "शान्ति",
            "recognized_transliteration": "śānti",
            "overall_clarity": 97,
            "detected_segments": [
                {"expected_char": "श", "heard_char": "श", "is_match": True, "confidence": 0.96},
                {"expected_char": "न", "heard_char": "न", "is_match": True, "confidence": 0.98},
                {"expected_char": "त", "heard_char": "त", "is_match": True, "confidence": 0.98}
            ]
        },
        "word_guru": {
            "recognized_text": "गुरु",
            "recognized_transliteration": "guru",
            "overall_clarity": 97,
            "detected_segments": [
                {"expected_char": "ग", "heard_char": "ग", "is_match": True, "confidence": 0.97},
                {"expected_char": "र", "heard_char": "र", "is_match": True, "confidence": 0.96}
            ]
        },
        "word_yoga": {
            "recognized_text": "योग",
            "recognized_transliteration": "yoga",
            "overall_clarity": 96,
            "detected_segments": [
                {"expected_char": "य", "heard_char": "य", "is_match": True, "confidence": 0.97},
                {"expected_char": "ग", "heard_char": "ग", "is_match": True, "confidence": 0.96}
            ]
        },
        "word_mantra": {
            "recognized_text": "मंत्र",
            "recognized_transliteration": "mantra",
            "overall_clarity": 95,
            "detected_segments": [
                {"expected_char": "म", "heard_char": "म", "is_match": True, "confidence": 0.98},
                {"expected_char": "न", "heard_char": "न", "is_match": True, "confidence": 0.95},
                {"expected_char": "त", "heard_char": "त", "is_match": True, "confidence": 0.97},
                {"expected_char": "र", "heard_char": "र", "is_match": True, "confidence": 0.96}
            ]
        },
        "shloka_ganeshaya_namah": {
            "recognized_text": "श्री गणेशाय नमः",
            "recognized_transliteration": "śrī gaṇeśāya namaḥ",
            "overall_clarity": 96,
            "detected_segments": [
                {"expected_char": "श", "heard_char": "श", "is_match": True, "confidence": 0.97},
                {"expected_char": "र", "heard_char": "र", "is_match": True, "confidence": 0.98},
                {"expected_char": "ग", "heard_char": "ग", "is_match": True, "confidence": 0.98},
                {"expected_char": "ण", "heard_char": "ण", "is_match": True, "confidence": 0.94},
                {"expected_char": "श", "heard_char": "श", "is_match": True, "confidence": 0.98},
                {"expected_char": "य", "heard_char": "य", "is_match": True, "confidence": 0.96},
                {"expected_char": "न", "heard_char": "न", "is_match": True, "confidence": 0.99},
                {"expected_char": "म", "heard_char": "म", "is_match": True, "confidence": 0.99},
                {"expected_char": "ह", "heard_char": "ह", "is_match": True, "confidence": 0.93}
            ]
        },
        "shloka_saha_navavatu": {
            "recognized_text": "ॐ सह नाववतु",
            "recognized_transliteration": "om saha nāvavatu",
            "overall_clarity": 95,
            "detected_segments": [
                {"expected_char": "स", "heard_char": "स", "is_match": True, "confidence": 0.98},
                {"expected_char": "ह", "heard_char": "ह", "is_match": True, "confidence": 0.96},
                {"expected_char": "न", "heard_char": "न", "is_match": True, "confidence": 0.97},
                {"expected_char": "व", "heard_char": "व", "is_match": True, "confidence": 0.95},
                {"expected_char": "त", "heard_char": "त", "is_match": True, "confidence": 0.96}
            ]
        },
        "shloka_satyameva_jayate": {
            "recognized_text": "सत्यमेव जयते",
            "recognized_transliteration": "satyameva jayate",
            "overall_clarity": 96,
            "detected_segments": [
                {"expected_char": "स", "heard_char": "स", "is_match": True, "confidence": 0.97},
                {"expected_char": "त", "heard_char": "त", "is_match": True, "confidence": 0.96},
                {"expected_char": "य", "heard_char": "य", "is_match": True, "confidence": 0.96},
                {"expected_char": "म", "heard_char": "म", "is_match": True, "confidence": 0.98},
                {"expected_char": "व", "heard_char": "व", "is_match": True, "confidence": 0.95},
                {"expected_char": "ज", "heard_char": "ज", "is_match": True, "confidence": 0.97}
            ]
        },
        "shloka_gayatri": {
            "recognized_text": "ॐ भूर्भुवः स्वः",
            "recognized_transliteration": "oṃ bhūr bhuvaḥ svaḥ",
            "overall_clarity": 93,
            "detected_segments": [
                {"expected_char": "भ", "heard_char": "ब", "is_match": False, "confidence": 0.88},
                {"expected_char": "र", "heard_char": "र", "is_match": True, "confidence": 0.96},
                {"expected_char": "व", "heard_char": "व", "is_match": True, "confidence": 0.95},
                {"expected_char": "स", "heard_char": "स", "is_match": True, "confidence": 0.97}
            ]
        },
        "shloka_asato_ma": {
            "recognized_text": "असतो मा सद्गमय",
            "recognized_transliteration": "asato mā sadgamaya",
            "overall_clarity": 94,
            "detected_segments": [
                {"expected_char": "स", "heard_char": "स", "is_match": True, "confidence": 0.96},
                {"expected_char": "त", "heard_char": "त", "is_match": True, "confidence": 0.95},
                {"expected_char": "म", "heard_char": "म", "is_match": True, "confidence": 0.98},
                {"expected_char": "द", "heard_char": "द", "is_match": True, "confidence": 0.94},
                {"expected_char": "ग", "heard_char": "ग", "is_match": True, "confidence": 0.96},
                {"expected_char": "य", "heard_char": "य", "is_match": True, "confidence": 0.97}
            ]
        },
        "shloka_tamaso_ma": {
            "recognized_text": "तमसो मा ज्योतिर्गमय",
            "recognized_transliteration": "tamaso mā jyotirgamaya",
            "overall_clarity": 92,
            "detected_segments": [
                {"expected_char": "त", "heard_char": "त", "is_match": True, "confidence": 0.95},
                {"expected_char": "म", "heard_char": "म", "is_match": True, "confidence": 0.97},
                {"expected_char": "स", "heard_char": "स", "is_match": True, "confidence": 0.96},
                {"expected_char": "ज", "heard_char": "ज", "is_match": True, "confidence": 0.94},
                {"expected_char": "य", "heard_char": "य", "is_match": True, "confidence": 0.93},
                {"expected_char": "र", "heard_char": "र", "is_match": True, "confidence": 0.95},
                {"expected_char": "ग", "heard_char": "ग", "is_match": True, "confidence": 0.96}
            ]
        },
        "shloka_vakratunda": {
            "recognized_text": "वक्रतुण्ड महाकाय",
            "recognized_transliteration": "vakratuṇḍa mahākāya",
            "overall_clarity": 93,
            "detected_segments": [
                {"expected_char": "व", "heard_char": "व", "is_match": True, "confidence": 0.96},
                {"expected_char": "क", "heard_char": "क", "is_match": True, "confidence": 0.97},
                {"expected_char": "र", "heard_char": "र", "is_match": True, "confidence": 0.95},
                {"expected_char": "त", "heard_char": "त", "is_match": True, "confidence": 0.96},
                {"expected_char": "ण", "heard_char": "न", "is_match": False, "confidence": 0.89},
                {"expected_char": "ड", "heard_char": "ड", "is_match": True, "confidence": 0.94},
                {"expected_char": "म", "heard_char": "म", "is_match": True, "confidence": 0.98},
                {"expected_char": "ह", "heard_char": "ह", "is_match": True, "confidence": 0.95}
            ]
        },
        "shloka_om_namah_shivaya": {
            "recognized_text": "ॐ नमः शिवाय",
            "recognized_transliteration": "oṃ namaḥ śivāya",
            "overall_clarity": 97,
            "detected_segments": [
                {"expected_char": "न", "heard_char": "न", "is_match": True, "confidence": 0.98},
                {"expected_char": "म", "heard_char": "म", "is_match": True, "confidence": 0.99},
                {"expected_char": "श", "heard_char": "श", "is_match": True, "confidence": 0.97},
                {"expected_char": "व", "heard_char": "व", "is_match": True, "confidence": 0.96},
                {"expected_char": "य", "heard_char": "य", "is_match": True, "confidence": 0.97}
            ]
        },
        "shloka_vidya_dadati": {
            "recognized_text": "विद्या ददाति विनयं",
            "recognized_transliteration": "vidyā dadāti vinayaṃ",
            "overall_clarity": 95,
            "detected_segments": [
                {"expected_char": "व", "heard_char": "व", "is_match": True, "confidence": 0.97},
                {"expected_char": "द", "heard_char": "द", "is_match": True, "confidence": 0.96},
                {"expected_char": "य", "heard_char": "य", "is_match": True, "confidence": 0.95},
                {"expected_char": "त", "heard_char": "त", "is_match": True, "confidence": 0.97},
                {"expected_char": "न", "heard_char": "न", "is_match": True, "confidence": 0.98}
            ]
        }
    }
    
    demo_data = known_demos.get(item_id)
    if not demo_data:
        # Generate generic segment match for unknown items
        focus_sounds = target_item.get("focus_sounds", []) if target_item else []
        if not focus_sounds:
            clean_chars = [c for c in target_text if c.strip() and c not in ["v", "s", " ", "।", "॥"]]
            focus_sounds = clean_chars[:8]
        
        segments = [{"expected_char": c, "heard_char": c, "is_match": True, "confidence": 0.95} for c in focus_sounds]
        demo_data = {
            "recognized_text": target_text,
            "recognized_transliteration": target_item.get("transliteration", "") if target_item else "",
            "overall_clarity": 95,
            "detected_segments": segments
        }
    
    return demo_data


class GeminiService:
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        self.model_name = Config.GEMINI_MODEL
        self.client = None
        
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info(f"Initialized Google GenAI client with model: {self.model_name}")
            except Exception as e:
                logger.warning(f"Could not initialize GenAI client: {e}")

    def _convert_audio_if_needed(self, audio_path):
        """
        Attempts to convert audio using ffmpeg if available.
        Returns the path to the best audio file and detected mime type.
        """
        mime_type = "audio/webm"
        ext = audio_path.suffix.lower()
        if ext == ".wav":
            mime_type = "audio/wav"
        elif ext == ".mp3":
            mime_type = "audio/mp3"
        elif ext == ".ogg":
            mime_type = "audio/ogg"

        ffmpeg_bin = shutil.which("ffmpeg")
        if not ffmpeg_bin:
            return audio_path, mime_type

        # If ffmpeg is present, convert to wav for better compatibility
        try:
            wav_path = audio_path.with_suffix(".wav")
            if not wav_path.exists():
                cmd = [
                    ffmpeg_bin, "-y", "-i", str(audio_path),
                    "-ar", "16000", "-ac", "1", str(wav_path)
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
            if wav_path.exists() and wav_path.stat().st_size > 0:
                return wav_path, "audio/wav"
        except Exception as e:
            logger.warning(f"FFmpeg conversion skipped/failed: {e}")

        return audio_path, mime_type

    def _clean_json_response(self, text):
        """Strips markdown code fences and cleans text for JSON parsing."""
        if not text:
            return ""
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()

    def analyze_audio(self, audio_path, target_item, is_demo_requested=False):
        """
        Main pipeline:
        1. Checks DEMO_MODE or absence of Gemini key -> returns pre-defined response.
        2. Otherwise, calls Gemini API via google-genai SDK.
        3. Parses JSON safely (retry once on invalid JSON).
        4. Runs detected segments through deterministic Pāṇinian Shiksha comparator.
        """
        item_id = target_item.get("_id", "") if target_item else ""
        target_text = target_item.get("text", "") if target_item else ""

        # Check if Demo Mode is active, or Gemini client is unconfigured
        use_demo = Config.DEMO_MODE or is_demo_requested or not self.client or not self.api_key

        if use_demo:
            logger.info(f"Using DEMO_MODE response for item: {item_id}")
            return self._process_demo(item_id, target_text, target_item)

        # Real Gemini Call — need audio file
        if not audio_path or not Path(audio_path).exists():
            logger.warning("No audio file provided for real analysis. Falling back to demo mode.")
            return self._process_demo(item_id, target_text, target_item)
        
        try:
            processed_path, mime_type = self._convert_audio_if_needed(audio_path)
            with open(processed_path, "rb") as f:
                audio_bytes = f.read()
            
            if len(audio_bytes) < 100:
                logger.warning(f"Audio file too small ({len(audio_bytes)} bytes). Falling back to demo.")
                return self._process_demo(item_id, target_text, target_item)
                
            from google.genai import types

            prompt_text = (
                f"The target text is: '{target_text}'. "
                f"Transliteration: '{target_item.get('transliteration', '')}'. "
                f"Please listen to the attached audio and produce JSON analysis."
            )

            audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)

            parsed_json = None
            for attempt in range(2):
                try:
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=[audio_part, prompt_text],
                        config=types.GenerateContentConfig(
                            system_instruction=SHIKSHA_SYSTEM_INSTRUCTION,
                            temperature=0.1,
                            response_mime_type="application/json"
                        )
                    )
                    
                    raw_text = response.text or ""
                    cleaned = self._clean_json_response(raw_text)
                    parsed_json = json.loads(cleaned)
                    logger.info(f"Gemini returned valid JSON on attempt {attempt + 1}")
                    break
                except json.JSONDecodeError as e:
                    logger.warning(f"Gemini JSON parse error on attempt {attempt + 1}: {e}")
                    if attempt == 1:
                        logger.error("Gemini JSON parse failed after retry. Falling back to Demo Mode.")
                        return self._process_demo(item_id, target_text, target_item)
                except Exception as e:
                    logger.warning(f"Gemini API attempt {attempt + 1} error: {e}")
                    if attempt == 1:
                        logger.error("Gemini failed after retry. Falling back to Demo Mode result.")
                        return self._process_demo(item_id, target_text, target_item)

            if not parsed_json or "detected_segments" not in parsed_json:
                logger.warning("Empty or malformed JSON from Gemini. Falling back to demo data.")
                return self._process_demo(item_id, target_text, target_item)

            # Deterministic Pāṇinian Shiksha comparison
            phonetics_result = PhoneticsService.analyze_phonetic_differences(
                parsed_json.get("detected_segments", []), target_text
            )

            composite_score = ScoringService.calculate_composite_score(
                phonetics_result["char_results"], parsed_json.get("overall_clarity", 90)
            )

            return {
                "score": composite_score,
                "overall_clarity": parsed_json.get("overall_clarity", 90),
                "recognized_text": parsed_json.get("recognized_text", target_text),
                "recognized_transliteration": parsed_json.get("recognized_transliteration", ""),
                "tip": phonetics_result["tip"],
                "errors": phonetics_result["errors"],
                "char_results": phonetics_result["char_results"],
                "demo_mode": False
            }
            
        except Exception as e:
            logger.error(f"Unexpected error during Gemini analysis: {e}", exc_info=True)
            return self._process_demo(item_id, target_text, target_item)

    def _process_demo(self, item_id, target_text, target_item):
        """Process a demo response through the Shiksha pipeline."""
        demo_data = _build_demo_response(item_id, target_text, target_item)
        
        phonetics_result = PhoneticsService.analyze_phonetic_differences(
            demo_data["detected_segments"], target_text
        )
        
        composite_score = ScoringService.calculate_composite_score(
            phonetics_result["char_results"], demo_data.get("overall_clarity", 92)
        )
        
        return {
            "score": composite_score,
            "overall_clarity": demo_data.get("overall_clarity", 95),
            "recognized_text": demo_data.get("recognized_text", target_text),
            "recognized_transliteration": demo_data.get("recognized_transliteration", ""),
            "tip": phonetics_result["tip"],
            "errors": phonetics_result["errors"],
            "char_results": phonetics_result["char_results"],
            "demo_mode": True
        }

    # ===================================================================
    # FREE MODE — 3-Pass Pipeline Methods
    # ===================================================================

    def transcribe_audio_free(self, audio_path):
        """
        FREE MODE Pass 1: Raw transcription of audio to Devanagari.
        No target text — just transcribe exactly what was spoken.
        Returns: { heard_text, heard_transliteration, clarity }
        """
        if not self.client or not self.api_key:
            return {
                "heard_text": "",
                "heard_transliteration": "",
                "clarity": 0,
                "error": "Gemini API not configured. Please set GEMINI_API_KEY in .env"
            }

        if not audio_path or not Path(audio_path).exists():
            return {
                "heard_text": "",
                "heard_transliteration": "",
                "clarity": 0,
                "error": "No audio file provided"
            }

        processed_path, mime_type = self._convert_audio_if_needed(audio_path)
        with open(processed_path, "rb") as f:
            audio_bytes = f.read()

        if len(audio_bytes) < 100:
            return {
                "heard_text": "",
                "heard_transliteration": "",
                "clarity": 0,
                "error": "Audio recording too short"
            }

        from google.genai import types

        transcribe_prompt = """Listen to this audio recording of someone speaking Sanskrit, Hindi, or a Vedic mantra/shloka.

CRITICAL: Transcribe EXACTLY what you phonetically hear in Devanagari script. Do NOT auto-correct or guess what they meant to say.
If you hear retroflex ट instead of dental त, write ट. If you hear unaspirated क instead of aspirated ख, write क.

Output ONLY valid JSON:
{
  "heard_text": "<exact Devanagari transcription of what was spoken>",
  "heard_transliteration": "<IAST transliteration>",
  "clarity": <integer 0-100 rating of audio recording quality>
}"""

        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)

        for attempt in range(2):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=[audio_part, transcribe_prompt],
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        response_mime_type="application/json"
                    )
                )
                raw = self._clean_json_response(response.text or "")
                result = json.loads(raw)
                logger.info(f"Free Mode Pass 1 transcription: {result.get('heard_text', '')}")
                return result
            except Exception as e:
                logger.warning(f"Free Mode Pass 1 attempt {attempt+1} error: {e}")
                if attempt == 1:
                    return {
                        "heard_text": "",
                        "heard_transliteration": "",
                        "clarity": 0,
                        "error": f"Transcription failed: {str(e)}"
                    }

        return {"heard_text": "", "heard_transliteration": "", "clarity": 0, "error": "Unknown error"}

    def identify_shloka(self, heard_text, audio_path=None):
        """
        FREE MODE Pass 2: Identify the shloka/mantra from transcribed text.
        Returns: { source, standard_text, standard_transliteration, meaning, iks_analysis }
        """
        if not self.client or not self.api_key:
            return {
                "source": "Unknown",
                "standard_text": heard_text,
                "standard_transliteration": "",
                "meaning": "",
                "iks_analysis": {},
                "error": "Gemini API not configured"
            }

        from google.genai import types

        identify_prompt = f"""A Sanskrit/Hindi learner spoke a mantra or shloka. The phonetic transcription is:
"{heard_text}"

Your task:
1. Identify which shloka, mantra, or verse this is (e.g., "Bhagavad Gita 2.47", "Gayatri Mantra", "Ishavasya Upanishad 1", etc.)
2. Provide the STANDARD (correct, canonical) text in Devanagari
3. Provide IAST transliteration
4. Provide meaning in English
5. Provide IKS (Indian Knowledge System) analysis of this shloka

If you cannot identify the exact source, write "Source not identified" and still provide the closest standard text you can infer.

Output ONLY valid JSON:
{{
  "source": "<scripture name, chapter, verse number or 'Source not identified'>",
  "standard_text": "<correct canonical Devanagari text>",
  "standard_transliteration": "<IAST transliteration of the standard text>",
  "meaning": "<English translation/meaning of the shloka>",
  "iks_analysis": {{
    "vedanga_context": "<which Vedanga or tradition this belongs to>",
    "chandas": "<meter/chandas if applicable, else 'Prose' or 'Free verse'>",
    "key_phonetic_features": "<notable Sthāna or Prayatna requirements in this verse>",
    "spiritual_significance": "<brief spiritual/philosophical significance>"
  }}
}}"""

        contents = [identify_prompt]
        if audio_path and Path(audio_path).exists():
            try:
                with open(audio_path, "rb") as f:
                    audio_bytes = f.read()
                _, mime_type = self._convert_audio_if_needed(audio_path)
                audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
                contents = [audio_part, identify_prompt]
            except Exception:
                pass

        for attempt in range(2):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        response_mime_type="application/json"
                    )
                )
                raw = self._clean_json_response(response.text or "")
                result = json.loads(raw)
                logger.info(f"Free Mode Pass 2 identified: {result.get('source', 'unknown')}")
                return result
            except Exception as e:
                logger.warning(f"Free Mode Pass 2 attempt {attempt+1} error: {e}")
                if attempt == 1:
                    return {
                        "source": "Identification failed",
                        "standard_text": heard_text,
                        "standard_transliteration": "",
                        "meaning": "",
                        "iks_analysis": {},
                        "error": str(e)
                    }

        return {"source": "Unknown", "standard_text": heard_text, "standard_transliteration": "", "meaning": "", "iks_analysis": {}}

    def recheck_audio_detailed(self, audio_path, heard_text, intended_text):
        """
        FREE MODE Pass 3 (Gemini part): Re-listen to audio comparing heard vs intended.
        Catches subtle errors the deterministic diff might miss.
        Returns: list of detected_segments with fine-grained phonetic differences.
        """
        if not self.client or not self.api_key or not audio_path or not Path(audio_path).exists():
            return []

        try:
            processed_path, mime_type = self._convert_audio_if_needed(audio_path)
            with open(processed_path, "rb") as f:
                audio_bytes = f.read()

            if len(audio_bytes) < 100:
                return []

            from google.genai import types

            recheck_prompt = f"""You previously transcribed this audio as: "{heard_text}"
The intended/standard text is: "{intended_text}"

Now re-listen VERY carefully to the audio. For each consonant and vowel in the intended text, compare what was actually articulated vs what should have been.

Focus on subtle distinctions:
- Dental vs Retroflex (त/ट, द/ड, न/ण, स/ष)
- Aspirated vs Unaspirated (क/ख, ग/घ, च/छ, ज/झ, ट/ठ, ड/ढ, त/थ, द/ध, प/फ, ब/भ)
- Voiced vs Voiceless
- Palatal श vs Retroflex ष vs Dental स
- Anusvara ं, Visarga ः, Chandrabindu ँ

Output ONLY valid JSON:
{{
  "recheck_segments": [
    {{
      "expected_char": "<intended character>",
      "heard_char": "<what was actually articulated>",
      "is_match": <true/false>,
      "confidence": <0.0-1.0>,
      "note": "<brief note on the phonetic difference if any>"
    }}
  ]
}}"""

            audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[audio_part, recheck_prompt],
                config=types.GenerateContentConfig(
                    system_instruction=SHIKSHA_SYSTEM_INSTRUCTION,
                    temperature=0.1,
                    response_mime_type="application/json"
                )
            )
            raw = self._clean_json_response(response.text or "")
            result = json.loads(raw)
            segments = result.get("recheck_segments", [])
            logger.info(f"Free Mode Pass 3 recheck found {len(segments)} segments")
            return segments

        except Exception as e:
            logger.warning(f"Free Mode Pass 3 recheck error: {e}")
            return []


# Singleton instance
gemini_service = GeminiService()
