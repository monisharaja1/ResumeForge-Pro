"""
Entry point for ResumeBuilder.
Initialises database and launches the GUI.
"""
from database import Database
from ui import ResumeApp


def main():
    db = Database("resume.db")
    app = ResumeApp(db)
    app.run()


if __name__ == "__main__":
    main()
