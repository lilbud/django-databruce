# Performance & Startup
preload_app = True          # CRITICAL: Loads code once, saving RAM and start time
workers = 2                 # Perfect for 1 vCPU
threads = 2
worker_class = 'gthread'
worker_connections = 500

# Connection & Timeout
bind = "unix:/run/gunicorn.sock"
timeout = 30
keepalive = 2
graceful_timeout = 10       # Don't let old workers hang for 30s during restart

# Resource Management
max_requests = 500          # Lowered: cycles workers more often to clear RAM
max_requests_jitter = 50
capture_output = True
loglevel = "info"

# Logging
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
