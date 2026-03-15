import os
from pathlib import Path

DATABASE_URL: str = os.getenv("DATABASE_URL", "netvista.db")
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8040"))
NMAP_PATH: str = os.getenv("NMAP_PATH", "nmap")
DATA_DIR: Path = Path(os.getenv("DATA_DIR", "/data" if os.path.exists("/data") else "."))
CORS_ORIGINS: list[str] = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5175").split(",")
    if o.strip()
]
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
