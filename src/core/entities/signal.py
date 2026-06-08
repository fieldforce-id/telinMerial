from dataclasses import dataclass, field
from typing import List

@dataclass
class TradingSignal:
    """
    Entity domain yang mewakili Sinyal Trading.
    Sifatnya murni Python dan tidak tergantung pada library eksternal (Clean Architecture).
    """
    symbol: str
    action: str  # 'BUY' atau 'SELL'
    entry_min: float
    entry_max: float
    take_profits: List[float] = field(default_factory=list)
    stop_loss: float = 0.0
    source_group: str = ""

    def __post_init__(self):
        # Normalisasi action ke uppercase
        self.action = self.action.upper()
        if self.action not in ("BUY", "SELL"):
            raise ValueError(f"Action sinyal harus 'BUY' atau 'SELL', didapat: '{self.action}'")
        
        # Urutkan entry min dan max agar entry_min selalu yang terkecil
        if self.entry_min > self.entry_max:
            self.entry_min, self.entry_max = self.entry_max, self.entry_min


@dataclass
class SignalUpdate:
    """
    Entity domain yang mewakili update sinyal trading (seperti hit TP/SL).
    """
    symbol: str
    update_text: str  # e.g., 'DONE HIT TP1', 'HIT SL'
    source_group: str = ""

    def __post_init__(self):
        self.symbol = self.symbol.upper()
        self.update_text = self.update_text.upper()


@dataclass
class RawMessage:
    """
    Entity domain yang mewakili pesan mentah yang diteruskan apa adanya (tanpa parsing terstruktur).
    """
    text: str
    source_group: str = ""
