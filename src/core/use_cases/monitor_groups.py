import logging
from typing import Callable, Awaitable, Dict
from src.core.entities.signal import TradingSignal, RawMessage
from src.adapters.telegram.parsers.factory import get_parser

logger = logging.getLogger(__name__)

class MonitorGroupsUseCase:
    """
    Use Case untuk mengoordinasikan pemantauan grup-grup Telegram.
    Menerima pesan mentah, melakukan pemfilteran awal, memparsing sinyal, 
    dan menyerahkannya ke handler selanjutnya (misal: Forwarding Use Case).
    """
    def __init__(self, config, on_signal_parsed: Callable[[TradingSignal], Awaitable[None]]):
        self.config = config
        self.on_signal_parsed = on_signal_parsed
        self.update_config(config)

    async def handle_new_message(self, text: str, chat_id: int, chat_title: str = "") -> None:
        """
        Method handler utama yang dipanggil oleh listener ketika menerima pesan baru dari grup.
        """
        # 1. Dapatkan tipe parser untuk grup ini (berdasarkan chat_id atau pencocokan nama partial)
        parser_type_str = self.group_parsers_by_id.get(chat_id)
        if not parser_type_str and chat_title:
            chat_title_lower = chat_title.lower()
            for config_name_lower, p_type in self.group_parsers_by_name.items():
                # Jika nama di konfigurasi merupakan bagian (substring) dari nama grup asli
                # Contoh: "circle tga" cocok dengan grup "CIRCLE TGA IND"
                if config_name_lower in chat_title_lower:
                    parser_type_str = p_type
                    logger.info(f"Pencocokan nama grup berhasil secara partial: '{chat_title}' cocok dengan konfigurasi '{config_name_lower}'")
                    break

        if not parser_type_str:
            logger.debug(
                f"Pesan di chat {chat_id} ('{chat_title}') diabaikan "
                "karena grup tidak terdaftar sebagai grup sumber berdasarkan ID maupun Nama."
            )
            return

        parser_types = [pt.strip() for pt in parser_type_str.split(",")]

        # 2. Filter Kriteria Awal secara dinamis berdasarkan parser yang aktif
        has_match = False
        text_upper = text.upper()
        for p_type in parser_types:
            p_type_lower = p_type.lower()
            if p_type_lower in ("gold", "price") and "PRICE:" in text_upper:
                has_match = True
                break
            elif p_type_lower == "hit_tp" and ("HIT TP" in text_upper or "HIT SL" in text_upper):
                has_match = True
                break
            elif p_type_lower not in ("gold", "price", "hit_tp"):
                # Jika tipe parser tidak dikenal, perlakukan sebagai kata kunci mentah
                if p_type.upper() in text_upper:
                    has_match = True
                    break

        if not has_match:
            logger.debug(f"Pesan dari chat {chat_id} ('{chat_title}') diabaikan karena tidak memenuhi kriteria filter awal parser mana pun: {parser_types}.")
            return

        logger.info(f"Mendeteksi pesan potensial di chat {chat_id} ('{chat_title}')...")

        # 3. Parsing pesan mentah menggunakan parser yang sesuai secara bergantian
        parsed_obj = None
        successful_parser = None
        for p_type in parser_types:
            p_type_lower = p_type.lower()
            try:
                if p_type_lower in ("gold", "price", "hit_tp"):
                    parser = get_parser(p_type_lower)
                    parsed_obj = parser.parse(text)
                    if parsed_obj:
                        successful_parser = p_type_lower
                        break
                else:
                    # Jika tipe parser tidak dikenal, dan pesan mengandung kata kunci ini,
                    # kita buat objek RawMessage untuk dikirim apa adanya
                    if p_type.upper() in text.upper():
                        parsed_obj = RawMessage(text=text)
                        successful_parser = f"raw_keyword('{p_type}')"
                        break
            except Exception as e:
                logger.error(f"Gagal memproses pesan dengan parser '{p_type}': {e}", exc_info=True)

        if parsed_obj:
            parsed_obj.source_group = chat_title
            
            # Tambahkan detail log yang sesuai tipe entitas
            if isinstance(parsed_obj, TradingSignal):
                logger.info(f"Sinyal trading {parsed_obj.symbol} {parsed_obj.action} berhasil diparsing menggunakan parser '{successful_parser}'.")
            elif isinstance(parsed_obj, RawMessage):
                logger.info(f"Pesan mentah berhasil dicocokkan dengan kata kunci '{successful_parser}'.")
            else:
                logger.info(f"Update sinyal {parsed_obj.symbol} berhasil diparsing menggunakan parser '{successful_parser}'.")
            
            # Kirim ke callback (misal: Use Case Forwarding)
            await self.on_signal_parsed(parsed_obj)
        else:
            logger.warning(f"Pesan di chat {chat_id} ('{chat_title}') lolos filter awal, tetapi gagal diparsing oleh semua parser: {parser_types}.")

    def update_config(self, new_config) -> None:
        """
        Memperbarui konfigurasi grup sumber secara dinamis saat runtime.
        """
        self.config = new_config
        # Buat pemetaan terpisah untuk ID dan Nama
        self.group_parsers_by_id = {}
        self.group_parsers_by_name = {}
        
        for src in new_config.sources:
            if src.chat_id is not None:
                self.group_parsers_by_id[src.chat_id] = src.parser_type
            if src.name:
                self.group_parsers_by_name[src.name.lower()] = src.parser_type
                
        logger.info("MonitorGroupsUseCase berhasil memperbarui konfigurasi grup sumber secara dinamis.")
