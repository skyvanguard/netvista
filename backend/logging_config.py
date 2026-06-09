from __future__ import annotations

import logging

from config import LOG_LEVEL


def setup_logging() -> None:
    """Configure root logging once at startup.

    `force=True` overrides uvicorn's default handler so our `netvista.*`
    loggers emit with a consistent format and the configured level.
    """
    logging.basicConfig(
        level=LOG_LEVEL.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        force=True,
    )
