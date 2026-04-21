"""HTTP helpers that work in both desktop Python and pygbag/Emscripten.

Why this module exists
----------------------
Pygame-CE in the browser runs under Emscripten, where the usual
``urllib.request`` stack is unreliable -- blocking sockets are not
implemented, and calls from deep inside gameplay code tend to raise
exception types that were never part of the desktop catch list
(``NotImplementedError``, ``AttributeError`` from the socket shim, etc.).

Instead of papering over that at every call site, every browser-bound HTTP
request in the game funnels through this module.  Two usage patterns are
supported:

* ``fetch_json`` / ``post_json`` / ``request_json``
    Synchronous, best-effort JSON calls.  On desktop they use ``urllib``.
    In the browser they use a synchronous ``XMLHttpRequest`` through
    ``platform.window`` so existing synchronous init code keeps working
    without a full async refactor.  These DO briefly block the caller,
    so use them only during setup / event-triggered actions, not every
    frame.

* ``request_json_async`` / ``fetch_json_async`` / ``post_json_async``
    Non-blocking coroutines that await ``platform.window.fetch`` in the
    browser (Promise-based, yields back to the render loop) and run
    urllib inside ``asyncio.to_thread`` on desktop.  Use these from
    gameplay code that runs once per frame so the canvas never stalls.

* ``kick_off_background_json``
    Fire-and-forget: schedules an async request and invokes a callback
    with the parsed result.  Ideal for periodic refreshes from a
    ``pygame.Sprite.update`` method where we don't want to turn every
    caller into a coroutine.

All helpers return ``dict``/``list``/``None`` and never raise -- network
failures simply return ``None`` so the game keeps running with local
state if the backend is unreachable.
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any, Callable, Mapping, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

IS_BROWSER = sys.platform == "emscripten"

JsonLike = Optional[Any]
ResultCallback = Callable[[JsonLike], None]

DEFAULT_TIMEOUT_SEC = 4.0


# ---------------------------------------------------------------------------
# Synchronous path
# ---------------------------------------------------------------------------

def browser_xhr_sync(
    method: str,
    url: str,
    body: Optional[Mapping[str, Any]] = None,
    headers: Optional[Mapping[str, str]] = None,
) -> JsonLike:
    """Issue a blocking XHR from pygbag and return parsed JSON or None.

    The browser forbids setting ``xhr.timeout`` on synchronous requests
    (it throws ``InvalidAccessError``) so we never try; callers that
    need a bounded wait should use ``request_json_async`` instead.
    """
    try:
        from platform import window  # type: ignore[import-not-found]
    except Exception as exc:
        print(f"[web_http] platform.window unavailable: {exc}")
        return None

    try:
        xhr = window.XMLHttpRequest.new()
        xhr.open(method.upper(), url, False)
        xhr.setRequestHeader("Content-Type", "application/json")
        xhr.setRequestHeader("Accept", "application/json")
        if headers:
            for key, value in headers.items():
                xhr.setRequestHeader(key, value)

        payload = json.dumps(dict(body)) if body is not None else None
        if payload is None:
            xhr.send()
        else:
            xhr.send(payload)

        status = int(getattr(xhr, "status", 0) or 0)
        if 200 <= status < 300:
            text = str(getattr(xhr, "responseText", "") or "")
            if not text:
                return None
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return None
        print(f"[web_http] {method} {url} -> HTTP {status}")
        return None
    except Exception as exc:
        print(f"[web_http] sync XHR failure for {method} {url}: {exc}")
        return None


def desktop_urlopen(
    method: str,
    url: str,
    body: Optional[Mapping[str, Any]] = None,
    headers: Optional[Mapping[str, str]] = None,
    timeout: float = DEFAULT_TIMEOUT_SEC,
) -> JsonLike:
    """Issue a desktop HTTP request via urllib; always returns dict/list/None."""
    data = json.dumps(dict(body)).encode("utf-8") if body is not None else None
    merged_headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if headers:
        merged_headers.update(headers)
    try:
        req = Request(url, data=data, headers=merged_headers, method=method.upper())
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            if not raw:
                return None
            return json.loads(raw)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[web_http] {method} {url} failed: {exc}")
        return None
    except Exception as exc:
        print(f"[web_http] {method} {url} unexpected error: {exc}")
        return None


def request_json(
    method: str,
    url: str,
    body: Optional[Mapping[str, Any]] = None,
    headers: Optional[Mapping[str, str]] = None,
    timeout: float = DEFAULT_TIMEOUT_SEC,
) -> JsonLike:
    """Cross-platform JSON request.  Returns parsed body or ``None``."""
    if IS_BROWSER:
        return browser_xhr_sync(method, url, body=body, headers=headers)
    return desktop_urlopen(method, url, body=body, headers=headers, timeout=timeout)


def fetch_json(url: str, timeout: float = DEFAULT_TIMEOUT_SEC) -> JsonLike:
    """Convenience blocking GET helper."""
    return request_json("GET", url, timeout=timeout)


def post_json(url: str, body: Mapping[str, Any], timeout: float = DEFAULT_TIMEOUT_SEC) -> JsonLike:
    """Convenience blocking POST helper with a JSON body."""
    return request_json("POST", url, body=body, timeout=timeout)


# ---------------------------------------------------------------------------
# Asynchronous / non-blocking path
# ---------------------------------------------------------------------------

async def browser_fetch_async(
    method: str,
    url: str,
    body: Optional[Mapping[str, Any]] = None,
    headers: Optional[Mapping[str, str]] = None,
    timeout: float = DEFAULT_TIMEOUT_SEC,
) -> JsonLike:
    """Non-blocking browser fetch that yields to the render loop.

    Uses ``platform.window.fetch`` (the standard browser Fetch API) and
    awaits its Promise directly -- pygbag's asyncio integration bridges
    JS Promises and Python awaits.  Options are passed as a JSON string
    that JavaScript parses into a real object, which sidesteps the
    Python<->JS object-conversion quirks in Emscripten.
    """
    try:
        from platform import window  # type: ignore[import-not-found]
    except Exception as exc:
        print(f"[web_http] platform.window unavailable: {exc}")
        return None

    # Build a fetch init object via JSON + JSON.parse on the JS side.
    init = {
        "method": method.upper(),
        "headers": {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **(dict(headers) if headers else {}),
        },
        "mode": "cors",
        "credentials": "omit",
        "cache": "no-store",
    }
    if body is not None:
        init["body"] = json.dumps(dict(body))

    try:
        parser = window.JSON.parse
        init_js = parser(json.dumps(init))
        response = await window.fetch(url, init_js)
        status = int(getattr(response, "status", 0) or 0)
        if not (200 <= status < 300):
            print(f"[web_http] async {method} {url} -> HTTP {status}")
            return None
        text_promise = response.text()
        text = await text_promise
        text_str = str(text) if text is not None else ""
        if not text_str:
            return None
        try:
            return json.loads(text_str)
        except json.JSONDecodeError:
            return None
    except Exception as exc:
        print(f"[web_http] async fetch failure for {method} {url}: {exc}")
        return None


async def request_json_async(
    method: str,
    url: str,
    body: Optional[Mapping[str, Any]] = None,
    headers: Optional[Mapping[str, str]] = None,
    timeout: float = DEFAULT_TIMEOUT_SEC,
) -> JsonLike:
    """Cross-platform non-blocking JSON request."""
    if IS_BROWSER:
        try:
            return await asyncio.wait_for(
                browser_fetch_async(method, url, body=body, headers=headers, timeout=timeout),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            print(f"[web_http] async {method} {url} timed out after {timeout}s")
            return None
        except Exception as exc:
            print(f"[web_http] async {method} {url} error: {exc}")
            return None

    # Desktop: run blocking urllib in a worker thread so the game loop
    # keeps drawing while the request is in flight.
    try:
        return await asyncio.to_thread(
            desktop_urlopen, method, url, body, headers, timeout
        )
    except Exception as exc:
        print(f"[web_http] desktop async {method} {url} error: {exc}")
        return None


async def fetch_json_async(url: str, timeout: float = DEFAULT_TIMEOUT_SEC) -> JsonLike:
    """Non-blocking GET helper."""
    return await request_json_async("GET", url, timeout=timeout)


async def post_json_async(
    url: str,
    body: Mapping[str, Any],
    timeout: float = DEFAULT_TIMEOUT_SEC,
) -> JsonLike:
    """Non-blocking POST helper."""
    return await request_json_async("POST", url, body=body, timeout=timeout)


# ---------------------------------------------------------------------------
# Fire-and-forget helper for frame-rate-sensitive callers
# ---------------------------------------------------------------------------

def kick_off_background_json(
    method: str,
    url: str,
    body: Optional[Mapping[str, Any]] = None,
    on_result: Optional[ResultCallback] = None,
    timeout: float = DEFAULT_TIMEOUT_SEC,
) -> bool:
    """Schedule an async request and invoke ``on_result`` when it completes.

    Returns True if the task was scheduled, False if no event loop was
    available (in which case the caller should fall back to the sync
    ``request_json``).  The callback runs with the parsed JSON body
    (or ``None`` on failure) and is never allowed to raise into the
    game loop.
    """
    async def runner() -> None:
        result = await request_json_async(method, url, body=body, timeout=timeout)
        if on_result is None:
            return
        try:
            on_result(result)
        except Exception as exc:
            print(f"[web_http] background callback error for {method} {url}: {exc}")

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is None:
        # No running loop (e.g. headless desktop script).  Execute
        # synchronously so we still produce a result.
        result = request_json(method, url, body=body, timeout=timeout)
        if on_result is not None:
            try:
                on_result(result)
            except Exception as exc:
                print(f"[web_http] sync callback error for {method} {url}: {exc}")
        return True

    try:
        loop.create_task(runner())
        return True
    except Exception as exc:
        print(f"[web_http] could not schedule background task for {method} {url}: {exc}")
        return False
