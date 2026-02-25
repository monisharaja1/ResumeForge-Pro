"""
Database layer using SQLite with migration support.
Follows Repository pattern for each entity.
"""
import sqlite3
import json
from contextlib import contextmanager
from typing import List, Optional
from datetime import datetime
from models import (
    Resume,
    Experience,
    Education,
    Project,
    Certification,
    Language,
    Achievement,
    Reference,
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path="resume.db"):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def connect(self):
        """Provide a transactional scope."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Create tables if they don't exist (with migration support)."""
        with self.connect() as conn:
            # Resume master
            conn.execute("""
                CREATE TABLE IF NOT EXISTS resumes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    full_name TEXT,
                    profile_title TEXT,
                    email TEXT,
                    phone TEXT,
                    city TEXT,
                    address TEXT,
                    summary TEXT,
                    profile_pic BLOB,
                    linkedin TEXT,
                    github TEXT,
                    twitter TEXT,
                    website TEXT,
                    qr_link TEXT,
                    custom_sections TEXT,
                    created TIMESTAMP,
                    updated TIMESTAMP
                )
            """)

            # Experiences
            conn.execute("""
                CREATE TABLE IF NOT EXISTS experiences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resume_id INTEGER NOT NULL,
                    job_title TEXT,
                    company TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    description TEXT,
                    sort_order INTEGER,
                    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
                )
            """)

            # Educations
            conn.execute("""
                CREATE TABLE IF NOT EXISTS educations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resume_id INTEGER NOT NULL,
                    degree TEXT,
                    institution TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    description TEXT,
                    sort_order INTEGER,
                    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
                )
            """)

            # Projects
            conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resume_id INTEGER NOT NULL,
                    name TEXT,
                    role TEXT,
                    technologies TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    description TEXT,
                    link TEXT,
                    sort_order INTEGER,
                    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
                )
            """)

            # Certifications
            conn.execute("""
                CREATE TABLE IF NOT EXISTS certifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resume_id INTEGER NOT NULL,
                    name TEXT,
                    issuer TEXT,
                    date TEXT,
                    link TEXT,
                    sort_order INTEGER,
                    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
                )
            """)

            # Languages
            conn.execute("""
                CREATE TABLE IF NOT EXISTS languages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resume_id INTEGER NOT NULL,
                    name TEXT,
                    proficiency TEXT,
                    sort_order INTEGER,
                    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
                )
            """)

            # Skills (simple list)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resume_id INTEGER NOT NULL,
                    skill_name TEXT,
                    sort_order INTEGER,
                    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
                )
            """)

            # Achievements
            conn.execute("""
                CREATE TABLE IF NOT EXISTS achievements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resume_id INTEGER NOT NULL,
                    title TEXT,
                    subtitle TEXT,
                    description TEXT,
                    sort_order INTEGER,
                    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
                )
            """)

            # References
            conn.execute("""
                CREATE TABLE IF NOT EXISTS "references" (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resume_id INTEGER NOT NULL,
                    name TEXT,
                    title TEXT,
                    company TEXT,
                    phone TEXT,
                    email TEXT,
                    website TEXT,
                    sort_order INTEGER,
                    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
                )
            """)

            # Migrations: bring older databases up to current schema.
            # resumes table
            self._migrate_add_column(conn, "resumes", "title", "TEXT")
            self._migrate_add_column(conn, "resumes", "address", "TEXT")
            self._migrate_add_column(conn, "resumes", "city", "TEXT")
            self._migrate_add_column(conn, "resumes", "profile_pic", "BLOB")
            self._migrate_add_column(conn, "resumes", "profile_title", "TEXT")
            self._migrate_add_column(conn, "resumes", "linkedin", "TEXT")
            self._migrate_add_column(conn, "resumes", "github", "TEXT")
            self._migrate_add_column(conn, "resumes", "twitter", "TEXT")
            self._migrate_add_column(conn, "resumes", "website", "TEXT")
            self._migrate_add_column(conn, "resumes", "qr_link", "TEXT")
            self._migrate_add_column(conn, "resumes", "custom_sections", "TEXT")

            # child tables
            self._migrate_add_column(conn, "experiences", "sort_order", "INTEGER")
            self._migrate_add_column(conn, "educations", "sort_order", "INTEGER")
            self._migrate_add_column(conn, "skills", "sort_order", "INTEGER")
            self._migrate_add_column(conn, "achievements", "sort_order", "INTEGER")
            self._migrate_add_column(conn, "references", "sort_order", "INTEGER")

    def _migrate_add_column(self, conn, table, column, col_type):
        """Add column if it doesn't exist."""
        quoted_table = f'"{table}"'
        cursor = conn.execute(f"PRAGMA table_info({quoted_table})")
        columns = [row[1] for row in cursor.fetchall()]
        if column not in columns:
            conn.execute(f"ALTER TABLE {quoted_table} ADD COLUMN {column} {col_type}")
            logger.info(f"Added column {column} to {table}")

    # ---------- CRUD for Resume ----------
    def save_resume(self, resume: Resume) -> int:
        """Insert or update a resume."""
        with self.connect() as conn:
            if resume.id is None:
                # Insert
                cursor = conn.execute("""
                    INSERT INTO resumes (
                        title, full_name, profile_title, email, phone, city, address, summary,
                        profile_pic, linkedin, github, twitter, website, qr_link, custom_sections,
                        created, updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    resume.title or resume.full_name,
                    resume.full_name, resume.profile_title, resume.email, resume.phone,
                    resume.city,
                    resume.address, resume.summary, resume.profile_pic,
                    resume.linkedin, resume.github, resume.twitter, resume.website,
                    resume.qr_link,
                    json.dumps(resume.custom_sections or []),
                    resume.created, resume.updated
                ))
                resume.id = cursor.lastrowid
            else:
                # Update
                conn.execute("""
                    UPDATE resumes SET
                        title=?, full_name=?, profile_title=?, email=?, phone=?, city=?, address=?,
                        summary=?, profile_pic=?, linkedin=?, github=?, twitter=?,
                        website=?, qr_link=?, custom_sections=?, updated=?
                    WHERE id=?
                """, (
                    resume.title or resume.full_name,
                    resume.full_name, resume.profile_title, resume.email, resume.phone,
                    resume.city,
                    resume.address, resume.summary, resume.profile_pic,
                    resume.linkedin, resume.github, resume.twitter, resume.website,
                    resume.qr_link,
                    json.dumps(resume.custom_sections or []),
                    resume.updated, resume.id
                ))
                # Delete existing child records
                conn.execute("DELETE FROM experiences WHERE resume_id=?", (resume.id,))
                conn.execute("DELETE FROM educations WHERE resume_id=?", (resume.id,))
                conn.execute("DELETE FROM projects WHERE resume_id=?", (resume.id,))
                conn.execute("DELETE FROM certifications WHERE resume_id=?", (resume.id,))
                conn.execute("DELETE FROM languages WHERE resume_id=?", (resume.id,))
                conn.execute("DELETE FROM skills WHERE resume_id=?", (resume.id,))
                conn.execute("DELETE FROM achievements WHERE resume_id=?", (resume.id,))
                conn.execute('DELETE FROM "references" WHERE resume_id=?', (resume.id,))

            # Insert child records with sort_order
            for idx, exp in enumerate(resume.experiences):
                conn.execute("""
                    INSERT INTO experiences (
                        resume_id, job_title, company, start_date, end_date,
                        description, sort_order
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (resume.id, exp.job_title, exp.company, exp.start_date,
                      exp.end_date, exp.description, idx))

            for idx, edu in enumerate(resume.educations):
                conn.execute("""
                    INSERT INTO educations (
                        resume_id, degree, institution, start_date, end_date,
                        description, sort_order
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (resume.id, edu.degree, edu.institution, edu.start_date,
                      edu.end_date, edu.description, idx))

            for idx, proj in enumerate(resume.projects):
                conn.execute("""
                    INSERT INTO projects (
                        resume_id, name, role, technologies, start_date, end_date,
                        description, link, sort_order
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (resume.id, proj.name, proj.role, proj.technologies,
                      proj.start_date, proj.end_date, proj.description,
                      proj.link, idx))

            for idx, cert in enumerate(resume.certifications):
                conn.execute("""
                    INSERT INTO certifications (
                        resume_id, name, issuer, date, link, sort_order
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (resume.id, cert.name, cert.issuer, cert.date,
                      cert.link, idx))

            for idx, lang in enumerate(resume.languages):
                conn.execute("""
                    INSERT INTO languages (
                        resume_id, name, proficiency, sort_order
                    ) VALUES (?, ?, ?, ?)
                """, (resume.id, lang.name, lang.proficiency, idx))

            for idx, skill in enumerate(resume.skills):
                conn.execute("""
                    INSERT INTO skills (
                        resume_id, skill_name, sort_order
                    ) VALUES (?, ?, ?)
                """, (resume.id, skill, idx))

            for idx, ach in enumerate(resume.achievements):
                conn.execute("""
                    INSERT INTO achievements (
                        resume_id, title, subtitle, description, sort_order
                    ) VALUES (?, ?, ?, ?, ?)
                """, (resume.id, ach.title, ach.subtitle, ach.description, idx))

            for idx, ref in enumerate(resume.references):
                conn.execute("""
                    INSERT INTO "references" (
                        resume_id, name, title, company, phone, email, website, sort_order
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    resume.id, ref.name, ref.title, ref.company, ref.phone, ref.email, ref.website, idx
                ))

            return resume.id

    def get_resume(self, resume_id: int) -> Optional[Resume]:
        """Load a complete resume by ID."""
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM resumes WHERE id=?", (resume_id,)).fetchone()
            if not row:
                return None

            resume = Resume(
                id=row['id'],
                title=row['title'],
                created=datetime.fromisoformat(row['created']) if row['created'] else datetime.now(),
                updated=datetime.fromisoformat(row['updated']) if row['updated'] else datetime.now(),
                full_name=row['full_name'] or "",
                profile_title=row['profile_title'] or "",
                email=row['email'] or "",
                phone=row['phone'] or "",
                city=row['city'] or "",
                address=row['address'] or "",
                summary=row['summary'] or "",
                profile_pic=row['profile_pic'],
                linkedin=row['linkedin'] or "",
                github=row['github'] or "",
                twitter=row['twitter'] or "",
                website=row['website'] or "",
                qr_link=row['qr_link'] or "",
                custom_sections=json.loads(row['custom_sections']) if row['custom_sections'] else []
            )

            # Load experiences
            rows = conn.execute("""
                SELECT * FROM experiences WHERE resume_id=? ORDER BY sort_order
            """, (resume_id,)).fetchall()
            resume.experiences = [
                Experience(
                    job_title=r['job_title'] or "",
                    company=r['company'] or "",
                    start_date=r['start_date'] or "",
                    end_date=r['end_date'] or "",
                    description=r['description'] or ""
                ) for r in rows
            ]

            # Load educations
            rows = conn.execute("""
                SELECT * FROM educations WHERE resume_id=? ORDER BY sort_order
            """, (resume_id,)).fetchall()
            resume.educations = [
                Education(
                    degree=r['degree'] or "",
                    institution=r['institution'] or "",
                    start_date=r['start_date'] or "",
                    end_date=r['end_date'] or "",
                    description=r['description'] or ""
                ) for r in rows
            ]

            # Load projects
            rows = conn.execute("""
                SELECT * FROM projects WHERE resume_id=? ORDER BY sort_order
            """, (resume_id,)).fetchall()
            resume.projects = [
                Project(
                    name=r['name'] or "",
                    role=r['role'] or "",
                    technologies=r['technologies'] or "",
                    start_date=r['start_date'] or "",
                    end_date=r['end_date'] or "",
                    description=r['description'] or "",
                    link=r['link'] or ""
                ) for r in rows
            ]

            # Load certifications
            rows = conn.execute("""
                SELECT * FROM certifications WHERE resume_id=? ORDER BY sort_order
            """, (resume_id,)).fetchall()
            resume.certifications = [
                Certification(
                    name=r['name'] or "",
                    issuer=r['issuer'] or "",
                    date=r['date'] or "",
                    link=r['link'] or ""
                ) for r in rows
            ]

            # Load languages
            rows = conn.execute("""
                SELECT * FROM languages WHERE resume_id=? ORDER BY sort_order
            """, (resume_id,)).fetchall()
            resume.languages = [
                Language(
                    name=r['name'] or "",
                    proficiency=r['proficiency'] or "Fluent"
                ) for r in rows
            ]

            # Load skills
            rows = conn.execute("""
                SELECT skill_name FROM skills WHERE resume_id=? ORDER BY sort_order
            """, (resume_id,)).fetchall()
            resume.skills = [r['skill_name'] for r in rows if r['skill_name']]

            # Load achievements
            rows = conn.execute("""
                SELECT * FROM achievements WHERE resume_id=? ORDER BY sort_order
            """, (resume_id,)).fetchall()
            resume.achievements = [
                Achievement(
                    title=r['title'] or "",
                    subtitle=r['subtitle'] or "",
                    description=r['description'] or ""
                ) for r in rows
            ]

            # Load references
            rows = conn.execute("""
                SELECT * FROM "references" WHERE resume_id=? ORDER BY sort_order
            """, (resume_id,)).fetchall()
            resume.references = [
                Reference(
                    name=r['name'] or "",
                    title=r['title'] or "",
                    company=r['company'] or "",
                    phone=r['phone'] or "",
                    email=r['email'] or "",
                    website=r['website'] or ""
                ) for r in rows
            ]

            return resume

    def get_all_resumes(self) -> List[dict]:
        """Return list of resume summaries for the list view."""
        with self.connect() as conn:
            rows = conn.execute("""
                SELECT id, title, full_name, updated
                FROM resumes ORDER BY updated DESC
            """).fetchall()
            result = []
            for row in rows:
                item = dict(row)
                item["title"] = item.get("title") or item.get("full_name") or "Untitled"
                item["updated"] = item.get("updated") or ""
                result.append(item)
            return result

    def delete_resume(self, resume_id: int):
        """Delete a resume (cascade)."""
        with self.connect() as conn:
            conn.execute("DELETE FROM resumes WHERE id=?", (resume_id,))

    # ---------- Compatibility helpers for dict-based UI ----------
    def _resume_to_dict(self, resume: Resume) -> dict:
        """Convert Resume model to dict expected by the simpler UI layer."""
        if not resume:
            return {}
        return {
            "id": resume.id,
            "full_name": resume.full_name,
            "profile_title": resume.profile_title,
            "email": resume.email,
            "phone": resume.phone,
            "city": resume.city,
            "qr_link": resume.qr_link,
            "summary": resume.summary,
            "experiences": [e.__dict__ for e in resume.experiences],
            "educations": [e.__dict__ for e in resume.educations],
            "skills": list(resume.skills),
            "achievements": [a.__dict__ for a in resume.achievements],
            "references": [r.__dict__ for r in resume.references],
            "custom_sections": list(resume.custom_sections or []),
            "updated": resume.updated.isoformat() if resume.updated else ""
        }

    def _dict_to_resume(self, data: dict, resume_id: Optional[int] = None) -> Resume:
        """Convert dict payload from simpler UI into Resume model."""
        resume = Resume(
            id=resume_id,
            title=(data.get("full_name") or "Untitled").strip(),
            full_name=(data.get("full_name") or "").strip(),
            profile_title=(data.get("profile_title") or "").strip(),
            email=(data.get("email") or "").strip(),
            phone=(data.get("phone") or "").strip(),
            city=(data.get("city") or "").strip(),
            qr_link=(data.get("qr_link") or "").strip(),
            summary=(data.get("summary") or "").strip(),
            updated=datetime.now()
        )
        resume.experiences = [Experience(**item) for item in data.get("experiences", [])]
        resume.educations = [Education(**item) for item in data.get("educations", [])]
        resume.skills = list(data.get("skills", []))
        resume.achievements = [Achievement(**item) for item in data.get("achievements", [])]
        resume.references = [Reference(**item) for item in data.get("references", [])]
        resume.custom_sections = list(data.get("custom_sections", []))
        return resume

    def create_resume(self, data: dict) -> int:
        """Compatibility API for dict-based UI: create and return resume id."""
        resume = self._dict_to_resume(data)
        return self.save_resume(resume)

    def update_resume(self, resume_id: int, data: dict):
        """Compatibility API for dict-based UI: update an existing resume."""
        resume = self._dict_to_resume(data, resume_id=resume_id)
        self.save_resume(resume)

    def get_resume_data(self, resume_id: int) -> Optional[dict]:
        """Compatibility API for dict-based UI: fetch a resume as dict."""
        resume = self.get_resume(resume_id)
        if not resume:
            return None
        return self._resume_to_dict(resume)
