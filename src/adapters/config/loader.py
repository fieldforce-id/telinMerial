import os
import yaml
from typing import List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field, ValidationError
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

class SourceConfig(BaseModel):
    chat_id: Optional[int] = None
    parser_type: str
    name: str

class TargetConfig(BaseModel):
    chat_id: int
    name: str

class AppConfig(BaseModel):
    # Telegram credentials (from env)
    api_id: int
    api_hash: str
    session_name: str
    
    # Sources and Targets routing (from yaml)
    sources: List[SourceConfig] = Field(default_factory=list)
    targets: List[TargetConfig] = Field(default_factory=list)


def load_config(env_path: Optional[str] = None) -> AppConfig:
    """
    Memuat konfigurasi aplikasi dengan menggabungkan .env (untuk kredensial)
    dan config.yaml (untuk rute grup sumber dan target).
    """
    # 1. Muat file .env jika ada
    if env_path:
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()

    # 2. Ambil variabel lingkungan untuk Telegram API
    api_id_raw = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_name = os.getenv("TELEGRAM_SESSION_NAME", "telin_merial_session")
    config_path = os.getenv("CONFIG_PATH", "config.yaml")

    if not api_id_raw:
        raise ValueError("Error: TELEGRAM_API_ID tidak ditemukan di environment (.env)")
    if not api_hash:
        raise ValueError("Error: TELEGRAM_API_HASH tidak ditemukan di environment (.env)")

    try:
        api_id = int(api_id_raw)
    except ValueError:
        raise ValueError(f"Error: TELEGRAM_API_ID harus berupa angka (integer), didapat: '{api_id_raw}'")

    # 3. Muat file YAML konfigurasi grup
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Error: File konfigurasi grup tidak ditemukan di path: '{config_path}'")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f) or {}
    except Exception as e:
        raise ValueError(f"Error: Gagal memparsing file YAML '{config_path}': {e}")

    # 4. Satukan dan validasi menggunakan Pydantic
    try:
        config = AppConfig(
            api_id=api_id,
            api_hash=api_hash,
            session_name=session_name,
            sources=yaml_data.get("sources", []),
            targets=yaml_data.get("targets", [])
        )
    except ValidationError as e:
        raise ValueError(f"Error: Validasi konfigurasi gagal:\n{e}")

    return config
