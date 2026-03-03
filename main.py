"""
Entry point for ResumeForge Pro.

Behavior:
- Desktop mode: launch the local GUI app.
- Web mode: if PORT is provided (PaaS runtime), start Flask server.
"""

import os


def _run_web_server() -> None:
    from app import app as flask_app

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    flask_app.run(host=host, port=port)


def _run_desktop_app() -> None:
    from database import Database
    from ui import ResumeApp

    db = Database("resume.db")
    desktop = ResumeApp(db)
    desktop.run()


def main() -> None:
    if os.getenv("PORT"):
        _run_web_server()
        return
    _run_desktop_app()


if __name__ == "__main__":
    main()
