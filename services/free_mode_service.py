"""
Free Mode Analysis Service for VaaniAI.
Implements the 3-pass pipeline:
  Pass 1: Gemini transcribes raw audio → Devanagari
  Pass 2: Gemini identifies the shloka & suggests standard text
  Pass 3: Deterministic char-level diff + Gemini re-check + Shiksha analysis
"""

import difflib
import logging
import re
from services.phonetics_service import PhoneticsService
from services.scoring import ScoringService

logger = logging.getLogger("vaaniai.freemode")

# Characters to skip during phonetic comparison
SKIP_CHARS = set(" \t\n।॥॰·|,.;:!?'\"""''()[]{}/-–—0123456789०१२३४५६७८९")

# Vowel matras (diacritics) mapped to their full vowel equivalents
MATRA_TO_VOWEL = {
    "ा": "आ", "ि": "इ", "ी": "ई", "ु": "उ", "ू": "ऊ",
    "ृ": "ऋ", "ॄ": "ॠ", "े": "ए", "ै": "ऐ", "ो": "ओ", "ौ": "औ",
}

# Combining marks and modifiers to skip in alignment
COMBINING_MARKS = set("्ं ँ ः ॅ ॆ ॉ ॊ ़".split() + ["्"])


def extract_phonemes(text):
    """
    Extract meaningful phoneme units from Devanagari text.
    Returns list of (char, position_in_original) tuples.
    Each 'char' is a base consonant or vowel suitable for Shiksha lookup.
    """
    phonemes = []
    i = 0
    chars = list(text)
    
    while i < len(chars):
        c = chars[i]
        
        # Skip whitespace and punctuation
        if c in SKIP_CHARS:
            i += 1
            continue
        
        # Skip virama (halant) — it just suppresses inherent vowel
        if c == "्":
            i += 1
            continue
        
        # Skip anusvara/visarga/chandrabindu as separate entries
        # but they are meaningful — include them
        if c in ("ं", "ः", "ँ"):
            phonemes.append((c, i))
            i += 1
            continue
        
        # Vowel matras → map to base vowel for comparison
        if c in MATRA_TO_VOWEL:
            phonemes.append((MATRA_TO_VOWEL[c], i))
            i += 1
            continue
        
        # Nukta — skip (modifies previous consonant)
        if c == "़":
            i += 1
            continue
        
        # Regular Devanagari character (consonant or vowel)
        if '\u0900' <= c <= '\u097F' or c == 'ॐ':
            phonemes.append((c, i))
            i += 1
            continue
        
        # Anything else — skip
        i += 1
    
    return phonemes


def align_phonemes(heard_phonemes, intended_phonemes):
    """
    Align two sequences of phonemes using SequenceMatcher.
    Returns list of (heard_char_or_None, intended_char_or_None, status) tuples.
    status is 'match', 'substitution', 'insertion', or 'deletion'.
    """
    heard_chars = [p[0] for p in heard_phonemes]
    intended_chars = [p[0] for p in intended_phonemes]
    
    sm = difflib.SequenceMatcher(None, intended_chars, heard_chars)
    alignment = []
    
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            for k in range(i2 - i1):
                alignment.append({
                    "intended": intended_chars[i1 + k],
                    "heard": heard_chars[j1 + k],
                    "status": "match"
                })
        elif tag == 'replace':
            max_len = max(i2 - i1, j2 - j1)
            for k in range(max_len):
                ic = intended_chars[i1 + k] if (i1 + k) < i2 else None
                hc = heard_chars[j1 + k] if (j1 + k) < j2 else None
                alignment.append({
                    "intended": ic,
                    "heard": hc,
                    "status": "substitution"
                })
        elif tag == 'insert':
            for k in range(j2 - j1):
                alignment.append({
                    "intended": None,
                    "heard": heard_chars[j1 + k],
                    "status": "insertion"
                })
        elif tag == 'delete':
            for k in range(i2 - i1):
                alignment.append({
                    "intended": intended_chars[i1 + k],
                    "heard": None,
                    "status": "deletion"
                })
    
    return alignment


