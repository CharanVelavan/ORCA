#!/usr/bin/env python3
import time
import urllib.request
import json
import sys

URL = "http://localhost:8000/v1/models"
MAX_WAIT_SEC = 3600  # 60 minutes
INTERVAL_SEC = 30

start = time.time()
print(f"Polling {URL} every {INTERVAL_SEC}s (max {MAX_WAIT_SEC}s)...")

while time.time() - start < MAX_WAIT_SEC:
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "AtlasTester/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                body = resp.read().decode("utf-8")
                data = json.loads(body)
                print("Model endpoint is UP!")
                print(json.dumps(data, indent=2))
                sys.exit(0)
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
        except Exception:
            err_body = str(e)
        print(f"[{int(time.time() - start)}s] HTTP {e.code}: {err_body}")
    except Exception as e:
        print(f"[{int(time.time() - start)}s] Connection error: {e}")
    time.sleep(INTERVAL_SEC)

print("Timed out after 60 minutes.")
sys.exit(1)
