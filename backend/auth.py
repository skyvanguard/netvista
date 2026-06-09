from __future__ import annotations

from fastapi import Header, HTTPException, Query, status

from config import API_KEY


async def verify_api_key(
    x_api_key: str | None = Header(default=None),
    api_key: str | None = Query(default=None),
) -> None:
    """Reject the request unless a valid API key is supplied.

    No-op when API_KEY is unset (auth disabled). The key may arrive either in
    the `X-API-Key` header (REST/JSON calls) or the `api_key` query param
    (download links and the WebSocket, which can't set custom headers).
    """
    if not API_KEY:
        return
    provided = x_api_key or api_key
    if provided != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
