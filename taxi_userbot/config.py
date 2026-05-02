import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
DB_PATH = str(Path(__file__).parent / "taxi_bot.db")

_missing = [
    name for name, val in [
        ("API_ID", API_ID), ("API_HASH", API_HASH),
        ("BOT_TOKEN", BOT_TOKEN),
    ] if not val
]
if not ADMIN_IDS:
    _missing.append("ADMIN_IDS")

if _missing:
    sys.exit(
        f"[config] Majburiy .env o'zgaruvchilari topilmadi: {', '.join(_missing)}\n"
        f"         .env.example faylini ko'rib, .env ni to'ldiring."
    )
