import unittest
from unittest.mock import AsyncMock, MagicMock
import sys
import os

# Tambahkan project root ke sys.path agar src bisa di-import
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from src.core.use_cases.monitor_groups import MonitorGroupsUseCase
from src.core.entities.signal import TradingSignal, SignalUpdate, RawMessage

class TestMonitorGroupsUseCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # 1. Mock Config
        self.mock_source = MagicMock()
        self.mock_source.chat_id = -100123456789
        self.mock_source.parser_type = "gold"
        self.mock_source.name = "Test Source Group"
        
        self.mock_config = MagicMock()
        self.mock_config.sources = [self.mock_source]
        
        # 2. Callback Mock (Async)
        self.mock_callback = AsyncMock()
        
        # 3. Instance Use Case
        self.use_case = MonitorGroupsUseCase(
            config=self.mock_config,
            on_signal_parsed=self.mock_callback
        )

    async def test_handle_new_message_success(self):
        msg = """
        👑 GOLD BUY NOW 👑
        PRICE: 4500 - 4497
        TP1 🎖: 4504
        SL: 4492‼️
        """
        
        # Jalankan use case handler
        await self.use_case.handle_new_message(msg, chat_id=-100123456789)
        
        # Callback harus dipanggil sekali
        self.mock_callback.assert_called_once()
        
        # Periksa argumen panggilan
        parsed_signal = self.mock_callback.call_args[0][0]
        self.assertIsInstance(parsed_signal, TradingSignal)
        self.assertEqual(parsed_signal.symbol, "GOLD")
        self.assertEqual(parsed_signal.action, "BUY")
        self.assertEqual(parsed_signal.entry_min, 4497.0)
        self.assertEqual(parsed_signal.entry_max, 4500.0)
        self.assertEqual(parsed_signal.take_profits, [4504.0])
        self.assertEqual(parsed_signal.stop_loss, 4492.0)
        self.assertEqual(parsed_signal.source_group, "")

    async def test_handle_new_message_ignored_no_price(self):
        msg = "👑 GOLD BUY NOW 👑\nTidak ada kata kunci harga di sini."
        
        await self.use_case.handle_new_message(msg, chat_id=-100123456789)
        
        # Callback tidak boleh dipanggil karena tidak ada kata PRICE:
        self.mock_callback.assert_not_called()

    async def test_handle_new_message_ignored_unregistered_group(self):
        msg = "👑 GOLD BUY NOW 👑\nPRICE: 4500 - 4497\nTP1: 4504\nSL: 4492"
        
        # Kirim dari chat_id yang salah (-999999)
        await self.use_case.handle_new_message(msg, chat_id=-999999)
        
        # Callback tidak boleh dipanggil karena grup tidak terdaftar di config
        self.mock_callback.assert_not_called()

    async def test_update_config_dynamic_reloads_sources(self):
        # 1. Cek konfigurasi awal
        self.assertIn(-100123456789, self.use_case.group_parsers_by_id)
        self.assertEqual(self.use_case.group_parsers_by_id[-100123456789], "gold")

        # 2. Buat mock config baru dengan grup sumber baru
        new_source = MagicMock()
        new_source.chat_id = -100555555555
        new_source.parser_type = "price"
        new_source.name = "New Source Group"
        
        new_config = MagicMock()
        new_config.sources = [new_source]

        # 3. Panggil update_config
        self.use_case.update_config(new_config)

        # 4. Verifikasi bahwa konfigurasi telah berubah secara dinamis
        self.assertNotIn(-100123456789, self.use_case.group_parsers_by_id)
        self.assertIn(-100555555555, self.use_case.group_parsers_by_id)
        self.assertEqual(self.use_case.group_parsers_by_id[-100555555555], "price")
        self.assertIn("new source group", self.use_case.group_parsers_by_name)

    async def test_handle_new_message_success_by_name(self):
        # 1. Buat source dengan chat_id=None dan name="VIP Gold Signals"
        self.mock_source.chat_id = None
        self.mock_source.name = "VIP Gold Signals"
        self.use_case.update_config(self.mock_config)

        msg = """
        👑 GOLD BUY NOW 👑
        PRICE: 4500 - 4497
        TP1 🎖: 4504
        SL: 4492‼️
        """
        
        # Jalankan use case handler dengan chat_id=9999 (tidak terdaftar) tapi chat_title="VIP Gold Signals IND" (cocok secara partial)
        await self.use_case.handle_new_message(msg, chat_id=9999, chat_title="VIP Gold Signals IND")
        
        # Callback harus dipanggil sekali
        self.mock_callback.assert_called_once()
        
        # Periksa argumen panggilan
        parsed_signal = self.mock_callback.call_args[0][0]
        self.assertEqual(parsed_signal.symbol, "GOLD")
        self.assertEqual(parsed_signal.action, "BUY")
        self.assertEqual(parsed_signal.source_group, "VIP Gold Signals IND")

    async def test_handle_new_message_multi_parser_price(self):
        # Set parser_type ke "price, hit_tp"
        self.mock_source.parser_type = "price, hit_tp"
        self.use_case.update_config(self.mock_config)

        msg = "GOLD BUY NOW\nPRICE: 4500 - 4497\nTP1: 4504\nSL: 4492"
        await self.use_case.handle_new_message(msg, chat_id=-100123456789, chat_title="Test Source Group")

        self.mock_callback.assert_called_once()
        parsed_signal = self.mock_callback.call_args[0][0]
        self.assertIsInstance(parsed_signal, TradingSignal)
        self.assertEqual(parsed_signal.symbol, "GOLD")
        self.assertEqual(parsed_signal.source_group, "Test Source Group")

    async def test_handle_new_message_multi_parser_hit_tp(self):
        # Set parser_type ke "price, hit_tp"
        self.mock_source.parser_type = "price, hit_tp"
        self.use_case.update_config(self.mock_config)

        msg = "GOLD DONE HIT TP1"
        await self.use_case.handle_new_message(msg, chat_id=-100123456789, chat_title="Test Source Group")

        self.mock_callback.assert_called_once()
        parsed_update = self.mock_callback.call_args[0][0]
        self.assertIsInstance(parsed_update, SignalUpdate)
        self.assertEqual(parsed_update.symbol, "GOLD")
        self.assertEqual(parsed_update.update_text, "DONE HIT TP1")
        self.assertEqual(parsed_update.source_group, "Test Source Group")

    async def test_handle_new_message_raw_keyword_match(self):
        # Set parser_type ke "price, GOLD DONE HIT TP1"
        self.mock_source.parser_type = "price, GOLD DONE HIT TP1"
        self.use_case.update_config(self.mock_config)

        msg = "GOLD DONE HIT TP1"
        await self.use_case.handle_new_message(msg, chat_id=-100123456789, chat_title="Test Source Group")

        self.mock_callback.assert_called_once()
        parsed_raw = self.mock_callback.call_args[0][0]
        self.assertIsInstance(parsed_raw, RawMessage)
        self.assertEqual(parsed_raw.text, "GOLD DONE HIT TP1")
        self.assertEqual(parsed_raw.source_group, "Test Source Group")

if __name__ == "__main__":
    unittest.main()
