import uvicorn

from .core.settings import get_settings
from .api.app import app  # noqa: F401 — imported so uvicorn string reference resolves


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "src.api.app:app",
        host=settings.decision_host,
        port=settings.decision_port,
        workers=settings.decision_workers,
        log_level=settings.decision_log_level,
        reload=settings.decision_env == "development",
    )


if __name__ == "__main__":
    main()
