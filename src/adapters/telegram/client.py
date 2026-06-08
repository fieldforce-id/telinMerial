import logging
from typing import Callable, List, Union, Awaitable
# pyrefly: ignore [missing-import]
from telethon import TelegramClient, events
from src.adapters.config.loader import AppConfig

logger = logging.getLogger(__name__)

class TelegramClientAdapter:
    """
    Adapter untuk membungkus Telethon TelegramClient.
    Menyediakan interface bersih untuk interaksi dengan Telegram API.
    """
    def __init__(self, config: AppConfig):
        self.config = config
        # File session akan disimpan di project root
        self.client = TelegramClient(
            config.session_name,
            config.api_id,
            config.api_hash
        )

    async def connect(self) -> None:
        """
        Menghubungkan client ke Telegram network.
        """
        logger.info("Menghubungkan ke Telegram...")
        await self.client.connect()
        logger.info("Terhubung ke Telegram.")

    async def is_authorized(self) -> bool:
        """
        Memeriksa apakah session saat ini sudah masuk (authorized).
        """
        return await self.client.is_user_authorized()

    async def start(self) -> None:
        """
        Memulai client. Jika belum login, akan memicu login interaktif di terminal.
        """
        logger.info("Memulai sesi Telegram...")
        await self.client.start()
        logger.info("Sesi Telegram berhasil dimulai.")

    async def disconnect(self) -> None:
        """
        Memutus koneksi client secara aman.
        """
        logger.info("Memutuskan koneksi dari Telegram...")
        await self.client.disconnect()
        logger.info("Koneksi Telegram terputus.")

    async def send_message(self, chat_id: Union[int, str], text: str) -> None:
        """
        Mengirim pesan teks ke chat_id atau username tertentu.
        """
        logger.info(f"Mengirim pesan ke chat_id: {chat_id} - {text} ")
        await self.client.send_message(chat_id, text)

    # def register_message_handler(self, chat_ids: List[int], callback: Callable[[str, int], Awaitable[None]]) -> None:
    def register_message_handler(self, chat_ids: List[int], callback: Callable[[str, int, str], Awaitable[None]]) -> None:
        """
        Mendaftarkan callback asynchronous untuk mendengarkan pesan baru dari daftar chat_ids.
        """
        self.update_message_handler(chat_ids, callback)

    # def update_message_handler(self, chat_ids: List[int], callback: Callable[[str, int], Awaitable[None]]) -> None:
    def update_message_handler(self, chat_ids: List[int], callback: Callable[[str, int, str], Awaitable[None]]) -> None:
        """
        Memperbarui handler pesan masuk secara dinamis.
        Mendengarkan semua pesan masuk untuk dapat mencetak chat_id dan nama chat yang belum terdaftar.
        Menghapus handler lama (jika ada) dan mendaftarkan handler baru untuk chat_ids yang baru. (ini yg listening berdasarkan id yg terdaftar)
        """
        if hasattr(self, '_registered_handler') and self._registered_handler:
            logger.info("Menghapus handler event pesan lama...")
            self.client.remove_event_handler(self._registered_handler)
            self._registered_handler = None

        logger.info("Mendaftarkan handler event pesan baru (Mendengarkan semua chat untuk mempermudah deteksi chat_id)...")
        # @self.client.on(events.NewMessage(chats=chat_ids))

        # @self.client.on(events.NewMessage(chats=chat_ids))
        @self.client.on(events.NewMessage())
        async def handler(event):
            # Abaikan pesan kosong atau bukan berupa text
            if not event.raw_text:
                return
            
            chat_id = event.chat_id
            text = event.raw_text
            
            # Dapatkan nama chat/grup
            chat = await event.get_chat()
            chat_title = getattr(chat, 'title', None) or getattr(chat, 'username', None) or getattr(chat, 'first_name', None) or ""
            
            # Print ke konsol/log setiap kali ada pesan masuk untuk membantu melihat chat_id dan nama grup
            logger.info(f"📥 [PESAN MASUK] Chat ID: {chat_id} | Nama: '{chat_title}' | Teks: {text.strip().replace(chr(10), ' ')[:60]}...")
            
            try:
                # await callback(text, chat_id)
                await callback(text, chat_id, chat_title)
            except Exception as e:
                logger.error(f"Error saat mengeksekusi callback handler: {e}", exc_info=True)

        self._registered_handler = handler

    async def run_until_disconnected(self) -> None:
        """
        Menjaga aplikasi tetap berjalan untuk terus mendengarkan event baru.
        """
        logger.info("Aplikasi sedang mendengarkan pesan (listening)... Tekan Ctrl+C untuk keluar.")
        await self.client.run_until_disconnected()
