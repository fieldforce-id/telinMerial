# Telegram Signal Listener & Forwarder

Aplikasi Python berbasis Clean Architecture yang memonitoring sinyal trading dari grup Telegram tertentu, menyaring & memparsing teks pesan secara otomatis, lalu meneruskannya ke satu atau beberapa akun target (channel/group/kontak) lain dengan format yang rapi dan seragam.

---

## Fitur Utama

- **Clean Architecture**: Pemisahan tegas antara logika bisnis (Domain & Use Cases) dengan detail teknis Telegram (Infrastructure & Adapters).
- **Multi-Source & Multi-Target**: Memantau banyak grup sumber dengan tipe parser berbeda, lalu meneruskan pesan ke banyak target sekaligus.
- **Pemuatan Konfigurasi Terpisah**:
  - `.env` untuk kredensial sensitif (`api_id`, `api_hash`).
  - `config.yaml` untuk daftar routing grup (sumber dan target).
- **Graceful Shutdown**: Menutup koneksi Telegram secara aman saat aplikasi dihentikan (SIGINT/SIGTERM).
- **Logging Lengkap**: Mencatat alur proses aplikasi ke terminal dan file log (`app.log`).
- **Resilience**: Penanganan error tangguh sehingga kegagalan pengiriman ke salah satu target tidak menggagalkan pengiriman ke target lainnya.
- **Docker Ready**: Tersedia `Dockerfile` untuk deployment cepat di server VPS.

---

## Persyaratan Sistem

- Python 3.10+
- Akun Telegram (beserta `api_id` dan `api_hash` dari [my.telegram.org](https://my.telegram.org))

---

## Langkah Instalasi & Penggunaan

### 1. Kloning & Persiapan
Buka terminal Anda di direktori proyek ini.

```bash
# Buat virtual environment
python3 -m venv .venv

# Aktifkan virtual environment
source .venv/bin/activate  # Untuk macOS/Linux
# atau
.venv\Scripts\activate     # Untuk Windows

# Instal dependensi
pip install -r requirements.txt
```

### 2. Konfigurasi
1. Salin `.env.example` menjadi `.env`:
   ```bash
   cp .env.example .env
   ```
2. Buka `.env` dan masukkan `TELEGRAM_API_ID` serta `TELEGRAM_API_HASH` Anda.
3. Edit [config.yaml](file:///Users/benysutanto/Documents/Works/Personal/telinMerial/config.yaml) untuk menentukan grup sumber yang dipantau (`sources`) dan target pengiriman (`targets`).

### 3. Login Pertama Kali (Interaktif)
Karena Telegram memerlukan otentikasi satu kali melalui OTP, jalankan perintah berikut di terminal lokal Anda untuk membuat file sesi:

```bash
python login.py
```
Masukkan nomor telepon Anda (dengan kode negara, contoh: `+62812xxx`), lalu masukkan kode verifikasi yang Anda terima di Telegram. File sesi `{session_name}.session` akan terbuat secara lokal.

### 4. Menjalankan Aplikasi
Setelah sesi dibuat, jalankan listener secara terus-menerus menggunakan perintah:

```bash
python main.py
```

---

## Deployment Menggunakan Docker

Anda bisa mendeploy aplikasi ini di server VPS menggunakan Docker secara mudah:

### 1. Langkah Persiapan
Pastikan Anda sudah menjalankan `python login.py` secara lokal dan memiliki file sesi (misalnya `telin_merial_session.session`).

### 2. Build Docker Image
```bash
docker build -t telegram-listener .
```

### 3. Jalankan Container
Jalankan container dengan melakukan mounting file `.env`, `config.yaml`, dan file `.session` agar data sesi tetap persisten di server:

```bash
docker run -d \
  --name telegram-listener-app \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v $(pwd)/telin_merial_session.session:/app/telin_merial_session.session \
  telegram-listener
```

### 4. Cek Log Container
```bash
docker logs -f telegram-listener-app
```
