import hashlib
import json
import re
import time
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx


class SECError(RuntimeError):
    pass


def read_preserved(cache: Path, url: str, sha256: str) -> bytes:
    """Resolve immutable evidence first, retaining compatibility with older URL caches."""
    if not re.fullmatch(r"[a-f0-9]{64}", sha256):
        raise SECError("Invalid preserved response hash.")
    for path in (cache / "raw" / f"{sha256}.raw", cache / f"{hashlib.sha256(url.encode()).hexdigest()}.raw"):
        if path.exists():
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() == sha256:
                return raw
    raise SECError("Original response bytes for this source manifest are unavailable or fail their hash check.")


class SECClient:
    """Synchronous CLI client; shared process lock enforces <= 2 requests/sec across imports."""

    def __init__(self, user_agent: str, cache: Path, *, transport=None, ttl_seconds=86400):
        if not re.fullmatch(r"RefiLens/[^\s]+ contact: [^\s@]+@[^\s@]+\.[^\s@]+", user_agent):
            raise SECError("Set SEC_USER_AGENT to RefiLens/0.1 contact: your-real-email. No requests made.")
        self.cache = cache
        self.cache.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl_seconds
        self.http = httpx.Client(headers={"User-Agent": user_agent}, timeout=30, transport=transport)
        self.manifest: dict[str, dict] = {}

    def close(self):
        self.http.close()

    def _preserve(self, raw: bytes) -> None:
        directory = self.cache / "raw"
        directory.mkdir(exist_ok=True)
        path = directory / f"{hashlib.sha256(raw).hexdigest()}.raw"
        if not path.exists():
            path.write_bytes(raw)
        elif path.read_bytes() != raw:
            raise SECError("Immutable raw-evidence archive hash check failed.")

    def get(self, url: str) -> bytes:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname not in {"www.sec.gov", "data.sec.gov"}:
            raise SECError("SEC client only permits official HTTPS SEC hosts.")
        key = hashlib.sha256(url.encode()).hexdigest()
        raw_path, meta_path = self.cache / f"{key}.raw", self.cache / f"{key}.json"
        if raw_path.exists() and meta_path.exists():
            meta = json.loads(meta_path.read_text())
            age = datetime.now(UTC).timestamp() - datetime.fromisoformat(meta["retrieved_at"]).timestamp()
            raw = raw_path.read_bytes()
            if hashlib.sha256(raw).hexdigest() == meta["sha256"]:
                self._preserve(raw)
            if age <= self.ttl and hashlib.sha256(raw).hexdigest() == meta["sha256"]:
                self.manifest[url] = {**meta, "cache_hit": True}
                return raw
        for attempt in range(3):
            self._throttle()
            try:
                response = self.http.get(url)
            except httpx.TransportError as exc:
                if attempt == 2:
                    raise SECError("SEC network request failed after retries.") from exc
                time.sleep(2**attempt)
                continue
            if response.status_code == 403:
                raise SECError("SEC returned 403. Import stopped; do not bypass access restrictions.")
            if response.status_code == 429 or response.status_code >= 500:
                if attempt < 2:
                    retry = response.headers.get("Retry-After", "")
                    delay = float(2**attempt)
                    if retry.isdigit():
                        delay = max(delay, int(retry))
                    elif retry:
                        try:
                            delay = max(
                                delay, (parsedate_to_datetime(retry) - datetime.now(UTC)).total_seconds()
                            )
                        except (TypeError, ValueError):
                            pass
                    if delay > 30:
                        raise SECError(
                            "SEC requested a longer cooldown. Import stopped; retry after the published Retry-After time."
                        )
                    time.sleep(delay)
                    continue
                raise SECError(f"SEC returned {response.status_code} after retries.")
            if response.status_code != 200:
                raise SECError(f"SEC returned HTTP {response.status_code}.")
            raw = response.content
            meta = {
                "url": url,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "retrieved_at": datetime.now(UTC).isoformat(),
                "bytes": len(raw),
            }
            self._preserve(raw)
            raw_path.write_bytes(raw)
            meta_path.write_text(json.dumps(meta, indent=2))
            self.manifest[url] = {**meta, "cache_hit": False}
            return raw
        raise SECError("SEC request failed.")

    def _throttle(self):
        # fcntl also serializes concurrent CLI processes on this local Unix workspace.
        import fcntl

        with (self.cache / "request.lock").open("a+") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            lock.seek(0)
            previous = lock.read().strip()
            delay = max(0, 0.55 - (time.time() - float(previous or 0)))
            time.sleep(delay)
            lock.seek(0)
            lock.truncate()
            lock.write(str(time.time()))
            lock.flush()
            fcntl.flock(lock, fcntl.LOCK_UN)
