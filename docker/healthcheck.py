import os
import sys
import urllib.request

host = os.environ.get("WEB_HOST", "localhost")
port = os.environ.get("WEB_PORT", "8080")
path = os.environ.get("HEALTH_PATH", "/health")
url = f"http://{host}:{port}{path}"

try:
    with urllib.request.urlopen(url) as response:
        if response.status != 200:
            sys.exit(1)
except Exception:
    sys.exit(1)