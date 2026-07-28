import os
from pathlib import Path

DATABASE_URL: str = os.getenv("DATABASE_URL", "netvista.db")
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8040"))
NMAP_PATH: str = os.getenv("NMAP_PATH", "nmap")
MAX_CONCURRENT_SCANS: int = int(os.getenv("MAX_CONCURRENT_SCANS", "2"))
# Allowed CORS origins (comma-separated). Defaults to the local dev frontend.
CORS_ORIGINS: list[str] = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5175").split(",")
    if o.strip()
]
# Optional API key. When empty, auth is disabled (open API, current default).
# When set, every /api endpoint (except /api/health) requires it.
API_KEY: str = os.getenv("API_KEY", "")
# Reject scan targets whose range is larger than this many addresses
# (default 65536 = a /16). Guards against accidentally scanning, e.g., a /8.
MAX_TARGET_ADDRESSES: int = int(os.getenv("MAX_TARGET_ADDRESSES", "65536"))
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
DATA_DIR: Path = Path(os.getenv("DATA_DIR", "/data" if os.path.exists("/data") else "."))
