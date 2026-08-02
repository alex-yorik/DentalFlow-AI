import os
import sys
import urllib.request

host = os.environ.get("WEB_HOST", "localhost")
port = os.environ.get("WEB_PORT", "8080")
url = f"http://{host}:{port}/health"

try:
    with urllib.request.urlopen(url) as response:
        if response.status != 200:
            sys.exit(1)
except Exception:
    sys.exit(1)