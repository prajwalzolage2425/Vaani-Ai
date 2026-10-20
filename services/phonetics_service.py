"""
Phonetics Service for VaaniAI.
Implements the core Indian Knowledge Systems (IKS) logic grounded in Shiksha (Vedanga of phonetics).
Performs deterministic comparison between expected and produced sounds based on:
1. Sthāna (स्थान - Place of Articulation)
2. Mahāprāṇa / Alpaprāṇa (प्राण - Aspiration)
3. Ghoṣa / Aghoṣa (घोष - Voicing)
"""

from services.db_service import db_service

# Classical Paninian Sutras for Sthāna
SUTRAS = {
    "kanthya": "अकुहविसर्जनीयानां कण्ठः (Throat / Velum)",
    "talavya": "इचुयशानां तालु (Hard Palate)",
    "murdhanya": "ऋटुरषाणां मूर्धा (Roof of Palate / Retroflex)",
    "dantya": "ऌतुलसानां दन्ताः (Upper Teeth / Dental)",
    "oshthya": "उपूपध्मानीयानामोष्ठौ (Lips / Labial)",
    "kanthatālavya": "एदैतोः कण्ठतालु (Throat & Palate)",
    "kanthoṣṭhya": "ओदौतोः कण्ठोष्ठम् (Throat & Lips)",
    "dantoṣṭhya": "वकारस्य दन्तोष्ठम् (Teeth & Lips / Labiodental)",
    "nasikya": "ञमङणननां नासिका च (Nasal Resonator)"
}

STHANA_NAMES_DEVA = {
    "kanthya": "कण्ठ्य (Kaṇṭhya)",
    "talavya": "तालव्य (Tālavya)",
    "murdhanya": "मूर्धन्य (Mūrdhanya)",
    "dantya": "दन्त्य (Dantya)",
    "oshthya": "ओष्ठ्य (Oṣṭhya)",
    "kanthatālavya": "कण्ठतालव्य (Kaṇṭhatālavya)",
    "kanthoṣṭhya": "कण्ठोष्ठ्य (Kaṇṭhoṣṭhya)",
    "dantoṣṭhya": "दन्तोष्ठ्य (Dantoṣṭhya)",
    "nasikya": "नासिक्य (Nāsikya)"
}

