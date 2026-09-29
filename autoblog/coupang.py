"""Coupang Partners Open API: search products and return affiliate links.

Requires COUPANG_ACCESS_KEY / COUPANG_SECRET_KEY (issued in the Coupang Partners dashboard).
Without them, search_products() returns [] and posts are published without product cards.
"""
import hashlib
import hmac
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

API_HOST = "https://api-gateway.coupang.com"
SEARCH_PATH = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"


def _authorization(method: str, path: str, query: str, access_key: str, secret_key: str) -> str:
    signed_date = time.strftime("%y%m%dT%H%M%SZ", time.gmtime())
    message = signed_date + method + path + query
    signature = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).hexdigest()
    return (
        f"CEA algorithm=HmacSHA256, access-key={access_key}, "
        f"signed-date={signed_date}, signature={signature}"
    )


def search_products(keyword: str, limit: int = 3) -> list[dict]:
    access_key = os.environ.get("COUPANG_ACCESS_KEY")
    secret_key = os.environ.get("COUPANG_SECRET_KEY")
    if not (access_key and secret_key) or limit <= 0:
        return []

    query = urllib.parse.urlencode({"keyword": keyword, "limit": limit})
    req = urllib.request.Request(
        f"{API_HOST}{SEARCH_PATH}?{query}",
        headers={
            "Authorization": _authorization("GET", SEARCH_PATH, query, access_key, secret_key),
            "Content-Type": "application/json;charset=UTF-8",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.load(resp)
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        print(f"[coupang] search failed for {keyword!r}: {exc}")
        return []

    products = (payload.get("data") or {}).get("productData") or []
    return [
        {
            "name": p.get("productName", ""),
            "price": p.get("productPrice"),
            "image": p.get("productImage", ""),
            "url": p.get("productUrl", ""),
        }
        for p in products[:limit]
        if p.get("productUrl")
    ]
