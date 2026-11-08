"""Launch the local application with environment-configured port and loopback binding."""

import uvicorn

from .api import create_app
from .config import Settings


def main() -> None:
    """Serve the backend and built frontend on one local origin."""
    settings = Settings()
    uvicorn.run(
        create_app(settings),
        host="127.0.0.1",
        port=settings.backend_port,
        log_level="warning",
        access_log=False,
    )


if __name__ == "__main__":
    main()
