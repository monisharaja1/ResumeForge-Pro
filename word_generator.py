"""
Word-export helper using RTF output (opens in Microsoft Word without extra deps).
"""

import io
from typing import Union

from models import Resume


def _rtf_escape(text: str) -> str:
    """Escape text for RTF and preserve Unicode characters."""
    if not text:
        return ""
    out = []
    for ch in str(text):
        code = ord(ch)
        if ch == "\\":
            out.append(r"\\")
        elif ch == "{":
            out.append(r"\{")
        elif ch == "}":
            out.append(r"\}")
        elif ch == "\n":
            out.append(r"\line ")
        elif 32 <= code <= 126:
            out.append(ch)
        else:
            # RTF unicode escape with ASCII fallback.
            out.append(rf"\u{code}?")
    return "".join(out)


class WordGenerator:
    @staticmethod
    def generate(resume: Resume, output: Union[str, io.BytesIO]) -> Union[str, io.BytesIO]:
        lines = []
        add = lines.append

        add(r"{\rtf1\ansi\deff0")
        add(r"{\fonttbl{\f0 Calibri;}{\f1 Calibri;}}")
        add(r"\viewkind4\uc1\pard\sa140\sl276\slmult1\f0\fs22")

        if resume.full_name:
            add(rf"\pard\b\fs40 {_rtf_escape(resume.full_name)}\b0\fs22\par")
        if resume.profile_title:
            add(rf"\pard\i {_rtf_escape(resume.profile_title)}\i0\par")

        contact = []
        if resume.email:
            contact.append(f"Email: {resume.email}")
        if resume.phone:
            contact.append(f"Phone: {resume.phone}")
        if resume.address:
            contact.append(f"Address: {resume.address}")
        if contact:
            add(rf"\pard {_rtf_escape(' | '.join(contact))}\par")
        add(r"\par")

        def heading(title: str) -> None:
            add(rf"\pard\b\fs28 {_rtf_escape(title)}\b0\fs22\par")

        if resume.summary and resume.summary.strip():
            heading("SUMMARY")
            add(rf"\pard {_rtf_escape(resume.summary)}\par\par")

        if resume.experiences:
            heading("WORK EXPERIENCE")
            for exp in resume.experiences:
                head = exp.job_title or ""
                if exp.company:
                    head += f" at {exp.company}" if head else exp.company
                date = ""
                if exp.start_date or exp.end_date:
                    date = f" ({exp.start_date or ''} - {exp.end_date or 'Present'})"
                add(rf"\pard\b {_rtf_escape(head + date)}\b0\par")
                if exp.description:
                    add(rf"\pard {_rtf_escape(exp.description)}\par")
                add(r"\par")

        if resume.educations:
            heading("EDUCATION")
            for edu in resume.educations:
                head = edu.degree or ""
                if edu.institution:
                    head += f" at {edu.institution}" if head else edu.institution
                date = ""
                if edu.start_date or edu.end_date:
                    date = f" ({edu.start_date or ''} - {edu.end_date or 'Present'})"
                add(rf"\pard\b {_rtf_escape(head + date)}\b0\par")
                if edu.description:
                    add(rf"\pard {_rtf_escape(edu.description)}\par")
                add(r"\par")

        if resume.projects:
            heading("PROJECTS")
            for proj in resume.projects:
                head = proj.name or ""
                if proj.role:
                    head += f" - {proj.role}" if head else proj.role
                add(rf"\pard\b {_rtf_escape(head)}\b0\par")
                if proj.technologies:
                    add(rf"\pard Technologies: {_rtf_escape(proj.technologies)}\par")
                if proj.description:
                    add(rf"\pard {_rtf_escape(proj.description)}\par")
                if proj.link:
                    add(rf"\pard Link: {_rtf_escape(proj.link)}\par")
                add(r"\par")

        if resume.certifications:
            heading("CERTIFICATIONS")
            for cert in resume.certifications:
                head = cert.name or ""
                if cert.issuer:
                    head += f" - {cert.issuer}" if head else cert.issuer
                if cert.date:
                    head += f" ({cert.date})"
                add(rf"\pard\b {_rtf_escape(head)}\b0\par")
                if cert.link:
                    add(rf"\pard Credential: {_rtf_escape(cert.link)}\par")
                add(r"\par")

        if resume.languages:
            heading("LANGUAGES")
            for lang in resume.languages:
                add(rf"\pard {_rtf_escape((lang.name or '') + ' - ' + (lang.proficiency or ''))}\par")
            add(r"\par")

        if resume.skills:
            heading("SKILLS")
            for skill in sorted(resume.skills):
                add(rf"\pard - {_rtf_escape(skill)}\par")
            add(r"\par")

        if resume.achievements:
            heading("ACHIEVEMENTS")
            for ach in resume.achievements:
                add(rf"\pard\b {_rtf_escape(ach.title or '')}\b0\par")
                if ach.subtitle:
                    add(rf"\pard\i {_rtf_escape(ach.subtitle)}\i0\par")
                if ach.description:
                    add(rf"\pard {_rtf_escape(ach.description)}\par")
                add(r"\par")

        if resume.references:
            heading("REFERENCES")
            for ref in resume.references:
                head = ref.name or ""
                if ref.title:
                    head += f" - {ref.title}" if head else ref.title
                if ref.company:
                    head += f", {ref.company}" if head else ref.company
                add(rf"\pard\b {_rtf_escape(head)}\b0\par")
                if ref.phone:
                    add(rf"\pard Phone: {_rtf_escape(ref.phone)}\par")
                if ref.email:
                    add(rf"\pard Email: {_rtf_escape(ref.email)}\par")
                if ref.website:
                    add(rf"\pard Web: {_rtf_escape(ref.website)}\par")
                add(r"\par")

        add("}")
        content = "\n".join(lines).encode("utf-8")

        if isinstance(output, io.BytesIO):
            output.write(content)
            return output

        with open(output, "wb") as f:
            f.write(content)
        return output
