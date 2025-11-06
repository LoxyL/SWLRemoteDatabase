from __future__ import annotations

import json
from typing import Any, Dict

from urllib import request


def _join(base: str, path: str) -> str:
    base = base.rstrip("/")
    path = path if path.startswith("/") else "/" + path
    return base + path


def health_check(api_base: str, timeout_s: int = 10) -> Dict[str, Any]:
    url = _join(api_base, "/v1/health")
    with request.urlopen(url, timeout=timeout_s) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data


def post_json(api_base: str, path: str, payload: Any, timeout_s: int = 60) -> Any:
    url = _join(api_base, path)
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with request.urlopen(req, timeout=timeout_s) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else {}


