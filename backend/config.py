import os
from pathlib import Path

DATABASE_URL: str = os.getenv("DATABASE_URL", "netvista.db")
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8040"))
NMAP_PATH: str = os.getenv("NMAP_PATH", "nmap")
MAX_CONCURRENT_SCANS: int = int(os.getenv("MAX_CONCURRENT_SCANS", "2"))
DATA_DIR: Path = Path(os.getenv("DATA_DIR", "/data" if os.path.exists("/data") else "."))
