import re
from typing import Optional
from src.core.entities.signal import TradingSignal
from src.adapters.telegram.parsers.base import BaseSignalParser

class GoldSignalParser(BaseSignalParser):
    """
    Parser khusus untuk membaca sinyal trading pasangan GOLD (XAUUSD).
    Mendukung format BUY/SELL dengan TP berjenjang dan Stop Loss.
    """
    
    def parse(self, text: str) -> Optional[TradingSignal]:
        # 1. Normalisasi teks (menghapus spasi berlebih di awal/akhir)
        text_clean = text.strip()
        
        # 2. Cek apakah ada kata "PRICE:" (Filter awal wajib)
        if "PRICE:" not in text_clean.upper():
            return None

        # 3. Ekstrak Action (BUY / SELL)
        # Mendukung: "GOLD BUY NOW", "GOLD SELL NOW", dsb.
        action_match = re.search(r'GOLD\s+(BUY|SELL)\s+NOW', text_clean, re.IGNORECASE)
        if not action_match:
            return None
        action = action_match.group(1).upper()

        # 4. Ekstrak Entry Prices (Range Min - Max)
        # Pola: "PRICE: 4500 - 4497" atau "PRICE: 4500-4497"
        entry_match = re.search(r'PRICE:\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)', text_clean, re.IGNORECASE)
        if not entry_match:
            return None
        entry_min = float(entry_match.group(1))
        entry_max = float(entry_match.group(2))

        # 5. Ekstrak Take Profits (TP1, TP2, dst.)
        # Pola: "TP1 🎖: 4504" atau "TP2: 4510"
        tp_matches = re.findall(r'TP\d+.*?:\s*(\d+(?:\.\d+)?)', text_clean, re.IGNORECASE)
        take_profits = [float(tp) for tp in tp_matches]
        if not take_profits:
            return None

        # 6. Ekstrak Stop Loss (SL)
        # Pola: "SL: 4492‼️" atau "SL : 4492"
        sl_match = re.search(r'SL\s*.*?:\s*(\d+(?:\.\d+)?)', text_clean, re.IGNORECASE)
        if not sl_match:
            return None
        stop_loss = float(sl_match.group(1))

        # 7. Kembalikan objek TradingSignal
        return TradingSignal(
            symbol="GOLD",
            action=action,
            entry_min=entry_min,
            entry_max=entry_max,
            take_profits=take_profits,
            stop_loss=stop_loss
        )
