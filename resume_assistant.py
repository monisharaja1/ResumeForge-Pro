"""
Lightweight ATS and tailoring utilities.
Supports deterministic offline heuristics and optional LLM-assisted outputs.
"""
from __future__ import annotations

import math
import json
import os
import re
import urllib.error
import urllib.request
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from models import Resume


STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "you", "your", "are", "from",
    "have", "has", "will", "can", "into", "about", "across", "using", "use",
    "our", "their", "they", "them", "his", "her", "its", "was", "were", "been",
    "being", "able", "such", "than", "then", "also", "all", "any", "per", "not",
    "job", "role", "work", "years", "year", "required", "preferred", "strong",
}

ACTION_VERBS = {
    "built", "designed", "developed", "implemented", "optimized", "created",
    "led", "managed", "launched", "automated", "improved", "delivered",
    "analyzed", "reduced", "increased", "migrated", "deployed", "tested",
}


def _tokenize(text: str) -> List[str]:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.\-/]{1,}", (text or "").lower())
    cleaned = []
    for t in tokens:
        if len(t) < 3:
            continue
        if t in STOPWORDS:
            continue
        cleaned.append(t)
    return cleaned


def _resume_text(resume: Resume) -> str:
    parts = [
        resume.full_name,
        resume.profile_title,
        resume.summary,
        " ".join(resume.skills or []),
        " ".join([
            f"{e.job_title} {e.company} {e.description}"
            for e in (resume.experiences or [])
        ]),
        " ".join([
            f"{p.name} {p.role} {p.technologies} {p.description}"
            for p in (resume.projects or [])
        ]),
        " ".join([f"{c.name} {c.issuer}" for c in (resume.certifications or [])]),
        " ".join([f"{e.degree} {e.institution}" for e in (resume.educations or [])]),
    ]
    return " ".join([p for p in parts if p])


def _extract_job_keywords(job_description: str, limit: int = 25) -> List[str]:
    freq = Counter(_tokenize(job_description))
    # Keep meaningful, frequent terms first.
    return [word for word, _ in freq.most_common(limit)]


def _tfidf_cosine_similarity(text_a: str, text_b: str) -> float:
    """
    Lightweight TF-IDF cosine similarity without external dependencies.
    Returns similarity in percentage [0, 100].
    """
    tokens_a = _tokenize(text_a)
    tokens_b = _tokenize(text_b)
    if not tokens_a or not tokens_b:
        return 0.0

    docs = [tokens_a, tokens_b]
    vocab = sorted(set(tokens_a) | set(tokens_b))
    if not vocab:
        return 0.0

    # Document frequency
    df = {}
    for term in vocab:
        df[term] = sum(1 for d in docs if term in d)

    n_docs = len(docs)
    vectors = []
    for doc in docs:
        counts = Counter(doc)
        total = float(sum(counts.values()) or 1.0)
        vec = {}
        for term in vocab:
            tf = counts.get(term, 0) / total
            # Smoothed IDF.
            idf = math.log((1 + n_docs) / (1 + df.get(term, 0))) + 1.0
            vec[term] = tf * idf
        vectors.append(vec)

    a, b = vectors
    dot = sum(a[t] * b[t] for t in vocab)
    norm_a = math.sqrt(sum((a[t] ** 2) for t in vocab))
    norm_b = math.sqrt(sum((b[t] ** 2) for t in vocab))
    if norm_a <= 0 or norm_b <= 0:
        return 0.0
    return max(0.0, min(100.0, (dot / (norm_a * norm_b)) * 100.0))


def analyze_ats(resume: Resume, job_description: str) -> Dict[str, object]:
    jd_keywords = _extract_job_keywords(job_description)
    resume_text = _resume_text(resume)
    resume_tokens = set(_tokenize(resume_text))
    if not jd_keywords:
        return {
            "score": 0,
            "matched_keywords": [],
            "missing_keywords": [],
            "suggestions": ["Paste a job description to compute ATS score."],
            "section_scores": {},
            "section_advice": [],
            "text_similarity": 0,
            "algorithm": "keyword+tfidf_cosine",
        }

    matched = [k for k in jd_keywords if k in resume_tokens]
    missing = [k for k in jd_keywords if k not in resume_tokens]

    base_score = int((len(matched) / max(1, len(jd_keywords))) * 100)
    section_bonus = 0
    if resume.summary.strip():
        section_bonus += 5
    if resume.experiences:
        section_bonus += 5
    if resume.skills:
        section_bonus += 5
    tfidf_similarity = _tfidf_cosine_similarity(resume_text, job_description)
    # Blend keyword coverage and semantic text overlap.
    blended = int((0.65 * (base_score + section_bonus)) + (0.35 * tfidf_similarity))
    score = min(100, max(0, blended))

    suggestions: List[str] = []
    if missing:
        suggestions.append(
            "Add missing keywords in summary/skills: " + ", ".join(missing[:8])
        )
    if len(resume.experiences) < 2:
        suggestions.append("Add more experience entries with measurable outcomes.")
    if not any(re.search(r"\d|%|\$|x", (e.description or "")) for e in resume.experiences):
        suggestions.append("Include metrics in experience bullets (e.g., %, $, time saved).")
    if not resume.skills:
        suggestions.append("Add a skills section aligned to the job description.")
    if not suggestions:
        suggestions.append("Good alignment. Fine-tune wording to mirror job description phrasing.")

    # ATS v2: section-wise scoring for clearer guidance.
    section_texts = {
        "summary": resume.summary or "",
        "skills": " ".join(resume.skills or []),
        "experience": " ".join([f"{e.job_title} {e.company} {e.description}" for e in (resume.experiences or [])]),
        "projects": " ".join([f"{p.name} {p.role} {p.technologies} {p.description}" for p in (resume.projects or [])]),
    }
    section_scores: Dict[str, int] = {}
    for section, text in section_texts.items():
        tokens = set(_tokenize(text))
        if not jd_keywords:
            section_scores[section] = 0
            continue
        section_scores[section] = int((len([k for k in jd_keywords if k in tokens]) / len(jd_keywords)) * 100)

    section_advice: List[str] = []
    if section_scores.get("summary", 0) < 35:
        section_advice.append("Summary alignment is low; add role-specific keywords to first 2 lines.")
    if section_scores.get("skills", 0) < 45:
        section_advice.append("Skills section misses JD terms; include exact tool/stack keywords.")
    if section_scores.get("experience", 0) < 40:
        section_advice.append("Experience bullets should mirror JD verbs and include metrics.")
    if section_scores.get("projects", 0) < 30:
        section_advice.append("Projects can improve ATS relevance; add tech stack and outcomes.")
    if not section_advice:
        section_advice.append("Section alignment looks balanced. Focus on concise measurable bullets.")

    return {
        "score": score,
        "matched_keywords": matched,
        "missing_keywords": missing[:15],
        "suggestions": suggestions,
        "section_scores": section_scores,
        "section_advice": section_advice,
        "text_similarity": int(round(tfidf_similarity)),
        "algorithm": "keyword+tfidf_cosine",
    }


