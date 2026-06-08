# Panduan Pengembangan: Telegram Signal Group Listener & Forwarder

Aplikasi Python berbasis Clean Architecture untuk memonitoring sinyal trading dari beberapa grup Telegram, menyaring dan memparsing sinyal tersebut, lalu meneruskannya ke beberapa target (channel/grup/kontak) lain secara otomatis.

---

## 1. Spesifikasi Teknis

- **Bahasa**: Python 3.10+
- **Library Telegram Utama**: `Telethon` (menggunakan Telegram Client API / Userbot)
- **Library Pembantu**: `pydantic` (validasi config dan data), `python-dotenv` (untuk memuat `.env`), `pyyaml` (untuk file konfigurasi `config.yaml`), `structlog` atau `logging` (untuk structured logging).
- **Arsitektur**: Clean Architecture (Entities, Use Cases, Gateways/Adapters, External/Main).

---

## 2. Struktur Folder (Clean Architecture)

```text
src/
├── core/
│   ├── entities/
│   │   └── signal.py         # Data class untuk Trading Signal (Symbol, Action, Entry, TP, SL, dll.)
│   └── use_cases/
│       ├── parse_signal.py   # Logika untuk memparsing text mentah menjadi Entity Signal
│       ├── forward_signal.py # Logika untuk meneruskan sinyal yang sudah terformat ke target
│       └── monitor_groups.py # Logika koordinasi monitoring grup
├── adapters/
│   ├── telegram/
│   │   ├── client.py         # Wrapper Telethon untuk listen & send
│   │   └── parsers/
│   │       ├── base.py       # Base class parser
│   │       ├── gold_parser.py# Parser khusus format GOLD (Buy/Sell)
│   │       └── custom_parser.py
│   └── config/
│       └── loader.py         # Adapter untuk memuat .env dan config.yaml
├── .env                      # File kredensial & path konfigurasi utama
├── .env.example              # Contoh file environment (tanpa data sensitif)
├── config.yaml               # File daftar grup sumber & target
└── main.py                   # Entry point aplikasi (Composition Root)
```

---

## 3. Detail Konfigurasi (`.env` & `config.yaml`)

Konfigurasi dibagi menjadi dua bagian:
1. **`.env`**: Menyimpan kredensial sensitif dan path file konfigurasi. File ini tidak boleh di-commit ke Git.
2. **`config.yaml`**: Menyimpan daftar grup sumber dan target (non-sensitif).

### Contoh `.env`
```env
# Telegram API Credentials
TELEGRAM_API_ID=123456
TELEGRAM_API_HASH="your_api_hash_here"
TELEGRAM_SESSION_NAME="telin_merial_session"

# Path ke file konfigurasi YAML
CONFIG_PATH="config.yaml"
```

### Contoh `config.yaml`
```yaml
# Grup sumber yang akan dipantau
sources:
  - chat_id: -100123456789   # ID Grup Telegram
    parser_type: "gold"       # Jenis parser yang digunakan untuk format grup ini
    name: "VIP Gold Signals"
  - chat_id: -100987654321
    parser_type: "forex_custom"
    name: "Forex Daily Group"

# Akun/Grup/Channel tujuan pengiriman
targets:
  - chat_id: -100111222333   # Target Channel A
    name: "My Channel"
  - chat_id: 87654321        # Target User/Bot
    name: "Personal Account"
```

---

## 4. Spesifikasi Logika Bisnis & Kondisi

### Kriteria Filter Pesan
- Hanya proses pesan yang mengandung kata kunci `PRICE:` (case-insensitive).
- Pesan tanpa kata kunci tersebut wajib diabaikan.

### Aturan Parsing & Pemformatan Ulang (Format Output)
Setiap pesan yang lolos filter akan diparsing menjadi Entity `Signal` yang berisi:
- **Symbol**: E.g., `GOLD` atau `XAUUSD`
- **Action**: `BUY` atau `SELL`
- **Entry Range**: Min & Max price (e.g., `4500` dan `4497`)
- **Take Profit (TP)**: List TP (misal, `TP1: 4504`, `TP2: 4510`)
- **Stop Loss (SL)**: Nilai SL (misal, `4492`)

