import unittest
import sys
import os

# Tambahkan project root ke sys.path agar src bisa di-import
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from src.adapters.telegram.parsers.gold_parser import GoldSignalParser
from src.adapters.telegram.parsers.hit_tp_parser import HitTPParser
from src.core.entities.signal import TradingSignal, SignalUpdate

class TestGoldSignalParser(unittest.TestCase):
    def setUp(self):
        self.parser = GoldSignalParser()

    def test_parse_valid_buy_signal(self):
        msg = """
        👑 GOLD BUY NOW 👑

        PRICE: 4500 - 4497

        TP1 🎖: 4504
        TP2 🎖: 4510

        SL: 4492‼️

        ❗️ Entry Pelan-Pelan ❗️
        ❗️ Jaga Money Management❗️
        """
        signal = self.parser.parse(msg)
        
        self.assertIsNotNone(signal)
        self.assertEqual(signal.symbol, "GOLD")
        self.assertEqual(signal.action, "BUY")
        self.assertEqual(signal.entry_min, 4497.0) # Diautomatic-swap karena __post_init__ mengurutkan
        self.assertEqual(signal.entry_max, 4500.0)
        self.assertEqual(signal.take_profits, [4504.0, 4510.0])
        self.assertEqual(signal.stop_loss, 4492.0)

    def test_parse_valid_sell_signal(self):
        msg = """
        👑 GOLD SELL NOW 👑

        PRICE: 4464 - 4467

        TP1 🎖: 4461
        TP2 🎖: 4458

        SL: 4472‼️

        ❗️ Entry Pelan-Pelan ❗️
        ❗️ Jaga Money Management❗️
        """
        signal = self.parser.parse(msg)
        
        self.assertIsNotNone(signal)
        self.assertEqual(signal.symbol, "GOLD")
        self.assertEqual(signal.action, "SELL")
        self.assertEqual(signal.entry_min, 4464.0)
        self.assertEqual(signal.entry_max, 4467.0)
        self.assertEqual(signal.take_profits, [4461.0, 4458.0])
        self.assertEqual(signal.stop_loss, 4472.0)

    def test_parse_ignored_message_no_price(self):
        # Pesan tanpa kata "PRICE:" harus mengembalikan None
        msg = "Halo, hari ini market GOLD sangat volatile!"
        signal = self.parser.parse(msg)
        self.assertIsNone(signal)

    def test_parse_invalid_action(self):
        # Pesan dengan PRICE tapi action bukan BUY/SELL
        msg = """
        👑 GOLD HOLD NOW 👑

        PRICE: 4464 - 4467

        TP1 🎖: 4461
        SL: 4472
        """
        signal = self.parser.parse(msg)
        self.assertIsNone(signal)

    def test_parse_with_different_spacing_and_emojis(self):
        msg = "GOLD BUY NOW\nPRICE:4500-4497\nTP1:4504\nSL: 4492"
        signal = self.parser.parse(msg)
        
        self.assertIsNotNone(signal)
        self.assertEqual(signal.symbol, "GOLD")
        self.assertEqual(signal.action, "BUY")
        self.assertEqual(signal.entry_min, 4497.0)
        self.assertEqual(signal.entry_max, 4500.0)
        self.assertEqual(signal.take_profits, [4504.0])
        self.assertEqual(signal.stop_loss, 4492.0)


class TestHitTPParser(unittest.TestCase):
    def setUp(self):
        self.parser = HitTPParser()

    def test_parse_valid_hit_tp(self):
        msg = "GOLD DONE HIT TP1"
        update = self.parser.parse(msg)
        self.assertIsNotNone(update)
        self.assertEqual(update.symbol, "GOLD")
        self.assertEqual(update.update_text, "DONE HIT TP1")

    def test_parse_valid_hit_tp_no_done(self):
        msg = "GOLD HIT TP2"
        update = self.parser.parse(msg)
        self.assertIsNotNone(update)
        self.assertEqual(update.symbol, "GOLD")
        self.assertEqual(update.update_text, "HIT TP2")

    def test_parse_valid_hit_sl(self):
        msg = "GOLD HIT SL"
        update = self.parser.parse(msg)
        self.assertIsNotNone(update)
        self.assertEqual(update.symbol, "GOLD")
        self.assertEqual(update.update_text, "HIT SL")

    def test_parse_invalid_update(self):
        msg = "GOLD IS GOING UP"
        update = self.parser.parse(msg)
        self.assertIsNone(update)


if __name__ == "__main__":
    unittest.main()