def _build_template_features(resume: Resume, job_description: str) -> Dict[str, float]:
    role = (resume.profile_title or "").lower()
    skills = [s.lower() for s in (resume.skills or [])]
    jd = (job_description or "").lower()
    exp_count = len(resume.experiences or [])
    project_count = len(resume.projects or [])
    cert_count = len(resume.certifications or [])

    return {
        "is_creative_role": 1.0 if any(k in role for k in ["design", "ui", "ux", "creative", "brand"]) else 0.0,
        "is_data_role": 1.0 if any(k in role for k in ["data", "analyst", "ml", "ai"]) else 0.0,
        "is_engineering_role": 1.0 if any(k in role for k in ["engineer", "developer", "backend", "frontend", "full stack"]) else 0.0,
        "has_technical_skills": 1.0 if any(s in {"python", "sql", "flask", "fastapi", "java", "react", "docker"} for s in skills) else 0.0,
        "experience_count": float(exp_count),
        "project_count": float(project_count),
        "cert_count": float(cert_count),
        "summary_length": float(len((resume.summary or "").split())),
        "jd_creative": 1.0 if any(k in jd for k in ["creative", "design", "portfolio", "visual"]) else 0.0,
        "jd_formal": 1.0 if any(k in jd for k in ["executive", "manager", "leadership", "stakeholder"]) else 0.0,
        "jd_ats": 1.0 if any(k in jd for k in ["ats", "keywords", "screening", "machine readable"]) else 0.0,
    }


def _predict_category_with_random_forest(features: Dict[str, float]) -> Dict[str, float]:
    """
    Returns category probability map using RandomForest if sklearn is available.
    If sklearn is unavailable, returns an empty map (caller uses heuristic fallback).
    """
    try:
        from sklearn.ensemble import RandomForestClassifier  # type: ignore
    except Exception:
        return {}

    feature_names = list(features.keys())

    # Small synthetic supervised dataset for bootstrapping category behavior.
    samples = [
        ([1, 0, 0, 0, 0, 4, 0, 35, 1, 0, 0], "Creative"),
        ([1, 0, 0, 0, 1, 3, 1, 45, 1, 0, 0], "Creative"),
        ([0, 0, 1, 1, 1, 2, 0, 28, 0, 0, 1], "ATS"),
        ([0, 1, 1, 1, 1, 2, 1, 30, 0, 0, 1], "ATS"),
        ([0, 0, 1, 1, 4, 2, 2, 60, 0, 1, 0], "Corporate"),
        ([0, 0, 1, 1, 5, 1, 1, 70, 0, 1, 0], "Corporate"),
        ([0, 0, 1, 1, 2, 2, 1, 45, 0, 0, 0], "Modern"),
        ([0, 1, 1, 1, 3, 3, 1, 50, 0, 0, 0], "Modern"),
        ([0, 0, 0, 0, 6, 1, 1, 55, 0, 1, 0], "Classic"),
        ([0, 0, 1, 0, 5, 1, 0, 52, 0, 1, 0], "Classic"),
    ]
    X_train = [row for row, _label in samples]
    y_train = [label for _row, label in samples]

    model = RandomForestClassifier(
        n_estimators=80,
        max_depth=5,
        random_state=42,
    )
    model.fit(X_train, y_train)

    x = [features[name] for name in feature_names]
    probs = model.predict_proba([x])[0]
    labels = list(model.classes_)
    return {labels[i]: float(probs[i]) for i in range(len(labels))}