class PhoneticsService:
    @staticmethod
    def compare_sounds(expected_char, heard_char):
        """
        Deterministically compares expected vs heard sound using Shiksha rules.
        Returns a detailed diagnostic dictionary.
        """
        # If identical
        if expected_char == heard_char:
            sound = db_service.get_sound(expected_char)
            sthana = sound.get("sthana", "") if sound else ""
            return {
                "expected_char": expected_char,
                "heard_char": heard_char,
                "is_match": True,
                "sthana_match": True,
                "prana_match": True,
                "ghosha_match": True,
                "expected_sthana": sthana,
                "heard_sthana": sthana,
                "expected_sthana_name": STHANA_NAMES_DEVA.get(sthana, sthana),
                "heard_sthana_name": STHANA_NAMES_DEVA.get(sthana, sthana),
                "expected_sutra": SUTRAS.get(sthana, ""),
                "shiksha_rule": sound.get("sutra", "") if sound else "",
                "difference_summary": "शुद्ध उच्चारणम् (Accurate Pāṇinian Articulation)",
                "corrective_tip": f"उत्तमम्! '{expected_char}' was pronounced accurately with proper Sthāna ({STHANA_NAMES_DEVA.get(sthana, sthana)})."
            }

        exp_sound = db_service.get_sound(expected_char)
        hrd_sound = db_service.get_sound(heard_char)

        # Fallback if character not in catalog (e.g. conjunct or diacritic)
        if not exp_sound:
            return {
                "expected_char": expected_char,
                "heard_char": heard_char,
                "is_match": False,
                "difference_summary": f"Detected '{heard_char}' instead of expected '{expected_char}'",
                "corrective_tip": f"Focus on enunciating the sound '{expected_char}' clearly."
            }

        exp_sthana = exp_sound.get("sthana", "unknown")
        hrd_sthana = hrd_sound.get("sthana", "unknown") if hrd_sound else "unknown"

        exp_mahaprana = exp_sound.get("mahaprana", False)
        hrd_mahaprana = hrd_sound.get("mahaprana", False) if hrd_sound else False

        exp_ghosha = exp_sound.get("ghosha", False)
        hrd_ghosha = hrd_sound.get("ghosha", False) if hrd_sound else False

        sthana_match = (exp_sthana == hrd_sthana)
        prana_match = (exp_mahaprana == hrd_mahaprana)
        ghosha_match = (exp_ghosha == hrd_ghosha)

        # Build Shiksha diagnostic breakdown
        diff_reasons = []
        tips = []

        # 1. Sthana Difference
        if not sthana_match:
            exp_deva = STHANA_NAMES_DEVA.get(exp_sthana, exp_sthana)
            hrd_deva = STHANA_NAMES_DEVA.get(hrd_sthana, hrd_sthana)
            diff_reasons.append(f"स्थान भेद (Sthāna Mismatch): Expected {exp_deva}, heard {hrd_deva}")
            
            # Classical anatomical remedy
            if exp_sthana == "dantya" and hrd_sthana == "murdhanya":
                tips.append(
                    f"You articulated at Mūrdhā (retroflex/hard dome) producing '{heard_char}'; "
                    f"however '{expected_char}' is Dantya (दन्त्य). Panini's rule: '{SUTRAS.get('dantya', '')}'. "
                    f"Touch the flat tip of your tongue against the back of your upper front teeth—do NOT curl backward."
                )
            elif exp_sthana == "murdhanya" and hrd_sthana == "dantya":
                tips.append(
                    f"You produced a dental (Dantya) sound '{heard_char}'; '{expected_char}' is Mūrdhanya (मूर्धन्य). "
                    f"Panini's rule: '{SUTRAS.get('murdhanya', '')}'. "
                    f"Curl the tip of your tongue upward and backward to tap the roof/dome of your palate."
                )
            elif exp_sthana == "talavya" and hrd_sthana == "dantya":
                tips.append(
                    f"You articulated at the teeth; '{expected_char}' is Tālavya (तालव्य). "
                    f"Panini's rule: '{SUTRAS.get('talavya', '')}'. "
                    f"Spread the middle blade of your tongue firmly against the hard palate."
                )
            elif exp_sthana == "talavya" and hrd_sthana == "murdhanya":
                tips.append(
                    f"You curled your tongue backwards like retroflex ष/ट; '{expected_char}' is Tālavya (तालव्य - श/च). "
                    f"Spread your tongue flat along the roof without curling the tip."
                )
            elif exp_sthana == "oshthya" and hrd_sthana != "oshthya":
                tips.append(
                    f"'{expected_char}' is Oṣṭhya (ओष्ठ्य - {SUTRAS.get('oshthya', '')}). "
                    f"Keep both upper and lower lips together; do not use teeth."
                )
            else:
                tips.append(
                    f"Sthāna divergence: Target '{expected_char}' resides at {exp_deva} ({SUTRAS.get(exp_sthana, '')}), "
                    f"whereas '{heard_char}' was articulated at {hrd_deva}."
                )

        # 2. Prana (Aspiration) Difference
        if not prana_match:
            if exp_mahaprana and not hrd_mahaprana:
                diff_reasons.append("प्राण भेद (Aspiration Deficit): Required महाप्राण (Mahāprāṇa), but heard अल्पप्राण (Alpaprāṇa)")
                tips.append(
                    f"'{expected_char}' is Mahāprāṇa (महाप्राण) requiring an explosive burst of breath. "
                    f"Release an audible, energetic puff of warm air as you pronounce it."
                )
            elif not exp_mahaprana and hrd_mahaprana:
                diff_reasons.append("प्राण भेद (Excess Aspiration): Required अल्पप्राण (Alpaprāṇa), but heard महाप्राण (Mahāprāṇa)")
                tips.append(
                    f"'{expected_char}' is Alpaprāṇa (अल्पप्राण). You exhaled too much air burst. "
                    f"Keep the breath gentle and clean without extra breath puff."
                )

        # 3. Ghosha (Voicing) Difference
        if not ghosha_match:
            if exp_ghosha and not hrd_ghosha:
                diff_reasons.append("घोष भेद (Voicing Deficit): Required घोष (Ghoṣa / Voiced), but heard अघोष (Aghoṣa / Voiceless)")
                tips.append(
                    f"'{expected_char}' is Ghoṣa (घोष). Make sure your vocal cords vibrate with tone from the throat."
                )
            elif not exp_ghosha and hrd_ghosha:
                diff_reasons.append("घोष भेद (Unintended Voicing): Required अघोष (Aghoṣa / Voiceless), but vocal cords vibrated")
                tips.append(
                    f"'{expected_char}' is Aghoṣa (अघोष). Keep the vocal cords relaxed and silent during articulation."
                )

        primary_tip = " ".join(tips) if tips else exp_sound.get("anatomical_tip", "Refine articulation based on Shiksha principles.")

        return {
            "expected_char": expected_char,
            "heard_char": heard_char,
            "is_match": False,
            "sthana_match": sthana_match,
            "prana_match": prana_match,
            "ghosha_match": ghosha_match,
            "expected_sthana": exp_sthana,
            "heard_sthana": hrd_sthana,
            "expected_sthana_name": STHANA_NAMES_DEVA.get(exp_sthana, exp_sthana),
            "heard_sthana_name": STHANA_NAMES_DEVA.get(hrd_sthana, hrd_sthana),
            "expected_sutra": SUTRAS.get(exp_sthana, ""),
            "heard_sutra": SUTRAS.get(hrd_sthana, "") if hrd_sthana in SUTRAS else "",
            "expected_meta": exp_sound,
            "heard_meta": hrd_sound,
            "difference_summary": " | ".join(diff_reasons) if diff_reasons else f"Substitution of '{heard_char}' for '{expected_char}'",
            "corrective_tip": primary_tip
        }

    @staticmethod
    def analyze_phonetic_differences(detected_segments, target_text=""):
        """
        Receives raw segment detections (e.g. from Gemini or Demo Engine)
        and runs each segment through the deterministic Pāṇinian Shiksha rules.
        """
        errors = []
        char_results = []
        total_evaluable = 0
        matches = 0

        for seg in detected_segments:
            exp_char = seg.get("expected_char", "")
            hrd_char = seg.get("heard_char", exp_char)
            
            # Skip whitespace or non-phonetic punctuation in scoring
            if not exp_char.strip() or exp_char in [" ", "vs", "।", "॥", ","]:
                char_results.append({
                    "char": exp_char,
                    "status": "neutral",
                    "feedback": None
                })
                continue

            total_evaluable += 1
            comparison = PhoneticsService.compare_sounds(exp_char, hrd_char)
            
            if comparison["is_match"]:
                matches += 1
                char_results.append({
                    "char": exp_char,
                    "heard": hrd_char,
                    "status": "correct",
                    "feedback": comparison
                })
            else:
                errors.append(comparison)
                char_results.append({
                    "char": exp_char,
                    "heard": hrd_char,
                    "status": "error",
                    "feedback": comparison
                })

        # Calculate score (out of 100)
        if total_evaluable > 0:
            score = int(round((matches / total_evaluable) * 100))
        else:
            score = 100

        # General corrective tip
        if score == 100:
            overall_tip = "उत्कृष्टम्! Your Sanskrit pronunciation strictly satisfies Pāṇinian Sthāna and Prayatna standards."
        elif errors:
            first_err = errors[0]
            overall_tip = f"Notice the {first_err.get('difference_summary', 'phonetic discrepancy')}. {first_err.get('corrective_tip', '')}"
        else:
            overall_tip = "Good attempt. Re-listen to the reference audio and practice the tongue placement."

        return {
            "score": score,
            "errors": errors,
            "char_results": char_results,
            "tip": overall_tip
        }
