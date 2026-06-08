from src.adapters.telegram.parsers.base import BaseSignalParser
from src.adapters.telegram.parsers.gold_parser import GoldSignalParser
from src.adapters.telegram.parsers.hit_tp_parser import HitTPParser

def get_parser(parser_type: str) -> BaseSignalParser:
    """
    Factory method untuk mendapatkan instance parser berdasarkan tipe string.
    Mendukung 'gold' dan 'price' untuk memetakan ke GoldSignalParser,
    serta 'hit_tp' untuk memetakan ke HitTPParser.
    """
    pt_lower = parser_type.lower()
    if pt_lower in ("gold", "price"):
        return GoldSignalParser()
    elif pt_lower == "hit_tp":
        return HitTPParser()
    
    raise ValueError(f"Tipe parser tidak dikenal: '{parser_type}'")