def recommend_templates_ml(
    resume: Resume,
    job_description: str,
    templates_catalog: List[Dict[str, object]],
    top_k: int = 3,
) -> Dict[str, object]:
    """
    Recommends templates using:
    1) RandomForest (category preference) if sklearn available
    2) deterministic fallback heuristic
    """
    features = _build_template_features(resume, job_description)
    rf_probs = _predict_category_with_random_forest(features)
    used_model = "random_forest" if rf_probs else "heuristic"
    jd = (job_description or "").lower()
    role = (resume.profile_title or "").lower()
    ex_count = len(resume.experiences or [])

    scored = []
    for t in (templates_catalog or []):
        category = str(t.get("category", "General"))
        settings = t.get("settings", {}) or {}
        tpl = str(settings.get("template", "")).lower()
        mood = str(t.get("mood", "")).lower()

        score = 0.0
        # Category prior from RF probability (0..1 -> 0..8 points)
        if rf_probs:
            score += rf_probs.get(category, 0.0) * 8.0
        else:
            # Fallback heuristic category scoring.
            c = category.lower()
            if any(k in role for k in ["design", "ui", "ux", "creative"]):
                if c in {"creative"}:
                    score += 6
            if any(k in role for k in ["engineer", "developer", "analyst", "data"]):
                if c in {"modern", "ats", "corporate"}:
                    score += 5
            if ex_count >= 4 and c in {"corporate", "classic"}:
                score += 3
            if ex_count <= 1 and c in {"modern", "ats"}:
                score += 3

        # Template-level adjustments.
        if "ats" in jd and category.lower() == "ats":
            score += 3
        if any(k in jd for k in ["creative", "portfolio", "design"]) and category.lower() == "creative":
            score += 3
        if any(k in jd for k in ["manager", "lead", "stakeholder", "executive"]) and category.lower() in {"corporate", "classic"}:
            score += 2
        if tpl in {"compact", "modern"} and ex_count <= 2:
            score += 1.5
        if tpl in {"executive", "corporate"} and ex_count >= 4:
            score += 1.5
        if mood in {"formal", "technical"} and any(k in jd for k in ["ats", "enterprise", "platform"]):
            score += 1.0

        scored.append({
            "id": t.get("id"),
            "name": t.get("name"),
            "category": category,
            "template": settings.get("template"),
            "score": round(float(score), 3),
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    top = scored[: max(1, int(top_k or 3))]
    return {
        "algorithm": used_model,
        "top_templates": top,
        "features": features,
    }


def _enhance_line(line: str) -> str:
    text = re.sub(r"^[\-\*\u2022\.\s]+", "", (line or "").strip())
    if not text:
        return ""

    words = text.split()
    first = words[0].lower() if words else ""
    if first not in ACTION_VERBS:
        text = f"Delivered {text[0].lower() + text[1:]}" if len(text) > 1 else f"Delivered {text}"
    else:
        text = text[0].upper() + text[1:]

    has_metric = bool(re.search(r"\d|%|\$|x|ms|sec|hours?|days?", text.lower()))
    if not has_metric:
        text += " with measurable business impact"
    if not text.endswith("."):
        text += "."
    return text


def enhance_resume_bullets(resume: Resume) -> Dict[str, object]:
    enhanced_experiences = []
    for exp in resume.experiences:
        lines = [l for l in (exp.description or "").split("\n") if l.strip()]
        enhanced_lines = [_enhance_line(l) for l in lines] if lines else []
        enhanced_experiences.append({
            "job_title": exp.job_title,
            "company": exp.company,
            "start_date": exp.start_date,
            "end_date": exp.end_date,
            "description": "\n".join([l for l in enhanced_lines if l]),
        })

    enhanced_projects = []
    for proj in resume.projects:
        lines = [l for l in (proj.description or "").split("\n") if l.strip()]
        enhanced_lines = [_enhance_line(l) for l in lines] if lines else []
        enhanced_projects.append({
            "name": proj.name,
            "role": proj.role,
            "technologies": proj.technologies,
            "start_date": proj.start_date,
            "end_date": proj.end_date,
            "description": "\n".join([l for l in enhanced_lines if l]),
            "link": proj.link,
        })

    return {
        "experiences": enhanced_experiences,
        "projects": enhanced_projects,
        "message": "Bullets enhanced. Review wording and adjust metrics to real values.",
    }


def tailor_resume(resume: Resume, job_description: str) -> Dict[str, object]:
    ats = analyze_ats(resume, job_description)
    keywords = ats["matched_keywords"][:4] + ats["missing_keywords"][:4]
    keywords = [k for i, k in enumerate(keywords) if k and k not in keywords[:i]]

    role = resume.profile_title.strip() or "professional"
    summary = (
        f"Results-driven {role} with hands-on experience delivering projects across "
        f"{', '.join(keywords[:4]) if keywords else 'engineering and business priorities'}. "
        f"Known for execution, stakeholder collaboration, and measurable outcomes."
    )

    existing_skills = list(resume.skills or [])
    merged = existing_skills[:]
    for k in keywords:
        if k.lower() not in [s.lower() for s in merged]:
            merged.append(k)

    return {
        "tailored_summary": summary,
        "recommended_skills": merged[:20],
        "focus_keywords": keywords[:10],
        "ats_preview": ats,
    }


def rewrite_summary_tone(summary: str, tone: str) -> Dict[str, str]:
    text = (summary or "").strip()
    tone_key = (tone or "formal").strip().lower()
    if not text:
        return {"tone": tone_key, "rewritten_summary": ""}

    # Normalize spacing and trailing punctuation.
    text = re.sub(r"\s+", " ", text)
    if not text.endswith("."):
        text += "."

    if tone_key == "crisp":
        rewritten = (
            f"Delivers outcomes with clear ownership, fast execution, and measurable impact. {text}"
        )
    elif tone_key == "friendly":
        rewritten = (
            f"Enjoy collaborating with teams, solving practical problems, and shipping reliable results. {text}"
        )
    else:  # formal
        rewritten = (
            f"Results-oriented professional with a consistent record of execution and stakeholder alignment. {text}"
        )

    # Prevent repeated leading sentence when user clicks multiple times.
    rewritten = re.sub(
        r"(Results-oriented professional with a consistent record of execution and stakeholder alignment\.\s*){2,}",
        "Results-oriented professional with a consistent record of execution and stakeholder alignment. ",
        rewritten,
    )
    rewritten = re.sub(
        r"(Delivers outcomes with clear ownership, fast execution, and measurable impact\.\s*){2,}",
        "Delivers outcomes with clear ownership, fast execution, and measurable impact. ",
        rewritten,
    )
    rewritten = re.sub(
        r"(Enjoy collaborating with teams, solving practical problems, and shipping reliable results\.\s*){2,}",
        "Enjoy collaborating with teams, solving practical problems, and shipping reliable results. ",
        rewritten,
    )
    return {"tone": tone_key, "rewritten_summary": rewritten.strip()}


def plan_skill_gap(resume: Resume, job_description: str) -> Dict[str, object]:
    ats = analyze_ats(resume, job_description)
    missing = ats.get("missing_keywords", [])[:8]
    if not missing:
        return {
            "missing_skills": [],
            "plan_30_days": [
                "Week 1: Refine resume bullets with measurable impact.",
                "Week 2: Build one portfolio project aligned to target role.",
                "Week 3: Practice interview questions and system topics.",
                "Week 4: Apply to roles with tailored resume variants.",
            ],
            "message": "No major skill gaps detected from provided JD.",
        }

    weekly = [
        f"Week 1: Learn basics of {', '.join(missing[:2])}.",
        f"Week 2: Build mini project using {', '.join(missing[2:4] or missing[:2])}.",
        "Week 3: Document project, write impact bullets, and add GitHub proof.",
        "Week 4: Solve interview questions and update tailored resume.",
    ]
    return {
        "missing_skills": missing,
        "plan_30_days": weekly,
        "message": "Skill gap plan generated from current job description.",
    }


def _infer_assistant_intent(prompt: str) -> str:
    q = (prompt or "").strip().lower()
    if any(k in q for k in ["ats", "score", "keyword match", "jd match"]):
        return "ats"
    if any(k in q for k in ["tailor", "customize", "optimize resume", "align resume"]):
        return "tailor"
    if any(k in q for k in ["bullet", "enhance", "improve experience", "rewrite experience"]):
        return "bullets"
    if any(k in q for k in ["cover letter", "cover", "application letter"]):
        return "cover_letter"
    if any(k in q for k in ["interview", "questions"]):
        return "interview"
    if any(k in q for k in ["skill gap", "missing skills", "learning plan"]):
        return "skill_gap"
    if any(k in q for k in ["rewrite summary", "summary tone", "make summary"]):
        return "rewrite_summary"
    return "general"


def _resume_snapshot_for_llm(resume: Resume) -> Dict[str, Any]:
    def _cap(text: Any, limit: int = 420) -> str:
        t = re.sub(r"\s+", " ", str(text or "").strip())
        return t[:limit]

    experiences = []
    for e in (resume.experiences or [])[:8]:
        experiences.append({
            "job_title": _cap(e.job_title, 90),
            "company": _cap(e.company, 90),
            "start_date": _cap(e.start_date, 32),
            "end_date": _cap(e.end_date, 32),
            "description": _cap(e.description, 420),
        })

    projects = []
    for p in (resume.projects or [])[:8]:
        projects.append({
            "name": _cap(p.name, 90),
            "role": _cap(p.role, 90),
            "technologies": _cap(p.technologies, 160),
            "start_date": _cap(p.start_date, 32),
            "end_date": _cap(p.end_date, 32),
            "description": _cap(p.description, 420),
            "link": _cap(p.link, 180),
        })

    educations = []
    for e in (resume.educations or [])[:5]:
        educations.append({
            "degree": _cap(e.degree, 100),
            "institution": _cap(e.institution, 120),
            "start_date": _cap(e.start_date, 32),
            "end_date": _cap(e.end_date, 32),
            "description": _cap(e.description, 220),
        })

    return {
        "full_name": _cap(resume.full_name, 120),
        "profile_title": _cap(resume.profile_title, 120),
        "summary": _cap(resume.summary, 850),
        "email": _cap(resume.email, 160),
        "phone": _cap(resume.phone, 64),
        "location": _cap(f"{resume.city} {resume.address}", 180),
        "skills": [str(s).strip()[:64] for s in (resume.skills or [])[:25] if str(s).strip()],
        "experiences": experiences,
        "projects": projects,
        "educations": educations,
    }


def _sanitize_string(value: Any, max_chars: int = 1200) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return text[:max_chars]


def _sanitize_string_list(values: Any, max_items: int = 25, max_chars: int = 80) -> List[str]:
    if not isinstance(values, list):
        return []
    out: List[str] = []
    seen = set()
    for v in values:
        s = _sanitize_string(v, max_chars)
        if not s:
            continue
        k = s.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(s)
        if len(out) >= max_items:
            break
    return out


def _sanitize_experience_items(values: Any, max_items: int = 10) -> List[Dict[str, str]]:
    if not isinstance(values, list):
        return []
    items: List[Dict[str, str]] = []
    for row in values:
        if not isinstance(row, dict):
            continue
        description_raw = row.get("description")
        if isinstance(description_raw, list):
            description = "\n".join(
                [_sanitize_string(x, 220) for x in description_raw if _sanitize_string(x, 220)]
            )
        else:
            description = _sanitize_string(description_raw, 900)
        item = {
            "job_title": _sanitize_string(row.get("job_title"), 100),
            "company": _sanitize_string(row.get("company"), 100),
            "start_date": _sanitize_string(row.get("start_date"), 40),
            "end_date": _sanitize_string(row.get("end_date"), 40),
            "description": description,
        }
        if any(item.values()):
            items.append(item)
        if len(items) >= max_items:
            break
    return items


def _sanitize_project_items(values: Any, max_items: int = 10) -> List[Dict[str, str]]:
    if not isinstance(values, list):
        return []
    items: List[Dict[str, str]] = []
    for row in values:
        if not isinstance(row, dict):
            continue
        description_raw = row.get("description")
        if isinstance(description_raw, list):
            description = "\n".join(
                [_sanitize_string(x, 220) for x in description_raw if _sanitize_string(x, 220)]
            )
        else:
            description = _sanitize_string(description_raw, 900)
        item = {
            "name": _sanitize_string(row.get("name"), 120),
            "role": _sanitize_string(row.get("role"), 100),
            "technologies": _sanitize_string(row.get("technologies"), 180),
            "start_date": _sanitize_string(row.get("start_date"), 40),
            "end_date": _sanitize_string(row.get("end_date"), 40),
            "description": description,
            "link": _sanitize_string(row.get("link"), 220),
        }
        if any(item.values()):
            items.append(item)
        if len(items) >= max_items:
            break
    return items


def _sanitize_ai_patch(patch: Any) -> Dict[str, Any]:
    if not isinstance(patch, dict):
        return {}
    out: Dict[str, Any] = {}
    summary = _sanitize_string(patch.get("summary"), 1800)
    skills = _sanitize_string_list(patch.get("skills"), max_items=30, max_chars=70)
    experiences = _sanitize_experience_items(patch.get("experiences"), max_items=10)
    projects = _sanitize_project_items(patch.get("projects"), max_items=10)
    if summary:
        out["summary"] = summary
    if skills:
        out["skills"] = skills
    if experiences:
        out["experiences"] = experiences
    if projects:
        out["projects"] = projects
    return out


def _merge_ai_patches(primary: Dict[str, Any], fallback: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = dict(primary or {})
    for key, value in (fallback or {}).items():
        if key not in out:
            out[key] = value
            continue
        curr = out.get(key)
        if isinstance(curr, list) and not curr and isinstance(value, list):
            out[key] = value
        elif isinstance(curr, str) and not curr.strip() and isinstance(value, str):
            out[key] = value
    return out


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    raw = str(text or "").strip()
    if not raw:
        return None

    # Common fenced-code response cleanup.
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw).strip()

    for candidate in (raw, raw[raw.find("{"): raw.rfind("}") + 1] if ("{" in raw and "}" in raw) else ""):
        if not candidate:
            continue
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            continue
    return None


def _looks_like_placeholder_api_key(value: str) -> bool:
    v = str(value or "").strip().lower()
    if not v:
        return False
    if v in {"sk-xxxx", "your_openai_api_key", "your-api-key", "replace_me", "changeme"}:
        return True
    if v.startswith("sk-") and v.endswith("xxxx"):
        return True
    if "your" in v and "key" in v:
        return True
    return False


def _call_openai_structured_assistant(
    prompt: str,
    job_description: str,
    resume: Resume,
    company: str = "",
    role: str = "",
    timeout_sec: int = 25,
) -> Tuple[Optional[Dict[str, Any]], Dict[str, str]]:
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        return None, {"reason": "OPENAI_API_KEY not configured"}
    if _looks_like_placeholder_api_key(api_key):
        return None, {"reason": "OPENAI_API_KEY uses placeholder value; set a real key"}

    model = (os.getenv("OPENAI_MODEL") or "gpt-4o-mini").strip()
    base_url = (os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").strip().rstrip("/")
    url = f"{base_url}/chat/completions"

    system_prompt = (
        "You are a resume copilot. Reply ONLY as valid JSON object with keys: "
        "answer (string), apply_patch (object). "
        "apply_patch may include summary (string), skills (array of strings), "
        "experiences (array of objects with job_title, company, start_date, end_date, description), "
        "projects (array of objects with name, role, technologies, start_date, end_date, description, link). "
        "Do not invent companies, dates, or metrics unless explicitly present in input. "
        "When uncertain, keep apply_patch empty and give safe guidance in answer."
    )
    user_payload = {
        "prompt": _sanitize_string(prompt, 1200),
        "job_description": _sanitize_string(job_description, 4000),
        "company": _sanitize_string(company, 120),
        "role": _sanitize_string(role, 120),
        "resume": _resume_snapshot_for_llm(resume),
    }
    req_body = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(req_body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=max(10, int(timeout_sec))) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            body = ""
        status = getattr(e, "code", "http_error")
        reason = f"LLM HTTP {status}"
        if body:
            reason = f"{reason}: {body[:220]}"
        return None, {"reason": reason, "model": model}
    except Exception as e:
        return None, {"reason": f"LLM request failed: {str(e)}", "model": model}

    try:
        payload = json.loads(raw or "{}")
    except Exception:
        return None, {"reason": "LLM response is not valid JSON", "model": model}

    try:
        content = (
            payload.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
    except Exception:
        content = ""
    parsed = _extract_json_object(str(content or ""))
    if not parsed:
        return None, {"reason": "LLM did not return a valid JSON object", "model": model}
    return parsed, {"model": model}


def _quick_resume_score_local(resume: Resume) -> int:
    score = 0
    if (resume.full_name or "").strip():
        score += 10
    if (resume.email or "").strip():
        score += 10
    if (resume.phone or "").strip():
        score += 6
    if len(resume.skills or []) >= 5:
        score += 14
    if len(resume.experiences or []) >= 1:
        score += 20
    if len(resume.educations or []) >= 1:
        score += 14
    if len(resume.projects or []) >= 1:
        score += 12
    if (resume.summary or "").strip() and len((resume.summary or "").strip()) >= 40:
        score += 14
    return min(100, score)


def _heuristic_assistant_response(
    resume: Resume,
    prompt: str,
    job_description: str = "",
    company: str = "",
    role: str = "",
) -> Dict[str, Any]:
    intent = _infer_assistant_intent(prompt)

    def _reply(answer: str, patch: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            "answer": _sanitize_string(answer, 4000),
            "apply_patch": _sanitize_ai_patch(patch or {}),
            "intent": intent,
        }

    if intent == "ats":
        result = analyze_ats(resume, job_description)
        lines = [
            f"ATS Score: {result.get('score', 0)}/100",
            f"Matched: {', '.join(result.get('matched_keywords', [])[:10]) or '-'}",
            f"Missing: {', '.join(result.get('missing_keywords', [])[:10]) or '-'}",
        ]
        if result.get("suggestions"):
            lines.append("Top Suggestions:\n- " + "\n- ".join(result["suggestions"][:4]))
        return _reply("\n".join(lines))

    if intent == "tailor":
        result = tailor_resume(resume, job_description)
        patch = {
            "summary": result.get("tailored_summary", ""),
            "skills": result.get("recommended_skills", [])[:20],
        }
        lines = [
            "Tailored resume suggestions ready.",
            f"Focus Keywords: {', '.join(result.get('focus_keywords', [])[:10]) or '-'}",
            "Click 'Apply AI Changes' to update summary + skills.",
        ]
        return _reply("\n".join(lines), patch)

    if intent == "bullets":
        result = enhance_resume_bullets(resume)
        patch = {
            "experiences": result.get("experiences", []),
            "projects": result.get("projects", []),
        }
        msg = result.get("message") or "Bullet suggestions ready."
        return _reply(f"{msg}\nClick 'Apply AI Changes' to update bullets.", patch)

    if intent == "cover_letter":
        result = generate_cover_letter(
            resume=resume,
            job_description=job_description,
            company=company,
            role=role,
        )
        return _reply(result.get("cover_letter") or "Cover letter could not be generated.")

    if intent == "interview":
        result = generate_interview_questions(resume=resume, job_description=job_description, count=10)
        questions = result.get("questions", [])[:10]
        lines = [f"{i + 1}. {v}" for i, v in enumerate(questions)]
        return _reply("Interview Questions:\n" + ("\n".join(lines) if lines else "No questions generated."))

    if intent == "skill_gap":
        result = plan_skill_gap(resume, job_description)
        lines = [
            f"Missing Skills: {', '.join(result.get('missing_skills', [])[:10]) or '-'}",
        ]
        plan = result.get("learning_plan") or result.get("plan_30_days") or []
        if plan:
            lines.append("Learning Plan:\n- " + "\n- ".join(plan[:8]))
        if result.get("message"):
            lines.append(result["message"])
        return _reply("\n".join(lines))

    if intent == "rewrite_summary":
        tone = "formal"
        q = (prompt or "").lower()
        if "friendly" in q:
            tone = "friendly"
        elif "crisp" in q or "short" in q:
            tone = "crisp"
        result = rewrite_summary_tone(resume.summary or "", tone)
        patch = {"summary": result.get("rewritten_summary", "")}
        return _reply(f"Summary rewritten in {tone} tone. Click 'Apply AI Changes'.", patch)

    score = _quick_resume_score_local(resume)
    checks = []
    if not (resume.summary or "").strip():
        checks.append("Add a 2-3 line summary.")
    if len(resume.skills or []) < 6:
        checks.append("Add at least 6 core skills.")
    if len(resume.experiences or []) < 1:
        checks.append("Add at least 1 experience entry.")
    if len(resume.projects or []) < 1:
        checks.append("Add at least 1 project with outcomes.")
    if not resume.email or not resume.phone:
        checks.append("Complete email and phone in personal details.")
    if not checks:
        checks.append("Resume looks strong. Run ATS Score and Tailor Resume for job-specific optimization.")
    return _reply(
        f"I can help with ATS, tailoring, bullets, interview Q, cover letter, and skill-gap plans.\n"
        f"Current quick score: {score}/100\n"
        f"Next actions:\n- " + "\n- ".join(checks)
    )


def assist_resume_hybrid(
    resume: Resume,
    prompt: str,
    job_description: str = "",
    company: str = "",
    role: str = "",
    prefer_llm: bool = True,
) -> Dict[str, Any]:
    heuristic = _heuristic_assistant_response(
        resume=resume,
        prompt=prompt,
        job_description=job_description,
        company=company,
        role=role,
    )
    heuristic_patch = _sanitize_ai_patch(heuristic.get("apply_patch", {}))
    intent = str(heuristic.get("intent") or _infer_assistant_intent(prompt))

    if not prefer_llm:
        return {
            "answer": heuristic.get("answer", ""),
            "apply_patch": heuristic_patch,
            "intent": intent,
            "engine": "heuristic",
            "model": None,
            "fallback_used": False,
        }

    llm_data, llm_meta = _call_openai_structured_assistant(
        prompt=prompt,
        job_description=job_description,
        resume=resume,
        company=company,
        role=role,
    )
    if not llm_data:
        return {
            "answer": heuristic.get("answer", ""),
            "apply_patch": heuristic_patch,
            "intent": intent,
            "engine": "heuristic",
            "model": None,
            "fallback_used": True,
            "fallback_reason": llm_meta.get("reason", "LLM unavailable"),
        }

    llm_answer = _sanitize_string(llm_data.get("answer"), 5000)
    llm_patch = _sanitize_ai_patch(llm_data.get("apply_patch"))
    merged_patch = _merge_ai_patches(llm_patch, heuristic_patch)
    answer = llm_answer or heuristic.get("answer", "")
    if not answer:
        answer = "No answer generated. Please retry with a clearer prompt."

    return {
        "answer": answer,
        "apply_patch": merged_patch,
        "intent": intent,
        "engine": "llm",
        "model": llm_meta.get("model"),
        "fallback_used": False,
    }


def generate_cover_letter(
    resume: Resume,
    job_description: str,
    company: str = "",
    role: str = "",
) -> Dict[str, str]:
    """Create a deterministic, role-aware cover letter draft."""
    ats = analyze_ats(resume, job_description)
    focus = ats.get("matched_keywords", [])[:4] + ats.get("missing_keywords", [])[:3]
    focus = [k for i, k in enumerate(focus) if k and k not in focus[:i]]

    full_name = (resume.full_name or "Candidate").strip()
    target_role = (role or resume.profile_title or "the role").strip()
    company_name = (company or "your company").strip()
    years_hint = max(1, len(resume.experiences or []))
    summary = (resume.summary or "").strip()
    summary_line = summary[:240].strip()
    if summary_line and not summary_line.endswith("."):
        summary_line += "."

    skills_line = ", ".join((resume.skills or [])[:8])
    focus_line = ", ".join(focus[:6])

    letter = (
        f"Dear Hiring Manager,\n\n"
        f"I am writing to express my interest in the {target_role} position at {company_name}. "
        f"With hands-on experience across {years_hint}+ career stage(s), I have delivered projects that align with "
        f"business goals and technical quality.\n\n"
        f"{summary_line if summary_line else 'My background combines execution, collaboration, and measurable outcomes.'}\n\n"
        f"My core strengths include {skills_line if skills_line else 'software development, problem solving, and communication'}. "
        f"I am especially excited to contribute in areas such as {focus_line if focus_line else 'scalable delivery, product impact, and stakeholder alignment'}.\n\n"
        f"I would value the opportunity to discuss how my experience can support {company_name}'s goals. "
        f"Thank you for your time and consideration.\n\n"
        f"Sincerely,\n{full_name}"
    )
    return {
        "cover_letter": letter,
        "company": company_name,
        "role": target_role,
    }


def generate_interview_questions(
    resume: Resume,
    job_description: str,
    count: int = 20,
) -> Dict[str, object]:
    """Generate deterministic interview questions from resume role/skills + JD keywords."""
    total = max(5, min(30, int(count or 20)))
    role = (resume.profile_title or "the role").strip()
    skills = [s for s in (resume.skills or []) if s][:8]
    keywords = _extract_job_keywords(job_description, limit=12)
    anchors = []
    for item in (skills + keywords):
        if item and item.lower() not in [a.lower() for a in anchors]:
            anchors.append(item)
    anchors = anchors[:10]

    questions: List[str] = []
    questions.append(f"Tell me about yourself and why you are a fit for {role}.")
    questions.append("Walk me through one project where you delivered measurable impact.")
    questions.append("How do you prioritize tasks when multiple deadlines conflict?")
    questions.append("Describe a technical challenge you solved and the trade-offs you considered.")
    questions.append("How do you ensure quality before shipping your work?")

    for a in anchors:
        questions.append(f"Explain your hands-on experience with {a}.")
        questions.append(f"What is one common failure mode in {a}, and how do you prevent it?")

    questions.append("Describe a time you received difficult feedback and how you responded.")
    questions.append("How do you collaborate with non-technical stakeholders?")
    questions.append("What metrics do you track to evaluate your work impact?")
    questions.append("Why do you want this role, and what outcomes would you target in the first 90 days?")

    deduped = []
    seen = set()
    for q in questions:
        key = q.lower().strip()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(q)
        if len(deduped) >= total:
            break
    return {
        "role": role,
        "questions": deduped,
        "count": len(deduped),
    }


def create_multilingual_variant(
    resume: Resume,
    language: str = "english",
) -> Dict[str, object]:
    """Create lightweight localized headings + summary note for resume reuse."""
    lang = (language or "english").strip().lower()
    heading_map = {
        "english": {
            "summary": "Summary",
            "experience": "Experience",
            "education": "Education",
            "projects": "Projects",
            "skills": "Skills",
        },
        "tamil_romanized": {
            "summary": "Surukkam",
            "experience": "Anubavam",
            "education": "Kalvi",
            "projects": "Thittangal",
            "skills": "Thiranugal",
        },
        "hindi_romanized": {
            "summary": "Saaransh",
            "experience": "Anubhav",
            "education": "Shiksha",
            "projects": "Pariyojana",
            "skills": "Kaushal",
        },
    }
    if lang not in heading_map:
        lang = "english"

    name = (resume.full_name or "Candidate").strip()
    title = (resume.profile_title or "Professional").strip()
    summary = (resume.summary or "").strip() or "Add a concise role-focused summary."
    top_skills = ", ".join((resume.skills or [])[:8]) or "Add your core skills"
    labels = heading_map[lang]
    preview = (
        f"Name: {name}\n"
        f"Title: {title}\n"
        f"{labels['summary']}: {summary}\n"
        f"{labels['skills']}: {top_skills}\n"
        f"{labels['experience']}: {len(resume.experiences or [])} entries\n"
        f"{labels['education']}: {len(resume.educations or [])} entries\n"
        f"{labels['projects']}: {len(resume.projects or [])} entries\n"
    )
    return {
        "language": lang,
        "labels": labels,
        "preview_text": preview,
    }


def optimize_linkedin_profile(resume: Resume, target_role: str = "") -> Dict[str, object]:
    role = (target_role or resume.profile_title or "Professional").strip()
    skills = [s for s in (resume.skills or []) if s][:10]
    headline = f"{role} | " + " | ".join(skills[:4]) if skills else role
    about = (
        f"I am a {role} focused on delivering measurable outcomes through practical execution and team collaboration. "
        f"My core strengths include {', '.join(skills[:8]) if skills else 'problem solving, communication, and ownership'}. "
        f"I enjoy building reliable solutions, improving processes, and driving impact."
    )
    return {
        "headline": headline[:220],
        "about": about,
        "top_skills": skills,
    }


def grammar_fix_resume(resume: Resume) -> Dict[str, object]:
    def _fix(text: str) -> str:
        t = re.sub(r"\s+", " ", (text or "").strip())
        if not t:
            return ""
        t = t[0].upper() + t[1:]
        if not t.endswith("."):
            t += "."
        return t

    fixed_summary = _fix(resume.summary or "")
    fixed_exp = []
    for exp in (resume.experiences or []):
        lines = [l.strip() for l in (exp.description or "").split("\n") if l.strip()]
        fixed_lines = [_fix(l) for l in lines]
        fixed_exp.append({
            "job_title": exp.job_title,
            "company": exp.company,
            "start_date": exp.start_date,
            "end_date": exp.end_date,
            "description": "\n".join(fixed_lines),
        })
    fixed_proj = []
    for p in (resume.projects or []):
        lines = [l.strip() for l in (p.description or "").split("\n") if l.strip()]
        fixed_lines = [_fix(l) for l in lines]
        fixed_proj.append({
            "name": p.name,
            "role": p.role,
            "technologies": p.technologies,
            "start_date": p.start_date,
            "end_date": p.end_date,
            "description": "\n".join(fixed_lines),
            "link": p.link,
        })
    return {
        "summary": fixed_summary,
        "experiences": fixed_exp,
        "projects": fixed_proj,
        "message": "Grammar cleanup applied. Please verify meaning before final use.",
    }


def generate_email_apply_kit(resume: Resume, company: str = "", role: str = "") -> Dict[str, object]:
    r = (role or resume.profile_title or "Application").strip()
    c = (company or "Hiring Team").strip()
    subject = f"Application for {r} - {resume.full_name or 'Candidate'}"
    body = (
        f"Hello {c},\n\n"
        f"I am applying for the {r} role. I have attached my resume for your review.\n"
        f"I would appreciate the opportunity to discuss how my experience can contribute to your team.\n\n"
        f"Thanks,\n{resume.full_name or 'Candidate'}\n{resume.email or ''}\n{resume.phone or ''}"
    )
    checklist = [
        "Attach latest PDF resume",
        "Attach cover letter (if required)",
        "Include portfolio/GitHub link",
        "Customize subject with role + company",
        "Double-check recruiter name and email",
    ]
    return {"subject": subject, "body": body, "checklist": checklist}


def quantify_achievement_lines(resume: Resume) -> Dict[str, object]:
    suggestions = []
    source_lines = []
    for exp in (resume.experiences or []):
        for line in (exp.description or "").split("\n"):
            l = line.strip()
            if not l:
                continue
            source_lines.append(l)
            has_metric = bool(re.search(r"\d|%|\$|x|hours?|days?|weeks?", l.lower()))
            if not has_metric:
                suggestions.append(f"{l} -> {l.rstrip('.')} resulting in measurable impact (add real metric).")
    return {
        "total_lines": len(source_lines),
        "suggestions": suggestions[:20],
        "message": "Add real numbers where marked to increase recruiter trust.",
    }


def detect_duplicates(resume: Resume) -> Dict[str, object]:
    dup_skills = []
    seen = set()
    for s in (resume.skills or []):
        key = s.strip().lower()
        if not key:
            continue
        if key in seen and s not in dup_skills:
            dup_skills.append(s)
        seen.add(key)

    lines = []
    for exp in (resume.experiences or []):
        for l in (exp.description or "").split("\n"):
            if l.strip():
                lines.append(l.strip().lower())
    dup_lines = []
    line_seen = set()
    for l in lines:
        if l in line_seen and l not in dup_lines:
            dup_lines.append(l)
        line_seen.add(l)
    return {
        "duplicate_skills": dup_skills,
        "duplicate_bullets": dup_lines[:12],
        "message": "Remove duplicates to improve clarity and ATS readability.",
    }
