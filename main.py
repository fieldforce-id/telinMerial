import asyncio
import logging
import os
import signal
import sys
from src.adapters.config.loader import load_config
from src.adapters.telegram.client import TelegramClientAdapter
from src.core.use_cases.monitor_groups import MonitorGroupsUseCase
from src.core.use_cases.forward_signal import ForwardSignalUseCase

# Setup loggers (ke stdout dan file app.log)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("app.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("main")

async def watch_config_changes(
    config_path: str,
    env_path: str,
    monitor_use_case: MonitorGroupsUseCase,
    forward_use_case: ForwardSignalUseCase,
    telegram_client: TelegramClientAdapter
):
    """
    Memantau perubahan file config.yaml dan .env setiap 5 detik.
    Jika ada perubahan, konfigurasi dimuat ulang dan diterapkan secara dinamis.
    """
    logger.info("Memulai background task pemantau file konfigurasi (Hot Reload)...")
    
    # Dapatkan waktu modifikasi awal
    last_config_mtime = os.path.getmtime(config_path) if os.path.exists(config_path) else 0
    last_env_mtime = os.path.getmtime(env_path) if os.path.exists(env_path) else 0

    while True:
        await asyncio.sleep(5)  # Cek setiap 5 detik
        try:
            current_config_mtime = os.path.getmtime(config_path) if os.path.exists(config_path) else 0
            current_env_mtime = os.path.getmtime(env_path) if os.path.exists(env_path) else 0

            # Jika terdeteksi perubahan pada salah satu file
            if current_config_mtime != last_config_mtime or current_env_mtime != last_env_mtime:
                logger.info("Mendeteksi perubahan file konfigurasi. Memuat ulang (hot reloading)...")
                
                # Muat konfigurasi baru
                new_config = load_config()
                
                # Perbarui konfigurasi di Use Cases
                monitor_use_case.update_config(new_config)
                forward_use_case.update_config(new_config)
                
                # Perbarui event listener di Telegram client
                new_source_chat_ids = [src.chat_id for src in new_config.sources]
                logger.info("Parsed message----- %s ", new_source_chat_ids)
                telegram_client.update_message_handler(
                    chat_ids=new_source_chat_ids,
                    callback=monitor_use_case.handle_new_message
                )

                
                
                # Simpan timestamp modifikasi terbaru
                last_config_mtime = current_config_mtime
                last_env_mtime = current_env_mtime
                
                logger.info("Konfigurasi baru berhasil diterapkan secara dinamis tanpa restart!")
                
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Gagal memuat ulang konfigurasi secara otomatis: {e}")

async def main_async():
    logger.info("Memulai aplikasi Telegram Signal Listener & Forwarder...")
    
    # 1. Muat Konfigurasi dari .env dan config.yaml
    try:
        config = load_config()
        logger.info("Konfigurasi berhasil dimuat.")
    except Exception as e:
        logger.critical(f"Gagal memuat konfigurasi: {e}")
        sys.exit(1)
        
    # 2. Inisialisasi Adapter Telegram Client
    telegram_client = TelegramClientAdapter(config)
    
    # 3. Inisialisasi Use Cases (Composition Root)
    forward_use_case = ForwardSignalUseCase(config, telegram_client)
    
    # Callback saat sinyal berhasil diparsing oleh Monitor Use Case
    async def on_signal_parsed(signal_obj):
        await forward_use_case.execute(signal_obj)
        
    monitor_use_case = MonitorGroupsUseCase(config, on_signal_parsed)
    
    # 4. Daftarkan Event Listener untuk grup-grup sumber
    source_chat_ids = [src.chat_id for src in config.sources]
    if not source_chat_ids:
        logger.warning("Peringatan: Tidak ada grup sumber yang dikonfigurasi untuk dipantau.")
    
    telegram_client.register_message_handler(
        chat_ids=source_chat_ids,
        callback=monitor_use_case.handle_new_message
    )
    
    # 5. Tangani Graceful Shutdown (SIGTERM & SIGINT)
    loop = asyncio.get_running_loop()
    shutdown_triggered = False
    
    async def shutdown(sig=None):
        nonlocal shutdown_triggered
        if shutdown_triggered:
            return
        shutdown_triggered = True
        
        sig_name = sig.name if sig else "manual"
        logger.info(f"Sinyal shutdown diterima ({sig_name}). Menghentikan aplikasi secara aman...")
        
        try:
            await telegram_client.disconnect()
            logger.info("Koneksi Telegram berhasil ditutup.")
        except Exception as e:
            logger.error(f"Gagal memutus koneksi Telegram secara bersih: {e}")
            
        logger.info("Aplikasi dihentikan dengan sukses.")
        
        # Batalkan semua task yang sedang berjalan di event loop
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
            
    # loop.add_signal_handler hanya didukung di platform berbasis Unix (bukan Windows)
    if sys.platform != "win32":
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s)))
            
    # 6. Jalankan Telegram Client
    try:
        await telegram_client.start()
        
        # Validasi status otorisasi
        if not await telegram_client.is_authorized():
            logger.critical(
                "Error: Sesi belum terautentikasi! "
                "Silakan jalankan perintah 'python login.py' terlebih dahulu di terminal Anda untuk masuk."
            )
            await telegram_client.disconnect()
            sys.exit(1)
            
        me = await telegram_client.client.get_me()
        logger.info(f"Otorisasi sukses. Berjalan menggunakan akun: {me.first_name} {me.last_name or ''} (@{me.username or 'no_username'})")
        logger.info(f"Mulai mendengarkan pesan dari {len(source_chat_ids)} grup sumber...")
        logger.info(f"Sinyal yang valid akan diteruskan ke {len(config.targets)} target.")
        
        # Jalankan background task untuk Hot Reload
        config_path = os.getenv("CONFIG_PATH", "config.yaml")
        env_path = ".env"
        asyncio.create_task(
            watch_config_changes(
                config_path=config_path,
                env_path=env_path,
                monitor_use_case=monitor_use_case,
                forward_use_case=forward_use_case,
                telegram_client=telegram_client
            )
        )
        
        # Blok eksekusi untuk mendengarkan pesan
        await telegram_client.run_until_disconnected()
        
    except asyncio.CancelledError:
        # Ditangkap saat graceful shutdown membatalkan semua task
        pass
    except Exception as e:
        logger.critical(f"Terjadi error fatal pada runtime aplikasi: {e}", exc_info=True)
        sys.exit(1)

def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("Aplikasi dihentikan oleh pengguna (KeyboardInterrupt).")

if __name__ == "__main__":
    main()
