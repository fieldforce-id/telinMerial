# Gunakan image Python slim sebagai base image untuk menjaga ukuran container kecil
FROM python:3.11-slim

# Tentukan working directory di dalam container
WORKDIR /app

# Atur environment variables untuk Python
# PYTHONDONTWRITEBYTECODE=1: Mencegah Python menulis file pyc ke disk
# PYTHONUNBUFFERED=1: Memaksa log langsung dikirim ke stdout tanpa buffering
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Salin file requirements.txt ke dalam container
COPY requirements.txt .

# Instal dependensi Python
RUN pip install --no-cache-dir -r requirements.txt

# Salin kode aplikasi (direktori src dan file entrypoint)
COPY src/ ./src
COPY main.py .
COPY login.py .

# Jalankan aplikasi utama secara default
CMD ["python", "main.py"]
