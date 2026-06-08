import unittest
from unittest.mock import AsyncMock, MagicMock
import sys
import os

# Tambahkan project root ke sys.path agar src bisa di-import
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from src.core.use_cases.forward_signal import ForwardSignalUseCase, format_signal_message, format_update_message, format_raw_message
from src.core.entities.signal import TradingSignal, SignalUpdate, RawMessage

class TestForwardSignalUseCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # 1. Mock Targets
        self.target1 = MagicMock()
        self.target1.chat_id = -100111222333
        self.target1.name = "Target A"
        
        self.target2 = MagicMock()
        self.target2.chat_id = 87654321
        self.target2.name = "Target B"
        
        self.mock_config = MagicMock()
        self.mock_config.targets = [self.target1, self.target2]
        
        # 2. Mock Telegram Sender
        self.mock_sender = MagicMock()
        self.mock_sender.send_message = AsyncMock()
        
        # 3. Instance Use Case
        self.use_case = ForwardSignalUseCase(
            config=self.mock_config,
            telegram_sender=self.mock_sender
        )

    def test_format_signal_message(self):
        # Uji logika format pesan teks tanpa source group
        signal = TradingSignal(
            symbol="GOLD",
            action="BUY",
            entry_min=4497.0,
            entry_max=4500.0,
            take_profits=[4504.0, 4510.0],
            stop_loss=4492.0
        )
        
        formatted = format_signal_message(signal)
        
        self.assertIn("📢 **NEW SIGNAL RECEIVED** 📢", formatted)
        self.assertIn("📅 **Date**:", formatted)
        self.assertNotIn("🔹 **Pair**:", formatted)
        self.assertIn("🔹 **Action**: BUY NOW", formatted)
        self.assertIn("🔹 **Range Entry**: 4497 - 4500", formatted)
        self.assertIn("🎯 **Target Profit**:\n- TP 1: 4504\n- TP 2: 4510", formatted)
        self.assertIn("🛑 **Stop Loss**: 4492", formatted)
        self.assertIn("⚠️ *Jaga Money Management & Entry Pelan-Pelan*", formatted)

    def test_format_signal_message_with_source_group(self):
        # Uji logika format pesan teks dengan source group
        signal = TradingSignal(
            symbol="GOLD",
            action="BUY",
            entry_min=4497.0,
            entry_max=4500.0,
            take_profits=[4504.0],
            stop_loss=4492.0,
            source_group="CIRCLE TGA IND"
        )
        
        formatted = format_signal_message(signal)
        self.assertIn("📢 **NEW SIGNAL RECEIVED - CIRCLE TGA IND** 📢", formatted)

    async def test_execute_forward_to_multiple_targets(self):
        signal = TradingSignal(
            symbol="GOLD",
            action="SELL",
            entry_min=4464.0,
            entry_max=4467.0,
            take_profits=[4461.0, 4458.0],
            stop_loss=4472.0
        )
        
        # Eksekusi Use Case
        await self.use_case.execute(signal)
        
        # Pastikan send_message dipanggil 2 kali (sekali untuk masing-masing target)
        self.assertEqual(self.mock_sender.send_message.call_count, 2)
        
        # Verifikasi pemanggilan pertama
        self.mock_sender.send_message.assert_any_call(-100111222333, format_signal_message(signal))
        # Verifikasi pemanggilan kedua
        self.mock_sender.send_message.assert_any_call(87654321, format_signal_message(signal))

    async def test_execute_resilient_to_individual_failures(self):
        signal = TradingSignal(
            symbol="GOLD",
            action="BUY",
            entry_min=4500.0,
            entry_max=4497.0,
            take_profits=[4504.0],
            stop_loss=4492.0
        )
        
        # Buat pengiriman ke target pertama gagal, tetapi target kedua sukses
        async def side_effect(chat_id, text):
            if chat_id == -100111222333:
                raise Exception("Network Timeout")
            return None
        
        self.mock_sender.send_message.side_effect = side_effect
        
        # Eksekusi Use Case (tidak boleh melempar exception ke luar)
        await self.use_case.execute(signal)
        
        # Verifikasi bahwa send_message tetap dicoba ke kedua target
        self.assertEqual(self.mock_sender.send_message.call_count, 2)

    def test_format_update_message_without_group(self):
        update = SignalUpdate(
            symbol="GOLD",
            update_text="DONE HIT TP1"
        )
        formatted = format_update_message(update)
        self.assertIn("📢 **SIGNAL UPDATE** 📢", formatted)
        self.assertIn("📅 **Date**:", formatted)
        self.assertIn("✅ **GOLD DONE HIT TP1**", formatted)
        self.assertIn("⚠️ *Jaga Money Management & Entry Pelan-Pelan*", formatted)

    def test_format_update_message_with_group(self):
        update = SignalUpdate(
            symbol="GOLD",
            update_text="HIT SL",
            source_group="CIRCLE TGA"
        )
        formatted = format_update_message(update)
        self.assertIn("📢 **SIGNAL UPDATE - CIRCLE TGA** 📢", formatted)
        self.assertIn("✅ **GOLD HIT SL**", formatted)

    async def test_execute_forward_update_to_multiple_targets(self):
        update = SignalUpdate(
            symbol="GOLD",
            update_text="DONE HIT TP2",
            source_group="CIRCLE TGA"
        )
        # Eksekusi Use Case
        await self.use_case.execute(update)
        
        # Pastikan send_message dipanggil 2 kali
        self.assertEqual(self.mock_sender.send_message.call_count, 2)
        self.mock_sender.send_message.assert_any_call(-100111222333, format_update_message(update))
        self.mock_sender.send_message.assert_any_call(87654321, format_update_message(update))

    def test_format_raw_message(self):
        raw = RawMessage(
            text="GOLD DONE HIT TP1",
            source_group="CIRCLE TGA"
        )
        formatted = format_raw_message(raw)
        self.assertIn("📢 **NEW SIGNAL RECEIVED - CIRCLE TGA** 📢", formatted)
        self.assertIn("GOLD DONE HIT TP1", formatted)

    async def test_execute_forward_raw_message_to_multiple_targets(self):
        raw = RawMessage(
            text="GOLD DONE HIT TP1",
            source_group="CIRCLE TGA"
        )
        await self.use_case.execute(raw)
        self.assertEqual(self.mock_sender.send_message.call_count, 2)
        self.mock_sender.send_message.assert_any_call(-100111222333, format_raw_message(raw))
        self.mock_sender.send_message.assert_any_call(87654321, format_raw_message(raw))

if __name__ == "__main__":
    unittest.main()
