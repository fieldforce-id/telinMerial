import logging
from datetime import datetime, timezone, timedelta
from typing import Union
from src.core.entities.signal import TradingSignal, SignalUpdate, RawMessage

logger = logging.getLogger(__name__)

def format_signal_message(signal: TradingSignal) -> str:
    """
    Memformat objek TradingSignal menjadi string teks yang rapi dan mudah dibaca
    sesuai dengan spesifikasi tampilan output, menyertakan tanggal pengiriman.
    """
    tp_lines = []
    for i, tp in enumerate(signal.take_profits):
        # Format angka agar rapi (jika integer tampilkan tanpa desimal, jika float tampilkan desimalnya)
        tp_str = str(int(tp)) if tp.is_integer() else str(tp)
        tp_lines.append(f"- TP {i+1}: {tp_str}")
    tp_text = "\n".join(tp_lines)

    # Format entry dan stop loss
    entry_min_str = str(int(signal.entry_min)) if signal.entry_min.is_integer() else str(signal.entry_min)
    entry_max_str = str(int(signal.entry_max)) if signal.entry_max.is_integer() else str(signal.entry_max)
    sl_str = str(int(signal.stop_loss)) if signal.stop_loss.is_integer() else str(signal.stop_loss)

    # Format waktu saat ini (UTC+7)
    now_str = datetime.now(timezone(timedelta(hours=7))).strftime("%d-%m-%Y %H:%M:%S")

    # Format header dengan nama group jika ada
    if signal.source_group:
        header = f"📢 **NEW SIGNAL RECEIVED - {signal.source_group.upper()}** 📢"
    else:
        header = "📢 **NEW SIGNAL RECEIVED** 📢"

    return (
        f"{header}\n\n"
        f"📅 **Date**: {now_str}\n\n"
        # f"🔹 **Pair**: {signal.symbol.upper()}\n"
        f"🔹 **Action**: {signal.action.upper()} NOW\n"
        f"🔹 **Range Entry**: {entry_min_str} - {entry_max_str}\n\n"
        f"🎯 **Target Profit**:\n{tp_text}\n\n"
        f"🛑 **Stop Loss**: {sl_str}\n\n"
        f"⚠️ *Jaga Money Management & Entry Pelan-Pelan*"
    )


def format_update_message(update: SignalUpdate) -> str:
    """
    Memformat objek SignalUpdate (seperti GOLD DONE HIT TP1) menjadi string teks
    yang rapi dan konsisten dengan branding sinyal.
    """
    # Format header dengan nama group jika ada
    if update.source_group:
        header = f"📢 **SIGNAL UPDATE - {update.source_group.upper()}** 📢"
    else:
        header = "📢 **SIGNAL UPDATE** 📢"

    now_str = datetime.now(timezone(timedelta(hours=7))).strftime("%d-%m-%Y %H:%M:%S")

    return (
        f"{header}\n\n"
        f"📅 **Date**: {now_str}\n\n"
        f"✅ **{update.symbol} {update.update_text}**\n\n"
        f"⚠️ *Jaga Money Management & Entry Pelan-Pelan*"
    )


def format_raw_message(msg: RawMessage) -> str:
    """
    Memformat RawMessage agar memiliki header standar dan tanggal,
    namun konten pesannya tetap apa adanya (raw).
    """
    if msg.source_group:
        header = f"📢 **NEW SIGNAL RECEIVED - {msg.source_group.upper()}** 📢"
    else:
        header = "📢 **NEW SIGNAL RECEIVED** 📢"

    now_str = datetime.now(timezone(timedelta(hours=7))).strftime("%d-%m-%Y %H:%M:%S")

    return (
        f"{header}\n\n"
        f"📅 **Date**: {now_str}\n\n"
        f"{msg.text}"
    )


class ForwardSignalUseCase:
    """
    Use Case untuk meneruskan sinyal yang sudah terformat ke semua target telegram
    yang terdaftar di konfigurasi.
    """
    def __init__(self, config, telegram_sender):
        self.config = config
        self.telegram_sender = telegram_sender  # Dependency injection: adapter client

    async def execute(self, signal: Union[TradingSignal, SignalUpdate, RawMessage]) -> None:
        """
        Mengeksekusi pengiriman sinyal atau update terformat ke seluruh daftar target.
        """
        # 1. Format objek domain menjadi teks sesuai tipe entitasnya
        if isinstance(signal, TradingSignal):
            message_text = format_signal_message(signal)
            type_label = "sinyal"
        elif isinstance(signal, SignalUpdate):
            message_text = format_update_message(signal)
            type_label = "update"
        elif isinstance(signal, RawMessage):
            message_text = format_raw_message(signal)
            type_label = "pesan mentah"
        else:
            logger.error(f"Tipe entitas tidak dikenal untuk forwarding: {type(signal)}")
            return
        
        logger.info(f"Mengirim {type_label} terformat ke {len(self.config.targets)} target...")

        # 2. Kirim pesan ke semua target
        for target in self.config.targets:
            try:
                logger.info(f"Mengirim {type_label} ke target: '{target.name}' (Chat ID: {target.chat_id})")
                await self.telegram_sender.send_message(target.chat_id, message_text)
            except Exception as e:
                logger.error(
                    f"Gagal mengirim {type_label} ke target '{target.name}' (Chat ID: {target.chat_id}): {e}", 
                    exc_info=True
                )

    def update_config(self, new_config) -> None:
        """
        Memperbarui konfigurasi target pengiriman secara dinamis saat runtime.
        """
        self.config = new_config
        logger.info("ForwardSignalUseCase berhasil memperbarui konfigurasi target secara dinamis.")
