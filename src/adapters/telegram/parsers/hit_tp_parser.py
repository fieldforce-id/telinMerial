import re
from typing import Optional
from src.core.entities.signal import SignalUpdate
from src.adapters.telegram.parsers.base import BaseSignalParser

class HitTPParser(BaseSignalParser):
    """
    Parser untuk mendeteksi update sinyal (hit TP / SL).
    Contoh format: "GOLD DONE HIT TP1", "XAUUSD HIT TP2", "GOLD HIT SL"
    """

    def parse(self, text: str) -> Optional[SignalUpdate]:
        text_clean = text.strip()

        # Pola pencarian regex:
        # Group 1: Nama pair/simbol (e.g. GOLD, XAUUSD, dll.)
        # Group 2: Aksi hit (e.g. DONE HIT TP1, HIT TP2, HIT SL, dll.)
        pattern = r'(\w+)\s+((?:DONE\s+)?HIT\s+TP\d+|(?:DONE\s+)?HIT\s+SL)'
        match = re.search(pattern, text_clean, re.IGNORECASE)
        if not match:
            return None

        symbol = match.group(1)
        update_text = match.group(2)

        return SignalUpdate(
            symbol=symbol,
            update_text=update_text
        )
