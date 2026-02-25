"""
Data models using dataclasses. All resume entities are defined here.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Experience:
    job_title: str = ""
    company: str = ""
    start_date: str = ""
    end_date: str = ""
    description: str = ""


@dataclass
class Education:
    degree: str = ""
    institution: str = ""
    start_date: str = ""
    end_date: str = ""
    description: str = ""


@dataclass
class Project:
    name: str = ""
    role: str = ""
    technologies: str = ""
    start_date: str = ""
    end_date: str = ""
    description: str = ""
    link: str = ""


@dataclass
class Certification:
    name: str = ""
    issuer: str = ""
    date: str = ""
    link: str = ""


@dataclass
class Language:
    name: str = ""
    proficiency: str = "Fluent"  # Basic, Conversational, Professional, Native


@dataclass
class Reference:
    name: str = ""
    title: str = ""
    company: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""


@dataclass
class Achievement:
    title: str = ""
    subtitle: str = ""  # e.g., "Best Manager - 2020"
    description: str = ""


@dataclass
class Resume:
    # Metadata
    id: Optional[int] = None
    title: str = ""
    created: datetime = field(default_factory=datetime.now)
    updated: datetime = field(default_factory=datetime.now)

    # Personal
    full_name: str = ""
    profile_title: str = ""
    email: str = ""
    phone: str = ""
    city: str = ""
    address: str = ""
    summary: str = ""
    profile_pic: Optional[bytes] = None  # stored as BLOB

    # Social
    linkedin: str = ""
    github: str = ""
    twitter: str = ""
    website: str = ""
    qr_link: str = ""

    # Sections
    experiences: List[Experience] = field(default_factory=list)
    educations: List[Education] = field(default_factory=list)
    projects: List[Project] = field(default_factory=list)
    certifications: List[Certification] = field(default_factory=list)
    languages: List[Language] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    achievements: List[Achievement] = field(default_factory=list)
    references: List[Reference] = field(default_factory=list)
    custom_sections: List[dict] = field(default_factory=list)
