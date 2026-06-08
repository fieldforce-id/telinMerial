import asyncio
import logging
import sys
from src.adapters.config.loader import load_config
from src.adapters.telegram.client import TelegramClientAdapter

# Setup logging ke stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("login_script")

async def main():
    logger.info("Memulai proses inisialisasi login Telegram...")
    
    # 1. Load config dari .env dan config.yaml
    try:
        config = load_config()
        logger.info("Konfigurasi berhasil dimuat.")
    except Exception as e:
        logger.error(f"Gagal memuat konfigurasi: {e}")
        sys.exit(1)

    # 2. Inisialisasi adapter Telegram Client
    adapter = TelegramClientAdapter(config)

    # 3. Jalankan start (akan meminta input OTP/No HP di terminal jika belum login)
    try:
        logger.info("Mencoba menghubungkan client. Jika ini pertama kali, ikuti instruksi login di terminal.")
        await adapter.start()
        
        # Cek status otorisasi
        if await adapter.is_authorized():
            me = await adapter.client.get_me()
            logger.info("==================================================")
            logger.info("LOGIN SUKSES!")
            logger.info(f"Nama Akun  : {me.first_name} {me.last_name or ''}")
            logger.info(f"Username   : @{me.username or 'tidak ada'}")
            logger.info(f"User ID    : {me.id}")
            logger.info(f"Sesi disimpan sebagai: {config.session_name}.session")
            logger.info("==================================================")
        else:
            logger.error("Gagal mendapatkan otorisasi login.")
            
    except Exception as e:
        logger.error(f"Terjadi kesalahan saat proses login: {e}", exc_info=True)
    finally:
        # Putus koneksi agar sesi disimpan dengan aman
        await adapter.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