def analyze_free_mode(heard_text, intended_text, gemini_recheck_segments=None):
    """
    Full Pass 3 analysis:
    1. Extract phonemes from both texts
    2. Align them using sequence matching
    3. For each mismatch, run Shiksha comparison
    4. Compute composite score
    5. Return full report
    """
    heard_phonemes = extract_phonemes(heard_text)
    intended_phonemes = extract_phonemes(intended_text)
    
    alignment = align_phonemes(heard_phonemes, intended_phonemes)
    
    # Build char_results and errors arrays compatible with the practice page renderer
    char_results = []
    errors = []
    total_evaluable = 0
    matches = 0
    
    for entry in alignment:
        intended_c = entry["intended"]
        heard_c = entry["heard"]
        status = entry["status"]
        
        if status == "match" and intended_c:
            total_evaluable += 1
            matches += 1
            comparison = PhoneticsService.compare_sounds(intended_c, intended_c)
            char_results.append({
                "char": intended_c,
                "heard": heard_c,
                "status": "correct",
                "feedback": comparison
            })
        
        elif status == "substitution":
            if intended_c and heard_c:
                total_evaluable += 1
                comparison = PhoneticsService.compare_sounds(intended_c, heard_c)
                char_results.append({
                    "char": intended_c,
                    "heard": heard_c,
                    "status": "error",
                    "feedback": comparison
                })
                errors.append(comparison)
            elif intended_c and not heard_c:
                # Missing sound
                total_evaluable += 1
                char_results.append({
                    "char": intended_c,
                    "heard": "—",
                    "status": "error",
                    "feedback": {
                        "expected_char": intended_c,
                        "heard_char": "—",
                        "is_match": False,
                        "difference_summary": f"Missing sound: '{intended_c}' was not articulated",
                        "corrective_tip": f"The sound '{intended_c}' was expected but not detected in your pronunciation."
                    }
                })
                errors.append(char_results[-1]["feedback"])
            elif heard_c and not intended_c:
                # Extra sound
                char_results.append({
                    "char": f"+{heard_c}",
                    "heard": heard_c,
                    "status": "error",
                    "feedback": {
                        "expected_char": "—",
                        "heard_char": heard_c,
                        "is_match": False,
                        "difference_summary": f"Extra sound: '{heard_c}' was not expected",
                        "corrective_tip": f"An extra sound '{heard_c}' was detected that is not part of the intended text."
                    }
                })
        
        elif status == "insertion":
            if heard_c:
                char_results.append({
                    "char": f"+{heard_c}",
                    "heard": heard_c,
                    "status": "error",
                    "feedback": {
                        "expected_char": "—",
                        "heard_char": heard_c,
                        "is_match": False,
                        "difference_summary": f"Inserted sound: '{heard_c}'",
                        "corrective_tip": f"Extra sound '{heard_c}' was pronounced but not in the standard text."
                    }
                })
        
        elif status == "deletion":
            if intended_c:
                total_evaluable += 1
                char_results.append({
                    "char": intended_c,
                    "heard": "—",
                    "status": "error",
                    "feedback": {
                        "expected_char": intended_c,
                        "heard_char": "—",
                        "is_match": False,
                        "difference_summary": f"Omitted sound: '{intended_c}'",
                        "corrective_tip": f"The sound '{intended_c}' was omitted. Make sure to articulate every syllable."
                    }
                })
                errors.append(char_results[-1]["feedback"])
    
    # If gemini_recheck provided additional subtle errors, merge them
    if gemini_recheck_segments:
        for seg in gemini_recheck_segments:
            if not seg.get("is_match", True):
                exp = seg.get("expected_char", "")
                hrd = seg.get("heard_char", "")
                # Check if this error is already captured
                already_found = any(
                    e.get("expected_char") == exp and e.get("heard_char") == hrd
                    for e in errors
                )
                if not already_found and exp and hrd and exp != hrd:
                    comparison = PhoneticsService.compare_sounds(exp, hrd)
                    errors.append(comparison)
    
    # Score
    if total_evaluable > 0:
        raw_score = int(round((matches / total_evaluable) * 100))
    else:
        raw_score = 100
    
    # Composite score using Shiksha scoring
    composite_score = ScoringService.calculate_composite_score(char_results, raw_score)
    
    # Overall tip
    if composite_score >= 95:
        tip = "उत्कृष्टम्! Your pronunciation excellently matches the standard Pāṇinian articulation."
    elif errors:
        first_err = errors[0]
        tip = f"Primary deviation: {first_err.get('difference_summary', '')}. {first_err.get('corrective_tip', '')}"
    else:
        tip = "Good attempt. Practice the tongue placements as described in Pāṇinīya Śikṣā."
    
    return {
        "score": composite_score,
        "raw_accuracy": raw_score,
        "total_phonemes": total_evaluable,
        "matched_phonemes": matches,
        "error_count": len(errors),
        "char_results": char_results,
        "errors": errors,
        "tip": tip,
        "heard_text": heard_text,
        "intended_text": intended_text
    }