#### Format Sinyal Sumber:
- **FORMAT Untuk Perintah Beli:**
  ```text
  👑 GOLD BUY NOW 👑

  PRICE: 4500 - 4497

  TP1 🎖: 4504
  TP2 🎖: 4510

  SL: 4492‼️

  ❗️ Entry Pelan-Pelan ❗️
  ❗️ Jaga Money Management❗️
  ```

- **FORMAT Untuk Perintah Jual:**
  ```text
  👑 GOLD SELL NOW 👑

  PRICE: 4464 - 4467

  TP1 🎖: 4461
  TP2 🎖: 4458

  SL: 4472‼️

  ❗️ Entry Pelan-Pelan ❗️
  ❗️ Jaga Money Management❗️
  ```

#### Format Output Standar yang Diteruskan:
Pesan yang dikirim ke target harus dirangkai ulang menjadi format yang bersih dan seragam seperti berikut:

```text
📢 **NEW SIGNAL RECEIVED** 📢

🔹 **Pair**: GOLD
🔹 **Action**: BUY NOW (atau SELL NOW)
🔹 **Entry**: 4500 - 4497

🎯 **Target Profit**:
- TP 1: 4504
- TP 2: 4510

🛑 **Stop Loss**: 4492

⚠️ *Jaga Money Management & Entry Pelan-Pelan*
```

---

## 5. Penanganan Error & Kestabilan
- **Auto Reconnect**: Sistem harus otomatis terhubung kembali jika koneksi ke Telegram terputus.
- **Fail-safe Parser**: Jika parsing gagal pada pesan yang memiliki kata `PRICE:`, kirimkan pesan mentah tersebut ke target dengan tag `[PARSING FAILED]` atau catat di log agar tidak menghentikan aplikasi.
- **Graceful Shutdown**: Aplikasi harus menangani sinyal sistem (`SIGINT`, `SIGTERM`) untuk menutup sesi Telegram dengan aman.

---

## 6. Rencana Fase Pengembangan (Roadmap)

### Fase 1: Setup Project & Konfigurasi (Foundation)
- Inisialisasi virtual environment Python (menggunakan `uv` atau `venv`).
- Membuat file `.env`, `.env.example`, dan `config.yaml`.
- Membuat skema validasi konfigurasi menggunakan `pydantic` dan `python-dotenv` untuk memuat variabel lingkungan dari `.env` dan file `config.yaml`.
- Setup folder project sesuai dengan **Clean Architecture**.

### Fase 2: Implementasi Telegram Client & Koneksi (Infrastructure)
- Membuat adapter Telethon (`adapters/telegram/client.py`) untuk login menggunakan `TELEGRAM_API_ID` dan `TELEGRAM_API_HASH` yang dimuat dari `.env`.
- Membuat mekanisme autentikasi interaktif (meminta nomor telepon & kode OTP pada login pertama kali) dan menyimpan file sesi `.session`.
- Melakukan verifikasi koneksi ke Telegram.

### Fase 3: Logika Parsing & Domain Entity (Core Business Logic)
- Membuat domain entity `TradingSignal` di `core/entities/signal.py`.
- Menulis unit testing dan membuat parser (`adapters/telegram/parsers/`) menggunakan Regex untuk mengenali pola format BUY/SELL, Price, TP, dan SL.
- Menangani variasi format pesan (seperti emoji, spasi ganda, baris baru).

### Fase 4: Listener & Filter Orchestration (Use Cases)
- Membuat Use Case `MonitorGroupsUseCase` untuk mendengarkan pesan baru (`events.NewMessage`) pada list grup sumber dari konfigurasi.
- Mengimplementasikan filter pesan (`PRICE:` check).
- Mengintegrasikan parser untuk mengonversi pesan mentah menjadi objek `TradingSignal`.

### Fase 5: Forwarding & Output Formatting (Delivery)
- Mengimplementasikan logika untuk memformat ulang objek `TradingSignal` ke format pesan teks baru yang bersih.
- Menulis Use Case `ForwardSignalUseCase` untuk mengirim pesan terformat ke daftar target yang dikonfigurasi.
- Uji coba pengiriman pesan ke multi-target.

### Fase 6: Penanganan Error, Logging, & Dockerization (Production Ready)
- Implementasi logging terstruktur menggunakan `logging` bawaan Python.
- Menambahkan auto-reconnection dan penanganan error ketika API Telegram limit/terputus.
- Membuat `Dockerfile` untuk deployment mudah di server VPS.
- Dokumentasi cara menjalankan aplikasi (`README.md`).