import hmac
import time
from collections import defaultdict, deque

from fastapi import APIRouter, HTTPException, Request, status

from .config import settings
from .schemas import LoginIn

router = APIRouter(prefix="/api/auth", tags=["auth"])

# The app is reachable from the internet through the tunnel, so throttle
# password guessing: at most MAX_FAILURES bad logins per client per window.
MAX_FAILURES = 5
WINDOW_SECONDS = 15 * 60
_failures: dict[str, deque[float]] = defaultdict(deque)


def _client_key(request: Request) -> str:
    # cloudflared forwards the real visitor IP in this header.
    return request.headers.get("cf-connecting-ip") or (
        request.client.host if request.client else "unknown"
    )


def _recent_failures(key: str) -> deque[float]:
    q = _failures[key]
    cutoff = time.monotonic() - WINDOW_SECONDS
    while q and q[0] < cutoff:
        q.popleft()
    return q


def require_user(request: Request) -> str:
    user = request.session.get("user")
    if user != settings.username:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed in")
    return user


@router.post("/login")
def login(body: LoginIn, request: Request):
    key = _client_key(request)
    failures = _recent_failures(key)
    if len(failures) >= MAX_FAILURES:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many attempts, try again later")

    ok_user = hmac.compare_digest(body.username.encode(), settings.username.encode())
    ok_pass = hmac.compare_digest(body.password.encode(), settings.password.encode())
    if not (ok_user and ok_pass):
        failures.append(time.monotonic())
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong username or password")

    failures.clear()
    request.session.clear()
    request.session["user"] = settings.username
    return {"username": settings.username, "owner_name": settings.owner_name}


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}


@router.get("/me")
def me(request: Request):
    user = require_user(request)
    return {"username": user, "owner_name": settings.owner_name}
