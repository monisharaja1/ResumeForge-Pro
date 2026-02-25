"""
Utility functions: logging setup, dict conversion, image handling, etc.
"""
import json
import logging
import os
import base64
import io
from datetime import datetime
from typing import Dict, Any
from PIL import Image as PILImage
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

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger

def resume_to_dict(resume: Resume) -> Dict[str, Any]:
    """Convert Resume object to JSON-serializable dict."""
    return {
        "id": resume.id,
        "title": resume.title,
        "full_name": resume.full_name,
        "profile_title": resume.profile_title,
        "email": resume.email,
        "phone": resume.phone,
        "city": resume.city,
        "address": resume.address,
        "summary": resume.summary,
        "profile_pic": base64.b64encode(resume.profile_pic).decode("ascii") if resume.profile_pic else None,
        "linkedin": resume.linkedin,
        "github": resume.github,
        "twitter": resume.twitter,
        "website": resume.website,
        "qr_link": resume.qr_link,
        "experiences": [exp.__dict__ for exp in resume.experiences],
        "educations": [edu.__dict__ for edu in resume.educations],
        "projects": [proj.__dict__ for proj in resume.projects],
        "certifications": [cert.__dict__ for cert in resume.certifications],
        "languages": [lang.__dict__ for lang in resume.languages],
        "skills": resume.skills,
        "achievements": [ach.__dict__ for ach in resume.achievements],
        "references": [ref.__dict__ for ref in resume.references],
        "custom_sections": list(resume.custom_sections or []),
        "created": resume.created.isoformat() if resume.created else None,
        "updated": resume.updated.isoformat() if resume.updated else None
    }

def dict_to_resume(data: Dict[str, Any]) -> Resume:
    """Rebuild Resume object from dict."""
    def _safe_b64_decode(value: str) -> bytes:
        s = "".join(str(value or "").strip().split())
        if not s:
            return b""
        # Add missing padding if needed.
        pad = len(s) % 4
        if pad:
            s += "=" * (4 - pad)
        try:
            return base64.b64decode(s)
        except Exception:
            # Try urlsafe fallback
            return base64.urlsafe_b64decode(s)

    def _normalize_profile_pic(raw_bytes: bytes) -> bytes:
        try:
            with PILImage.open(io.BytesIO(raw_bytes)) as img:
                mode = img.mode or "RGB"
                if mode not in ("RGB", "RGBA"):
                    img = img.convert("RGB")
                out = io.BytesIO()
                img.save(out, format="PNG")
                return out.getvalue()
        except Exception:
            return raw_bytes

    # Handle binary data
    profile_pic = None
    if data.get("profile_pic"):
        pic_str = data["profile_pic"]
        if isinstance(pic_str, str):
            # Accept data URLs or plain base64
            if "," in pic_str:
                pic_str = pic_str.split(",", 1)[1]
            try:
                decoded = _safe_b64_decode(pic_str)
                profile_pic = _normalize_profile_pic(decoded) if decoded else None
            except Exception:
                profile_pic = None
    # ... convert each section
    resume = Resume(
        id=data.get("id"),
        title=data.get("title", ""),
        full_name=data.get("full_name", ""),
        profile_title=data.get("profile_title", ""),
        email=data.get("email", ""),
        phone=data.get("phone", ""),
        city=data.get("city", ""),
        address=data.get("address", ""),
        summary=data.get("summary", ""),
        profile_pic=profile_pic,
        linkedin=data.get("linkedin", ""),
        github=data.get("github", ""),
        twitter=data.get("twitter", ""),
        website=data.get("website", ""),
        qr_link=data.get("qr_link", ""),
        experiences=[Experience(**e) for e in data.get("experiences", [])],
        educations=[Education(**e) for e in data.get("educations", [])],
        projects=[Project(**p) for p in data.get("projects", [])],
        certifications=[Certification(**c) for c in data.get("certifications", [])],
        languages=[Language(**l) for l in data.get("languages", [])],
        skills=list(data.get("skills", [])),
        achievements=[Achievement(**a) for a in data.get("achievements", [])],
        references=[Reference(**r) for r in data.get("references", [])],
        custom_sections=list(data.get("custom_sections", [])),
        created=datetime.fromisoformat(data["created"]) if data.get("created") else None,
        updated=datetime.fromisoformat(data["updated"]) if data.get("updated") else None
    )
    return resume
