from abc import ABC, abstractmethod
from typing import Optional, Union, Any
from src.core.entities.signal import TradingSignal, SignalUpdate

class BaseSignalParser(ABC):
    """
    Abstract Base Class untuk mendefinisikan interface parser sinyal trading.
    Semua parser spesifik grup harus mengimplementasikan kelas ini.
    """
    
    @abstractmethod
    def parse(self, text: str) -> Optional[Union[TradingSignal, SignalUpdate]]:
        """
        Memparse teks mentah dari grup telegram menjadi domain entity TradingSignal atau SignalUpdate.
        Mengembalikan None jika pesan tidak cocok dengan pola parser.
        """
        pass
