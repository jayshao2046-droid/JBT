from __future__ import annotations

if __package__:
    from .api.app import app, create_app
    from .core.settings import get_settings
else:
    from api.app import app, create_app
    from core.settings import get_settings

__all__ = ["app", "create_app"]


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(app, host="0.0.0.0", port=settings.service_port)