"""
Scoring and evaluation service for VaaniAI.
Calculates weighted composite scores based on Sthāna and Prayatna fidelity.
"""

class ScoringService:
    @staticmethod
    def calculate_composite_score(char_results, raw_clarity=90):
        """
        Calculates a composite Shiksha Score (0-100) combining:
        - Sthāna precision (50% weight)
        - Prayatna (Aspiration + Voicing) precision (30% weight)
        - Articulatory Clarity (20% weight)
        """
        evaluable = [c for c in char_results if c.get("status") in ("correct", "error")]
        if not evaluable:
            return 100

        total_sounds = len(evaluable)
        sthana_hits = 0
        prana_hits = 0
        ghosha_hits = 0

        for item in evaluable:
            fb = item.get("feedback")
            if not fb:
                continue
            if fb.get("sthana_match", False):
                sthana_hits += 1
            if fb.get("prana_match", False):
                prana_hits += 1
            if fb.get("ghosha_match", False):
                ghosha_hits += 1

        sthana_score = (sthana_hits / total_sounds) * 100
        prayatna_score = ((prana_hits + ghosha_hits) / (2 * total_sounds)) * 100
        
        # Weighted composite: 50% Sthāna, 30% Prayatna, 20% overall clarity
        composite = (sthana_score * 0.50) + (prayatna_score * 0.30) + (raw_clarity * 0.20)
        return int(round(max(0, min(100, composite))))
