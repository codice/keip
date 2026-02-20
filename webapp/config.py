from starlette.config import Config

cfg = Config(".env")

# Server
DEBUG = cfg("DEBUG", cast=bool, default=False)

# Comma-separated list of origin URLs (e.g. "http://localhost:8123,https://www.example.com")
CORS_ALLOWED_ORIGINS = cfg("CORS_ALLOWED_ORIGINS", cast=str, default="")

# Application
INTEGRATION_CONTAINER_IMAGE = cfg(
    "INTEGRATION_IMAGE", cast=str, default="keip-integration"
)
