"""Single-process abuse controls. Use shared ingress limits before scaling workers."""
import time
import asyncio
import threading
from collections import OrderedDict
from fastapi import Depends, HTTPException
from starlette.responses import JSONResponse
from app.deps import get_current_user

class WindowLimiter:
    def __init__(self, limit=20, window=60, max_keys=4096):
        self.limit, self.window, self.max_keys = limit, window, max_keys
        self.entries = OrderedDict()
        self.lock = threading.Lock()

    def allow(self, key):
        now = time.monotonic()
        with self.lock:
            # Entries are insertion ordered, so expired entries can be removed cheaply.
            while self.entries and next(iter(self.entries.values()))[0] <= now - self.window:
                self.entries.popitem(last=False)
            started, count = self.entries.get(key, (now, 0))
            if count >= self.limit or (key not in self.entries and len(self.entries) >= self.max_keys):
                return False
            self.entries[key] = (started, count + 1)
            return True

class RequestLimitsMiddleware:
    def __init__(self, app, auth_limit=30):
        self.app = app
        self.auth = WindowLimiter(auth_limit)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        path = scope.get("path", "")
        async def reject(code, detail):
            await JSONResponse({"detail": detail}, status_code=code,
                               headers={"Retry-After": "60"} if code == 429 else {})(scope, receive, send)
        if scope["method"] == "POST" and path in ("/api/v1/auth/login", "/api/v1/auth/register"):
            # Never trust attacker-supplied forwarding headers here.
            peer = scope.get("client") or ("unknown", 0)
            if not self.auth.allow(peer[0]):
                return await reject(429, "Too many authentication attempts. Retry in a minute.")
        if scope["method"] in ("POST", "PUT", "PATCH"):
            limit = 6 * 1024 * 1024 if path.startswith("/api/v1/resume/") else 64 * 1024
            chunks, size = [], 0
            deadline = time.monotonic() + 20
            while True:
                try:
                    message = await asyncio.wait_for(receive(), timeout=max(0.001, deadline - time.monotonic()))
                except asyncio.TimeoutError:
                    return await reject(408, "Request body timed out.")
                if message["type"] == "http.disconnect":
                    return
                size += len(message.get("body", b""))
                if size > limit:
                    return await reject(413, "Request body is too large.")
                if message.get("body"):
                    chunks.append(message["body"])
                if not message.get("more_body", False):
                    break
            consumed = False
            async def bounded_receive():
                nonlocal consumed
                if consumed:
                    return await receive()
                consumed = True
                return {"type": "http.request", "body": b"".join(chunks), "more_body": False}
            return await self.app(scope, bounded_receive, send)
        await self.app(scope, receive, send)

_expensive = WindowLimiter(limit=12)
_slots = threading.BoundedSemaphore(2)
_active_users = set()
_active_lock = threading.Lock()

def expensive_request(user=Depends(get_current_user)):
    if not _expensive.allow(user.id):
        raise HTTPException(429, "Too many processing requests. Retry in a minute.", headers={"Retry-After": "60"})
    with _active_lock:
        if user.id in _active_users:
            raise HTTPException(409, "Another processing request is active for this account.")
        _active_users.add(user.id)
    if not _slots.acquire(blocking=False):
        with _active_lock:
            _active_users.discard(user.id)
        raise HTTPException(503, "Processing is busy. Please retry shortly.")
    try:
        yield
    finally:
        _slots.release()
        with _active_lock:
            _active_users.discard(user.id)
