"""Bounded readiness wait for CI; no remote access or sleep longer than one second."""

import time
from urllib.error import URLError
from urllib.request import urlopen

for _ in range(60):
    try:
        with urlopen("http://127.0.0.1:8000/ready", timeout=2) as api:
            assert api.status == 200
        with urlopen("http://127.0.0.1:3000", timeout=2) as web:
            assert web.status == 200
        print("RefiLens web and API are ready.")
        break
    except (URLError, OSError, AssertionError):
        time.sleep(1)
else:
    raise SystemExit("RefiLens did not become ready within the bounded startup wait.")
