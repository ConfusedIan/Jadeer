import requests
from fastapi import Request, Response
from core.exceptions import BadGatewayError
from config import REQUEST_TIMEOUT_SECONDS

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}

def _filtered_headers(headers: dict) -> dict:
    return {k: v for k, v in headers.items() if k.lower() not in HOP_BY_HOP_HEADERS}

def forward_request(
    request: Request,
    target_url: str,
    body: bytes | None,
) -> Response:
    try:
        res = requests.request(
            method=request.method,
            url=target_url,
            headers=_filtered_headers(dict(request.headers)),
            params=dict(request.query_params),
            data=body,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        return Response(
            content=res.content,
            status_code=res.status_code,
            headers=_filtered_headers(dict(res.headers)),
            media_type=res.headers.get("content-type"),
        )
    except requests.RequestException as e:
        raise BadGatewayError(f"Upstream request failed: {str(e)}")
