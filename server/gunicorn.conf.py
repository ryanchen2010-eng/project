"""Conservative single-instance settings for the password-protected beta.

TLS termination and HTTP-to-HTTPS redirect belong to the hosting ingress.
Do not expose the old loopback development HTTP server to the internet.
"""

import os

trial_port = int(os.environ.get("PORT", "10000"))
if not 1024 <= trial_port <= 65535:
    raise ValueError("PORT must be an unprivileged TCP port.")

bind = f"0.0.0.0:{trial_port}"
workers = 1
# A sync worker gives timeout a real worker-restart bound for a stuck native
# chemistry call. A gthread heartbeat is NOT a per-request wall-clock limit.
# One worker also keeps the gateway's process-local budgets consistent.
worker_class = "sync"
threads = 1
timeout = 90
graceful_timeout = 30
keepalive = 5
preload_app = True
max_requests = 500
max_requests_jitter = 50
# Do not log URLs, search terms, drawings, credentials, or cookie values.
accesslog = None
errorlog = "-"
loglevel = "warning"
