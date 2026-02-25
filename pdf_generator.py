"""
Professional PDF Generator â€“ with icons, tables, two-column references, achievements.
"""
import os
import io
import html
from typing import Union, Optional, List
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, HRFlowable
)
from PIL import Image as PILImage

from config import AppConfig
from models import Resume

import logging
logger = logging.getLogger(__name__)


class PDFGenerator:
    @staticmethod
    def _resolve_template_name(template_name: str) -> str:
        """Normalize incoming template key/id/name to a known template key."""
        raw = str(template_name or "").strip().lower()
        normalized = raw.replace("-", "_").replace(" ", "_")
        aliases = {
            "mod_clean": "modern",
            "mod_zen": "harsh_minimal",
            "corp_royal": "corporate",
            "corp_slate": "executive",
            "classic_ink": "classic",
            "classic_paper": "classic",
            "creative_amber": "snack_gray",
            "creative_blue": "vision_blue",
            "ats_fast": "compact",
            "ats_plain": "modern",
            "two_column_tech": "javid_split",
            "canva_mint_pro": "javid_split",
            "canva_editorial_rose": "modern",
            "canva_neo_charcoal": "executive",
            "canva_skyline_aqua": "vision_blue",
            "canva_portfolio_craft": "creative_split",
            "canva_aurora_green": "teal_modern",
            "canva_midnight_navy": "executive_slate",
            "canva_sunset_coral": "snack_gray",
            "canva_lilac_lite": "creative_split",
            "canva_forest_charcoal": "metro_sidebar",
            "canva_ice_blue": "astra_clean",
            "canva_gold_ink": "classic_clarity",
            "canva_ruby_panel": "impact_panel",
            "canva_slate_frost": "mono_compact",
            "canva_ocean_pro": "metro_sidebar",
        }
        resolved = aliases.get(normalized, normalized)
        if resolved in AppConfig.TEMPLATES:
            return resolved
        return AppConfig.DEFAULT_TEMPLATE

    @staticmethod
    def _apply_template_personality(template_name: str, template_cfg: dict) -> dict:
        """
        Apply per-template visual personality so each template renders
        with a distinct style/alignment baseline.
        """
        key = str(template_name or "").strip().lower()
        personalities = {
            "modern": {
                "font_size_title": 26,
                "font_size_heading": 13,
                "font_size_body": 10,
                "heading_align": "left",
                "body_align": "justify",
                "section_border": False,
                "border_radius": 4,
                "bullet": "-",
                "header_layout_default": "default",
                "bg_art": "top_band",
            },
            "corporate": {
                "font_size_title": 28,
                "font_size_heading": 14,
                "font_size_body": 11,
                "heading_align": "left",
                "body_align": "left",
                "section_border": True,
                "border_radius": 2,
                "bullet": "-",
                "header_layout_default": "split",
                "bg_art": "left_rail",
            },
            "classic": {
                "font_size_title": 27,
                "font_size_heading": 13,
                "font_size_body": 10,
                "heading_align": "center",
                "body_align": "left",
                "section_border": False,
                "border_radius": 0,
                "bullet": "*",
                "header_layout_default": "center",
                "bg_art": "double_rule",
            },
            "compact": {
                "font_size_title": 22,
                "font_size_heading": 12,
                "font_size_body": 9,
                "heading_align": "left",
                "body_align": "left",
                "section_border": False,
                "border_radius": 0,
                "bullet": "-",
                "header_layout_default": "default",
                "bg_art": "corner_mark",
            },
            "executive": {
                "font_size_title": 30,
                "font_size_heading": 14,
                "font_size_body": 11,
                "heading_align": "left",
                "body_align": "justify",
                "section_border": True,
                "border_radius": 2,
                "bullet": "*",
                "header_layout_default": "split",
                "bg_art": "executive_panel",
            },
            "snack_gray": {
                "heading_align": "left",
                "body_align": "left",
                "section_border": False,
                "header_layout_default": "left",
                "bg_art": "soft_orb",
            },
            "vision_blue": {
                "heading_align": "left",
                "body_align": "justify",
                "section_border": False,
                "header_layout_default": "default",
                "bg_art": "top_band",
            },
            "harsh_minimal": {
                "font_size_title": 26,
                "font_size_heading": 11,
                "font_size_body": 9,
                "heading_align": "center",
                "body_align": "left",
                "section_border": False,
                "bullet": "-",
                "header_layout_default": "center",
                "bg_art": "minimal_line",
            },
            "javid_split": {
                "layout": "two_column",
                "left_column_ratio": 0.32,
                "heading_align": "left",
                "body_align": "left",
                "section_border": False,
                "header_layout_default": "split",
                "bg_art": "split_rail",
            },
            "teal_modern": {
                "font_size_title": 28,
                "font_size_heading": 13,
                "font_size_body": 10,
                "heading_align": "left",
                "body_align": "left",
                "section_border": False,
                "border_radius": 5,
                "bullet": "-",
                "header_layout_default": "default",
                "bg_art": "top_band",
                "page_border": False,
                "contact_icons": False,
            },
            "astra_clean": {
                "heading_align": "left",
                "body_align": "justify",
                "section_border": False,
                "header_layout_default": "default",
                "bg_art": "minimal_line",
            },
            "metro_sidebar": {
                "layout": "two_column",
                "left_column_ratio": 0.33,
                "heading_align": "left",
                "body_align": "left",
                "section_border": False,
                "header_layout_default": "split",
                "bg_art": "split_rail",
            },
            "executive_slate": {
                "heading_align": "left",
                "body_align": "justify",
                "section_border": True,
                "border_radius": 2,
                "header_layout_default": "split",
                "bg_art": "executive_panel",
            },
            "creative_split": {
                "layout": "two_column",
                "left_column_ratio": 0.34,
                "heading_align": "left",
                "body_align": "left",
                "section_border": False,
                "bullet": "â€¢",
                "header_layout_default": "split",
                "bg_art": "creative_block",
            },
            "mono_compact": {
                "heading_align": "left",
                "body_align": "left",
                "section_border": False,
                "header_layout_default": "left",
                "bg_art": "corner_mark",
            },
            "classic_clarity": {
                "heading_align": "left",
                "body_align": "justify",
                "section_border": False,
                "header_layout_default": "default",
                "bg_art": "double_rule",
            },
            "impact_panel": {
                "layout": "two_column",
                "left_column_ratio": 0.31,
                "heading_align": "left",
                "body_align": "left",
                "section_border": True,
                "bullet": "â€¢",
                "header_layout_default": "split",
                "bg_art": "impact_band",
            },
            "contemporary_photo": {
                "heading_align": "left",
                "body_align": "justify",
                "section_border": False,
                "header_layout_default": "left",
                "bg_art": "photo_corner",
            },
        }
        template_cfg.update(personalities.get(key, {}))
        return template_cfg

    @staticmethod
    def _build_profile_image_flowable(raw_bytes: bytes, align: str = "LEFT"):
        """Create a robust profile image flowable with PNG conversion fallback."""
        if not raw_bytes:
            return None
        try:
            flow = Image(io.BytesIO(raw_bytes), width=0.95 * inch, height=0.95 * inch)
            flow.hAlign = align
            return flow
        except Exception:
            try:
                with PILImage.open(io.BytesIO(raw_bytes)) as img:
                    mode = img.mode or "RGB"
                    if mode not in ("RGB", "RGBA"):
                        img = img.convert("RGB")
                    out = io.BytesIO()
                    img.save(out, format="PNG")
                    out.seek(0)
                    flow = Image(out, width=0.95 * inch, height=0.95 * inch)
                    flow.hAlign = align
                    return flow
            except Exception:
                return None

    @staticmethod
    def generate(
        resume: Resume,
        output: Union[str, io.BytesIO],
        template_name: str = "corporate",  # Default to new corporate template
        page_size: str = "letter",
        layout_override: Optional[str] = None,
        heading_align_override: Optional[str] = None,
        body_align_override: Optional[str] = None,
        accent_color_override: Optional[str] = None,
        font_override: Optional[str] = None,
        page_border_override: Optional[bool] = None,
        compact_mode: bool = False,
        ats_safe_mode: bool = False,
        section_order: Optional[List[str]] = None,
        font_scale: float = 1.0,
        margin_preset: str = "normal",
        section_visibility: Optional[dict] = None,
        header_layout: Optional[str] = None,
    ) -> Union[str, io.BytesIO]:
        """
        Generate a beautifully formatted PDF resume with support for
        icons, education tables, two-column references, and achievements.
        """
        # Select page size
        pagesize = A4 if page_size.lower() == "a4" else letter

        # Load template config
        template_name = PDFGenerator._resolve_template_name(template_name)
        default_key = AppConfig.DEFAULT_TEMPLATE if AppConfig.DEFAULT_TEMPLATE in AppConfig.TEMPLATES else "modern"
        template_cfg = AppConfig.TEMPLATES.get(template_name, AppConfig.TEMPLATES[default_key]).copy()
        template_cfg = PDFGenerator._apply_template_personality(template_name, template_cfg)

        # Apply overrides
        if layout_override:
            normalized_layout = str(layout_override).strip().lower()
            layout_alias = {
                "single": "single",
                "single_column": "single",
                "one_column": "single",
                "two": "two_column",
                "two_column": "two_column",
                "two-column": "two_column",
            }
            template_cfg["layout"] = layout_alias.get(normalized_layout, normalized_layout)
        if heading_align_override:
            template_cfg["heading_align"] = heading_align_override
        if body_align_override:
            template_cfg["body_align"] = body_align_override
        if accent_color_override:
            template_cfg["accent"] = accent_color_override
        if font_override:
            font_map = {
                "Helvetica": ("Helvetica", "Helvetica-Bold"),
                "Times": ("Times-Roman", "Times-Bold"),
                "Courier": ("Courier", "Courier-Bold"),
                # Fallback to Times because Georgia is not guaranteed to be registered.
                "Georgia": ("Times-Roman", "Times-Bold"),
                # Web/modern names mapped to built-in safe PDF fonts.
                "Poppins": ("Helvetica", "Helvetica-Bold"),
                "Montserrat": ("Helvetica", "Helvetica-Bold"),
                "Nunito": ("Helvetica", "Helvetica-Bold"),
                "FiraSans": ("Helvetica", "Helvetica-Bold"),
                "Lora": ("Times-Roman", "Times-Bold"),
                "Merriweather": ("Times-Roman", "Times-Bold"),
                "RobotoSlab": ("Times-Roman", "Times-Bold"),
                "PlayfairDisplay": ("Times-Roman", "Times-Bold"),
                "LibreBaskerville": ("Times-Roman", "Times-Bold"),
            }
            body_font, heading_font = font_map.get(font_override, ("Helvetica", "Helvetica-Bold"))
            template_cfg["font_body"] = body_font
            template_cfg["font_heading"] = heading_font
        if page_border_override is not None:
            template_cfg["page_border"] = page_border_override

        # Normalize alignment keys so all templates render consistently.
        def _normalize_align(value: Optional[str], default: str = "left") -> str:
            val = str(value or default).strip().lower()
            return val if val in {"left", "center", "right", "justify"} else default

        template_cfg["heading_align"] = _normalize_align(template_cfg.get("heading_align"), "left")
        template_cfg["body_align"] = _normalize_align(template_cfg.get("body_align"), "left")
        if compact_mode:
            # Compact mode: fit more content while preserving readability.
            template_cfg["font_size_title"] = max(18, int(template_cfg.get("font_size_title", 24) * 0.88))
            template_cfg["font_size_heading"] = max(10, int(template_cfg.get("font_size_heading", 12) * 0.9))
            template_cfg["font_size_body"] = max(8, int(template_cfg.get("font_size_body", 10) * 0.92))
            template_cfg["spacing"] = max(8, int(template_cfg.get("spacing", 12) * 0.75))
        if ats_safe_mode:
            template_cfg["contact_icons"] = False
            template_cfg["page_border"] = False
            template_cfg["section_border"] = False
            template_cfg["font_body"] = "Helvetica"
            template_cfg["font_heading"] = "Helvetica-Bold"
            template_cfg["accent"] = "#111111"
            template_cfg["bullet"] = "-"
            template_cfg["background"] = "#ffffff"
        # User-facing font scaling control from UI slider.
        try:
            fs = float(font_scale)
        except Exception:
            fs = 1.0
        fs = min(1.3, max(0.8, fs))
        template_cfg["font_size_title"] = max(14, int(template_cfg.get("font_size_title", 24) * fs))
        template_cfg["font_size_heading"] = max(9, int(template_cfg.get("font_size_heading", 12) * fs))
        template_cfg["font_size_body"] = max(7, int(template_cfg.get("font_size_body", 10) * fs))

        margin_map = {
            "narrow": 54,
            "compact": 54,
            "normal": 54,
            "wide": 90,
            "relaxed": 90,
        }
        margin_value = margin_map.get(str(margin_preset or "normal").lower(), 72)

        # Convert hex colors
        accent_color = colors.HexColor(template_cfg["accent"])
        bg_color = colors.HexColor(template_cfg.get("background", "#ffffff"))
        section_spacing = max(2, int(template_cfg.get("spacing", 12) * 0.30))
        item_spacing = max(1, int(section_spacing * 0.5))
        section_tail_spacing = max(1, item_spacing)

        # Alignment helper
        def _get_alignment(align_str: str) -> int:
            key = str(align_str or "left").strip().lower()
            return {
                "left": TA_LEFT,
                "center": TA_CENTER,
                "right": TA_RIGHT,
                "justify": TA_JUSTIFY,
            }.get(key, TA_LEFT)

        # Document setup
        doc = SimpleDocTemplate(
            output,
            pagesize=pagesize,
            rightMargin=margin_value,
            leftMargin=margin_value,
            topMargin=margin_value,
            bottomMargin=margin_value,
            title=f"Resume - {resume.full_name}",
            author=resume.full_name,
        )

        # Draw page border on every page without affecting flowable layout.
        def _soften(col: colors.Color, white_mix: float = 0.87) -> colors.Color:
            mix = min(0.96, max(0.0, white_mix))
            return colors.Color(
                col.red * (1 - mix) + 1.0 * mix,
                col.green * (1 - mix) + 1.0 * mix,
                col.blue * (1 - mix) + 1.0 * mix,
            )

        def _draw_template_art(canv, width, height):
            art = str(template_cfg.get("bg_art", "")).strip().lower()
            if not art:
                return
            a_light = _soften(accent_color, 0.9)
            a_mid = _soften(accent_color, 0.8)
            canv.saveState()
            canv.setStrokeColor(a_mid)
            canv.setFillColor(a_light)
            if art == "top_band":
                canv.rect(0, height - 28, width, 20, stroke=0, fill=1)
                canv.setLineWidth(0.7)
                canv.line(36, height - 30, width - 36, height - 30)
            elif art == "left_rail":
                canv.rect(0, 0, 18, height, stroke=0, fill=1)
            elif art == "double_rule":
                canv.setLineWidth(0.8)
                canv.line(36, height - 36, width - 36, height - 36)
                canv.line(36, height - 42, width - 36, height - 42)
            elif art == "corner_mark":
                canv.rect(width - 58, height - 58, 28, 28, stroke=0, fill=1)
                canv.rect(width - 28, height - 28, 10, 10, stroke=0, fill=1)
            elif art == "executive_panel":
                canv.rect(0, height - 38, width, 16, stroke=0, fill=1)
                canv.rect(0, 0, 10, height, stroke=0, fill=1)
            elif art == "soft_orb":
                canv.circle(width - 34, height - 30, 14, stroke=0, fill=1)
                canv.circle(width - 16, height - 16, 7, stroke=0, fill=1)
            elif art == "minimal_line":
                canv.setLineWidth(1.0)
                canv.line(36, height - 26, width - 36, height - 26)
            elif art == "split_rail":
                rail_w = max(36, int(width * 0.08))
                canv.rect(0, 0, rail_w, height, stroke=0, fill=1)
            elif art == "creative_block":
                canv.rect(0, height - 44, 84, 22, stroke=0, fill=1)
                canv.rect(width - 84, height - 22, 84, 22, stroke=0, fill=1)
            elif art == "impact_band":
                canv.rect(0, height - 48, width, 18, stroke=0, fill=1)
                canv.rect(width - 20, 0, 20, height, stroke=0, fill=1)
            elif art == "photo_corner":
                canv.rect(width - 78, height - 78, 50, 50, stroke=0, fill=1)
                canv.circle(width - 28, height - 28, 8, stroke=0, fill=1)
            canv.restoreState()

        def _draw_page_border(canv, _doc):
            width, height = pagesize
            _draw_template_art(canv, width, height)
            if not template_cfg.get("page_border", True):
                return
            border_inset = 18
            canv.saveState()
            canv.setStrokeColor(accent_color)
            canv.setLineWidth(1)
            canv.rect(
                border_inset,
                border_inset,
                width - (2 * border_inset),
                height - (2 * border_inset),
                stroke=1,
                fill=0,
            )
            canv.restoreState()

        # ---------- Styles ----------
        styles = {}

        # Title (name)
        styles["Title"] = ParagraphStyle(
            name="Title",
            fontName=template_cfg["font_heading"],
            fontSize=template_cfg["font_size_title"],
            textColor=accent_color,
            alignment=_get_alignment(template_cfg["heading_align"]),
            leading=template_cfg["font_size_title"] + 2,
            spaceAfter=3,
        )

        # Profile title (e.g., "Office Marketing")
        styles["ProfileTitle"] = ParagraphStyle(
            name="ProfileTitle",
            fontName=template_cfg["font_body"],
            fontSize=template_cfg["font_size_title"] - 8,
            textColor=colors.gray,
            alignment=_get_alignment(template_cfg["heading_align"]),
            leading=template_cfg["font_size_title"] - 4,
            spaceBefore=1,
            spaceAfter=2,
        )

        # Section heading
        heading_style = ParagraphStyle(
            name="Heading",
            fontName=template_cfg["font_heading"],
            fontSize=template_cfg["font_size_heading"],
            textColor=accent_color,
            alignment=_get_alignment(template_cfg["heading_align"]),
            leading=template_cfg["font_size_heading"] + 2,
            spaceBefore=max(2, section_spacing - 1),
            spaceAfter=1,
            borderWidth=1 if template_cfg.get("section_border") else 0,
            borderColor=accent_color,
            borderRadius=template_cfg.get("border_radius", 3),
            borderPadding=(3, 3, 3, 3),
        )
        styles["Heading"] = heading_style

        # Body text
        body_align = _get_alignment(template_cfg.get("body_align", "left"))
        styles["Body"] = ParagraphStyle(
            name="Body",
            fontName=template_cfg["font_body"],
            fontSize=template_cfg["font_size_body"],
            textColor=colors.black,
            alignment=body_align,
            leading=template_cfg["font_size_body"] + 2,
            spaceAfter=1,
        )

        # Small body (dates, secondary)
        styles["BodySmall"] = ParagraphStyle(
            name="BodySmall",
            fontName=template_cfg["font_body"],
            fontSize=template_cfg["font_size_body"] - 1,
            textColor=colors.HexColor("#4b5563"),
            alignment=TA_RIGHT if template_cfg.get("show_date_on_right", True) else body_align,
            leading=template_cfg["font_size_body"] + 1,
            spaceAfter=0,
        )

        # Contact info (with icons)
        styles["Contact"] = ParagraphStyle(
            name="Contact",
            fontName=template_cfg["font_body"],
            fontSize=template_cfg["font_size_body"] - 1,
            textColor=colors.HexColor("#374151"),
            alignment=_get_alignment(template_cfg.get("heading_align", "left")),
            leading=template_cfg["font_size_body"] + 1,
            spaceAfter=0,
        )

        def _append_meta_row(left_html: str, right_html: str, left_ratio: float = 0.72):
            """Consistent left/right alignment row for date/meta fields."""
            left_text = str(left_html or "").strip()
            right_text = str(right_html or "").strip()
            if left_text and right_text:
                t = Table(
                    [[Paragraph(left_text, styles["Body"]), Paragraph(right_text, styles["BodySmall"])]],
                    colWidths=[doc.width * left_ratio, doc.width * (1 - left_ratio)],
                )
                t.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ]))
                story.append(t)
            elif left_text:
                story.append(Paragraph(left_text, styles["Body"]))
            elif right_text:
                story.append(Paragraph(right_text, styles["BodySmall"]))

        def _format_location(resume_obj, sep=", "):
            """Build a clean location string from city/address without duplicates."""
            city = (getattr(resume_obj, "city", "") or "").strip()
            address = (getattr(resume_obj, "address", "") or "").strip()
            if city and address:
                if city.lower() in address.lower():
                    return address
                if address.lower() in city.lower():
                    return city
                return f"{city}{sep}{address}"
            return city or address

        def _normalize_url(url: str) -> str:
            raw = (url or "").strip()
            if not raw:
                return ""
            if raw.startswith(("http://", "https://", "mailto:", "tel:")):
                return raw
            return f"https://{raw}"

        def _link(label: str, url: str) -> str:
            target = _normalize_url(url)
            if not target:
                return html.escape(label or "")
            return f'<link href="{html.escape(target, quote=True)}">{html.escape(label or target)}</link>'

        def _format_date_range(start: str, end: str, default_present_if_start_only: bool = True) -> str:
            """Build clean date text without leading/trailing separators."""
            s = (start or "").strip()
            e = (end or "").strip()
            if s and (not e) and default_present_if_start_only:
                e = "Present"
            if s and e:
                return template_cfg["date_format"].format(start=s, end=e).strip()
            if s:
                return s
            if e:
                return e
            return ""

        # ---------- Helper: Contact with icons ----------
        def _format_contact(resume):
            """Return contact string in PDF-safe plain labels."""
            parts = []
            if resume.phone:
                parts.append(f"Phone: {resume.phone}")
            if resume.email:
                parts.append(_link(f"Email: {resume.email}", f"mailto:{resume.email}"))
            location_text = _format_location(resume)
            if location_text:
                parts.append(f"Location: {location_text}")
            if resume.linkedin:
                parts.append(_link("LinkedIn", resume.linkedin))
            if resume.github:
                parts.append(_link("GitHub", resume.github))
            if resume.twitter:
                parts.append(_link("Twitter", resume.twitter))
            if resume.website:
                parts.append(_link(f"Web: {resume.website}", resume.website))
            return " | ".join(parts)

        normalized_header_layout = str(header_layout or template_cfg.get("header_layout_default", "default")).strip().lower()
        if normalized_header_layout not in {"default", "left", "center", "split"}:
            normalized_header_layout = "default"

        # ---------- Dedicated two-column layout ----------
        if template_cfg.get("layout") == "two_column":
            story = []

            title_center_style = ParagraphStyle(
                name="TwoColTitle",
                fontName=template_cfg["font_heading"],
                fontSize=template_cfg["font_size_title"],
                textColor=colors.HexColor("#4b5563"),
                alignment=TA_CENTER,
                leading=template_cfg["font_size_title"] + 2,
                spaceAfter=2,
            )
            subtitle_center_style = ParagraphStyle(
                name="TwoColSubtitle",
                fontName=template_cfg["font_body"],
                fontSize=template_cfg["font_size_body"] + 1,
                textColor=colors.HexColor("#6b7280"),
                alignment=TA_CENTER,
                leading=template_cfg["font_size_body"] + 2,
                spaceAfter=1,
            )
            two_col_heading_style = ParagraphStyle(
                name="TwoColHeading",
                fontName=template_cfg["font_heading"],
                fontSize=template_cfg["font_size_heading"] + 2,
                textColor=accent_color,
                alignment=TA_LEFT,
                leading=template_cfg["font_size_heading"] + 2,
                spaceBefore=4,
                spaceAfter=1,
            )
            two_col_body_style = ParagraphStyle(
                name="TwoColBody",
                fontName=template_cfg["font_body"],
                fontSize=template_cfg["font_size_body"],
                textColor=colors.HexColor("#4b5563"),
                alignment=TA_LEFT,
                leading=template_cfg["font_size_body"] + 1,
                spaceAfter=0,
            )
            two_col_meta_style = ParagraphStyle(
                name="TwoColMeta",
                fontName=template_cfg["font_body"],
                fontSize=max(7, template_cfg["font_size_body"] - 1),
                textColor=colors.HexColor("#6b7280"),
                alignment=TA_LEFT,
                leading=template_cfg["font_size_body"] + 1,
                spaceAfter=0,
            )
            two_col_emphasis_style = ParagraphStyle(
                name="TwoColEmphasis",
                fontName=template_cfg["font_heading"],
                fontSize=template_cfg["font_size_body"] + 1,
                textColor=colors.HexColor("#1f2937"),
                alignment=TA_LEFT,
                leading=template_cfg["font_size_body"] + 2,
                spaceAfter=0,
            )

            def _add_section(target, title):
                target.append(Paragraph(title.upper(), two_col_heading_style))

            def _add_para(target, text, style=two_col_body_style):
                if text and str(text).strip():
                    target.append(Paragraph(str(text).strip(), style))

            # Header block
            title_left_style = ParagraphStyle("TwoColTitleLeft", parent=title_center_style, alignment=TA_LEFT)
            subtitle_left_style = ParagraphStyle("TwoColSubtitleLeft", parent=subtitle_center_style, alignment=TA_LEFT)
            subtitle_right_style = ParagraphStyle("TwoColSubtitleRight", parent=subtitle_center_style, alignment=TA_RIGHT)
            if resume.profile_pic:
                try:
                    image_align = "CENTER" if normalized_header_layout == "center" else "LEFT"
                    profile_img = PDFGenerator._build_profile_image_flowable(resume.profile_pic, align=image_align)
                    if profile_img:
                        story.append(profile_img)
                        story.append(Spacer(1, 0.08 * inch))
                except Exception as e:
                    logger.warning("Could not render profile photo in two-column PDF: %s", e)

            header_parts = []
            if resume.website:
                header_parts.append(_link(resume.website, resume.website))
            if resume.email:
                header_parts.append(_link(resume.email, f"mailto:{resume.email}"))
            if resume.phone:
                header_parts.append(resume.phone)
            location_text = _format_location(resume)
            if location_text:
                header_parts.append(location_text)

            if normalized_header_layout == "split":
                left_bits = []
                if resume.full_name:
                    left_bits.append(Paragraph(resume.full_name, title_left_style))
                if resume.profile_title:
                    left_bits.append(Paragraph(resume.profile_title, subtitle_left_style))
                right_text = " | ".join(header_parts)
                right_para = Paragraph(right_text, subtitle_right_style) if right_text else Paragraph("", subtitle_right_style)
                split_header = Table([[left_bits, right_para]], colWidths=[doc.width * 0.62, doc.width * 0.38])
                split_header.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (0, 0), (0, 0), "LEFT"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]))
                story.append(split_header)
            else:
                title_style = title_center_style if normalized_header_layout == "center" else title_left_style
                sub_style = subtitle_center_style if normalized_header_layout == "center" else subtitle_left_style
                if resume.full_name:
                    story.append(Paragraph(resume.full_name, title_style))
                if resume.profile_title:
                    story.append(Paragraph(resume.profile_title, sub_style))
                if header_parts:
                    story.append(Paragraph(" | ".join(header_parts), sub_style))

            story.append(
                HRFlowable(
                    width="100%",
                    thickness=0.9,
                    color=colors.HexColor("#9ca3af"),
                    spaceBefore=2,
                    spaceAfter=4,
                )
            )

            left_col = []
            right_col = []

            # Left column: objective, education, links, skills
            if resume.summary and resume.summary.strip():
                _add_section(left_col, "Objective")
                _add_para(left_col, resume.summary.replace("\n", "<br/>"))

            if resume.educations:
                _add_section(left_col, "Education")
                for edu in resume.educations:
                    _add_para(left_col, f"{edu.institution}", two_col_body_style)
                    _add_para(left_col, edu.degree)
                    date_bits = [x for x in [edu.start_date, edu.end_date] if x]
                    if date_bits:
                        _add_para(left_col, " - ".join(date_bits), two_col_meta_style)
                    if edu.description:
                        _add_para(left_col, edu.description, two_col_meta_style)
                    left_col.append(Spacer(1, 1))

            link_lines = []
            if resume.linkedin:
                link_lines.append(f"LinkedIn: {_link(resume.linkedin, resume.linkedin)}")
            if resume.github:
                link_lines.append(f"GitHub: {_link(resume.github, resume.github)}")
            if resume.twitter:
                link_lines.append(f"Twitter: {_link(resume.twitter, resume.twitter)}")
            if resume.website:
                link_lines.append(f"Website: {_link(resume.website, resume.website)}")
            if link_lines:
                _add_section(left_col, "Links")
                for line in link_lines:
                    _add_para(left_col, line, two_col_meta_style)

            if resume.skills:
                _add_section(left_col, "Skills")
                for skill in sorted(resume.skills):
                    _add_para(left_col, skill)

            # Right column: experience, projects, training/certs, achievements
            if resume.experiences:
                _add_section(right_col, "Experience")
                for exp in resume.experiences:
                    top_line = ""
                    if exp.company and exp.job_title:
                        top_line = f"{exp.company.upper()} | {exp.job_title.upper()}"
                    elif exp.job_title:
                        top_line = f"{exp.job_title.upper()}"
                    elif exp.company:
                        top_line = f"{exp.company.upper()}"
                    _add_para(right_col, top_line, two_col_body_style)

                    date_place_bits = []
                    if exp.start_date or exp.end_date:
                        date_place_bits.append(_format_date_range(exp.start_date, exp.end_date, True))
                    location_text = _format_location(resume)
                    if location_text:
                        date_place_bits.append(location_text)
                    if date_place_bits:
                        _add_para(right_col, " | ".join(date_place_bits), two_col_meta_style)

                    if exp.description:
                        for line in exp.description.split("\n"):
                            if line.strip():
                                _add_para(right_col, f"- {line.strip()}", two_col_body_style)
                    right_col.append(Spacer(1, 1))

            if resume.projects:
                _add_section(right_col, "Projects")
                for proj in resume.projects:
                    _add_para(right_col, f"{proj.name.upper()}", two_col_body_style)
                    meta_bits = []
                    if proj.start_date or proj.end_date:
                        proj_date = _format_date_range(proj.start_date, proj.end_date, False)
                        if proj_date:
                            meta_bits.append(proj_date)
                    if proj.role:
                        meta_bits.append(proj.role)
                    if meta_bits:
                        _add_para(right_col, " | ".join(meta_bits), two_col_meta_style)
                    if proj.description:
                        _add_para(right_col, proj.description)
                    right_col.append(Spacer(1, 1))

            if resume.certifications:
                _add_section(right_col, "Training")
                for cert in resume.certifications:
                    _add_para(right_col, f"{cert.name.upper()}", two_col_body_style)
                    cert_meta = " | ".join([x for x in [cert.issuer, cert.date] if x])
                    if cert_meta:
                        _add_para(right_col, cert_meta, two_col_meta_style)
                    if cert.link:
                        _add_para(right_col, cert.link, two_col_meta_style)

            if resume.achievements:
                _add_section(right_col, "Achievements")
                for ach in resume.achievements:
                    _add_para(right_col, f"{ach.title}", two_col_body_style)
                    if ach.subtitle:
                        _add_para(right_col, ach.subtitle, two_col_meta_style)
                    if ach.description:
                        _add_para(right_col, ach.description)

            left_ratio = float(template_cfg.get("left_column_ratio", 0.32))
            left_ratio = min(0.45, max(0.22, left_ratio))
            two_col_table = Table(
                [[left_col, right_col]],
                colWidths=[doc.width * left_ratio, doc.width * (1 - left_ratio)],
            )
            two_col_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
                ("RIGHTPADDING", (0, 0), (0, -1), 12),
                ("LEFTPADDING", (1, 0), (1, -1), 8),
                ("RIGHTPADDING", (1, 0), (1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            story.append(two_col_table)

            doc.build(story, onFirstPage=_draw_page_border, onLaterPages=_draw_page_border)
            return output

        # ---------- Story ----------
        story = []

        # ----- Profile Photo (if uploaded) -----
        if resume.profile_pic:
            try:
                image_align = {
                    "left": "LEFT",
                    "center": "CENTER",
                    "right": "RIGHT",
                }.get(template_cfg.get("heading_align", "left"), "LEFT")
                profile_img = PDFGenerator._build_profile_image_flowable(resume.profile_pic, align=image_align)
                if profile_img:
                    story.append(profile_img)
                    story.append(Spacer(1, 0.1 * inch))
            except Exception as e:
                logger.warning("Could not render profile photo in PDF: %s", e)

        # ----- Logo (optional) -----
        if os.path.exists(AppConfig.LOGO_PATH):
            try:
                logo = Image(AppConfig.LOGO_PATH, width=1.2 * inch, height=0.4 * inch)
                logo.hAlign = {
                    "left": "LEFT",
                    "center": "CENTER",
                    "right": "RIGHT",
                }.get(template_cfg.get("heading_align", "left"), "LEFT")
                story.append(logo)
                story.append(Spacer(1, 0.1 * inch))
            except:
                pass

        # Prepare contact strings once; reused for different header layouts.
        contact_lines = []
        if resume.email:
            contact_lines.append(_link(f"Email: {resume.email}", f"mailto:{resume.email}"))
        if resume.phone:
            contact_lines.append(f"Phone: {resume.phone}")
        location_text = _format_location(resume)
        if location_text:
            contact_lines.append(f"Location: {location_text}")
        social_lines = []
        if resume.linkedin:
            social_lines.append(f"LinkedIn: {_link(resume.linkedin, resume.linkedin)}")
        if resume.github:
            social_lines.append(f"GitHub: {_link(resume.github, resume.github)}")
        if resume.twitter:
            social_lines.append(f"Twitter: {_link(resume.twitter, resume.twitter)}")
        if resume.website:
            social_lines.append(f"Web: {_link(resume.website, resume.website)}")
        icon_contact_text = _format_contact(resume) if template_cfg.get("contact_icons", False) else ""
        plain_contact_text = "<br/>".join(contact_lines + social_lines)

        normalized_header_layout = str(header_layout or template_cfg.get("header_layout_default", "default")).strip().lower()
        if normalized_header_layout not in {"default", "left", "center", "split"}:
            normalized_header_layout = "default"

        # ----- Header block -----
        if normalized_header_layout == "split":
            left_bits = []
            if resume.full_name:
                left_bits.append(Paragraph(resume.full_name, styles["Title"]))
            if resume.profile_title:
                left_bits.append(Paragraph(resume.profile_title, styles["ProfileTitle"]))
            if (not left_bits) and resume.full_name:
                left_bits.append(Paragraph(resume.full_name, styles["Title"]))

            right_text = icon_contact_text or plain_contact_text
            right_para = Paragraph(right_text, styles["Contact"]) if right_text else Paragraph("", styles["Contact"])
            header_table = Table([[left_bits, right_para]], colWidths=[doc.width * 0.62, doc.width * 0.38])
            header_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (0, 0), "LEFT"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            story.append(header_table)
            story.append(Spacer(1, section_tail_spacing))
        else:
            # left/default/center use standard stacked header.
            title_style = styles["Title"]
            profile_style = styles["ProfileTitle"]
            contact_style = styles["Contact"]
            if normalized_header_layout == "center":
                title_style = ParagraphStyle("HeaderTitleCenter", parent=styles["Title"], alignment=TA_CENTER)
                profile_style = ParagraphStyle("HeaderProfileCenter", parent=styles["ProfileTitle"], alignment=TA_CENTER)
                contact_style = ParagraphStyle("HeaderContactCenter", parent=styles["Contact"], alignment=TA_CENTER)
            if resume.full_name:
                story.append(Paragraph(resume.full_name, title_style))
            if resume.profile_title:
                story.append(Paragraph(resume.profile_title, profile_style))
            contact_text = icon_contact_text or plain_contact_text
            if contact_text:
                story.append(Paragraph(contact_text, contact_style))
                story.append(Spacer(1, max(1, item_spacing - 1)))

        # ----- QR Link (optional) -----
        if getattr(resume, "qr_link", None):
            qr_text = str(resume.qr_link).strip()
            if qr_text:
                try:
                    from reportlab.graphics.barcode import qr as rl_qr
                    from reportlab.graphics.shapes import Drawing
                    qr_widget = rl_qr.QrCodeWidget(qr_text)
                    b = qr_widget.getBounds()
                    w = max(1, b[2] - b[0])
                    h = max(1, b[3] - b[1])
                    size = 62
                    drawing = Drawing(size, size, transform=[size / w, 0, 0, size / h, 0, 0])
                    drawing.add(qr_widget)
                    story.append(drawing)
                    story.append(Paragraph(f"<i>QR:</i> {qr_text}", styles["Body"]))
                except Exception as e:
                    logger.warning("Could not render QR code: %s", e)
                    story.append(Paragraph(f"<i>QR:</i> {qr_text}", styles["Body"]))
                story.append(Spacer(1, section_tail_spacing))

            story.append(
                HRFlowable(
                    width="100%",
                    thickness=0.8,
                    color=accent_color,
                    spaceBefore=1,
                    spaceAfter=max(2, section_spacing - 1),
                )
            )

        normalized_section_order = []
        visibility = section_visibility or {}
        def _is_visible(key: str) -> bool:
            return bool(visibility.get(key, True))

        if section_order:
            allowed = {"summary", "experience", "education", "projects", "skills", "achievements", "custom"}
            for key in section_order:
                k = str(key).strip().lower()
                if k in allowed and k not in normalized_section_order:
                    normalized_section_order.append(k)
        use_ordered_sections = bool(normalized_section_order)

        def _render_summary():
            if _is_visible("summary") and resume.summary and resume.summary.strip():
                story.append(Paragraph("ABOUT ME" if template_name in ["corporate", "elegant_light"] else "SUMMARY", styles["Heading"]))
                story.append(Paragraph(resume.summary.replace("\n", "<br/>"), styles["Body"]))
                story.append(Spacer(1, section_tail_spacing))

        def _render_experience():
            if (not _is_visible("experience")) or (not resume.experiences):
                return
            story.append(Paragraph("WORK EXPERIENCE", styles["Heading"]))
            for exp in resume.experiences:
                title_company = f"{exp.job_title}"
                if exp.company:
                    title_company += f" at {exp.company}"
                has_date = bool((exp.start_date and exp.start_date.strip()) or (exp.end_date and exp.end_date.strip()))
                if has_date:
                    date_str = _format_date_range(exp.start_date, exp.end_date, True)
                    _append_meta_row(title_company, date_str)
                else:
                    story.append(Paragraph(title_company, styles["Body"]))
                if exp.description:
                    bullet = template_cfg.get("bullet", "-")
                    for line in exp.description.strip().split("\n"):
                        if line.strip():
                            story.append(Paragraph(f"{bullet} {line}", styles["Body"]))
                story.append(Spacer(1, section_tail_spacing))

        def _render_education():
            if (not _is_visible("education")) or (not resume.educations):
                return
            story.append(Paragraph("EDUCATION", styles["Heading"]))
            if template_cfg.get("education_table", False):
                table_data = []
                for edu in resume.educations:
                    course = f"{edu.degree}"
                    if edu.institution:
                        course += f"<br/>{edu.institution}"
                    table_data.append([course])
                t = Table(table_data, colWidths=[doc.width])
                t.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                    ('INNERGRID', (0, 0), (-1, -1), 0, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0, colors.white),
                    ('LEFTPADDING', (0, 0), (-1, -1), 2),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                    ('TOPPADDING', (0, 0), (-1, -1), 2),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ]))
                story.append(t)
            else:
                for edu in resume.educations:
                    degree_inst = f"{edu.degree}"
                    if edu.institution:
                        degree_inst += f" at {edu.institution}"
                    date_str = _format_date_range(edu.start_date, edu.end_date, False)
                    if date_str:
                        _append_meta_row(degree_inst, date_str)
                    else:
                        story.append(Paragraph(degree_inst, styles["Body"]))
                    if edu.description:
                        story.append(Paragraph(edu.description, styles["Body"]))
                    story.append(Spacer(1, section_tail_spacing))

        def _render_projects():
            if (not _is_visible("projects")) or (not resume.projects):
                return
            story.append(Paragraph("PROJECTS", styles["Heading"]))
            for proj in resume.projects:
                proj_name = f"{proj.name}"
                if proj.role:
                    proj_name += f" - {proj.role}"
                date_str = _format_date_range(proj.start_date, proj.end_date, False)
                if proj.start_date or proj.end_date:
                    _append_meta_row(proj_name, date_str)
                else:
                    story.append(Paragraph(proj_name, styles["Body"]))
                if proj.technologies:
                    story.append(Paragraph(f"<i>Technologies:</i> {proj.technologies}", styles["Body"]))
                if proj.description:
                    bullet = template_cfg.get("bullet", "-")
                    for line in proj.description.strip().split("\n"):
                        if line.strip():
                            story.append(Paragraph(f"{bullet} {line}", styles["Body"]))
                if proj.link:
                    story.append(Paragraph(f"<i>Link:</i> {proj.link}", styles["Body"]))
                story.append(Spacer(1, section_tail_spacing))

        def _render_skills():
            if (not _is_visible("skills")) or (not resume.skills):
                return
            story.append(Paragraph("SKILLS", styles["Heading"]))
            bullet = template_cfg.get("bullet", "-")
            for skill in sorted(resume.skills):
                story.append(Paragraph(f"{bullet} {skill}", styles["Body"]))
            story.append(Spacer(1, section_tail_spacing))

        def _render_achievements():
            if (not _is_visible("achievements")) or (not resume.achievements):
                return
            story.append(Paragraph("ACHIEVEMENTS", styles["Heading"]))
            for ach in resume.achievements:
                story.append(Paragraph(f"{ach.title}", styles["Body"]))
                if ach.subtitle:
                    story.append(Paragraph(ach.subtitle, styles["BodySmall"]))
                if ach.description:
                    story.append(Paragraph(ach.description, styles["Body"]))
                story.append(Spacer(1, section_tail_spacing))

        def _render_custom_sections():
            if (not _is_visible("custom")) or (not getattr(resume, "custom_sections", None)):
                return
            for section in resume.custom_sections:
                title = str(section.get("title", "")).strip()
                items = section.get("items") or []
                if not title or not items:
                    continue
                story.append(Paragraph(title.upper(), styles["Heading"]))
                bullet = template_cfg.get("bullet", "-")
                for item in items:
                    line = str(item).strip()
                    if line:
                        story.append(Paragraph(f"{bullet} {line}", styles["Body"]))
                story.append(Spacer(1, section_tail_spacing))

        if use_ordered_sections:
            renderers = {
                "summary": _render_summary,
                "experience": _render_experience,
                "education": _render_education,
                "projects": _render_projects,
                "skills": _render_skills,
                "achievements": _render_achievements,
                "custom": _render_custom_sections,
            }
            for key in normalized_section_order:
                renderer = renderers.get(key)
                if renderer:
                    renderer()

        # ----- SUMMARY / ABOUT ME -----
        if (not use_ordered_sections) and _is_visible("summary") and resume.summary and resume.summary.strip():
            story.append(Paragraph("ABOUT ME" if template_name in ["corporate", "elegant_light"] else "SUMMARY", styles["Heading"]))
            story.append(Paragraph(resume.summary.replace("\n", "<br/>"), styles["Body"]))
            story.append(Spacer(1, section_tail_spacing))

        # ----- WORK EXPERIENCE -----
        if (not use_ordered_sections) and _is_visible("experience") and resume.experiences:
            story.append(Paragraph("WORK EXPERIENCE", styles["Heading"]))
            for exp in resume.experiences:
                # Title & company (left) / Date (right)
                title_company = f"{exp.job_title}"
                if exp.company:
                    title_company += f" at {exp.company}"

                has_date = bool((exp.start_date and exp.start_date.strip()) or (exp.end_date and exp.end_date.strip()))
                if has_date:
                    date_str = _format_date_range(exp.start_date, exp.end_date, True)
                    _append_meta_row(title_company, date_str)
                else:
                    story.append(Paragraph(title_company, styles["Body"]))

                # Description with bullet points
                if exp.description:
                    desc_lines = exp.description.strip().split("\n")
                    bullet = template_cfg.get("bullet", "-")
                    for line in desc_lines:
                        if line.strip():
                            story.append(Paragraph(f"{bullet} {line}", styles["Body"]))
                story.append(Spacer(1, section_tail_spacing))

        # ----- EDUCATION (as Table, if enabled) -----
        if (not use_ordered_sections) and _is_visible("education") and resume.educations:
            story.append(Paragraph("EDUCATION", styles["Heading"]))

            if template_cfg.get("education_table", False):
                # Create compact education rows
                table_data = []
                for edu in resume.educations:
                    course = f"{edu.degree}"
                    if edu.institution:
                        course += f"<br/>{edu.institution}"
                    table_data.append([course])

                # Calculate column widths
                col_widths = [doc.width]
                t = Table(table_data, colWidths=col_widths)
                t.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                    ('INNERGRID', (0, 0), (-1, -1), 0, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0, colors.white),
                    ('LEFTPADDING', (0, 0), (-1, -1), 2),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                    ('TOPPADDING', (0, 0), (-1, -1), 2),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ]))
                story.append(t)
            else:
                # Traditional education layout (with date on right)
                for edu in resume.educations:
                    degree_inst = f"{edu.degree}"
                    if edu.institution:
                        degree_inst += f" at {edu.institution}"
                    date_str = _format_date_range(edu.start_date, edu.end_date, False)
                    degree_text_l = degree_inst.strip().lower()
                    date_text_l = str(date_str or "").strip().lower()
                    date_already_in_text = bool(date_text_l and date_text_l in degree_text_l)
                    if date_str:
                        if date_already_in_text:
                            story.append(Paragraph(degree_inst, styles["Body"]))
                        else:
                            data = [
                                [Paragraph(degree_inst, styles["Body"]),
                                 Paragraph(date_str, styles["BodySmall"])]
                            ]
                            t = Table(data, colWidths=[doc.width * 0.72, doc.width * 0.28])
                            t.setStyle(TableStyle([
                                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                                ('TOPPADDING', (0, 0), (-1, -1), 0),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                            ]))
                            story.append(t)
                    else:
                        story.append(Paragraph(degree_inst, styles["Body"]))
                    if edu.description:
                        story.append(Paragraph(edu.description, styles["Body"]))
                    story.append(Spacer(1, section_tail_spacing))

        # ----- PROJECTS -----
        if (not use_ordered_sections) and _is_visible("projects") and resume.projects:
            story.append(Paragraph("PROJECTS", styles["Heading"]))
            for proj in resume.projects:
                proj_name = f"{proj.name}"
                if proj.role:
                    proj_name += f" â€” {proj.role}"
                date_str = _format_date_range(proj.start_date, proj.end_date, False)
                if proj.start_date or proj.end_date:
                    _append_meta_row(proj_name, date_str)
                else:
                    story.append(Paragraph(proj_name, styles["Body"]))

                if proj.technologies:
                    story.append(Paragraph(f"<i>Technologies:</i> {proj.technologies}", styles["Body"]))
                if proj.description:
                    desc_lines = proj.description.strip().split("\n")
                    bullet = template_cfg.get("bullet", "-")
                    for line in desc_lines:
                        if line.strip():
                            story.append(Paragraph(f"{bullet} {line}", styles["Body"]))
                if proj.link:
                    story.append(Paragraph(f"<i>Link:</i> {proj.link}", styles["Body"]))
                story.append(Spacer(1, section_tail_spacing))

        # ----- CERTIFICATIONS -----
        if _is_visible("certifications") and resume.certifications:
            story.append(Paragraph("CERTIFICATIONS", styles["Heading"]))
            for cert in resume.certifications:
                cert_name = f"{cert.name}"
                if cert.issuer:
                    cert_name += f" â€” {cert.issuer}"
                if cert.date:
                    _append_meta_row(cert_name, cert.date)
                else:
                    story.append(Paragraph(cert_name, styles["Body"]))
                if cert.link:
                    story.append(Paragraph(f"<i>Credential:</i> {cert.link}", styles["Body"]))
                story.append(Spacer(1, section_tail_spacing))

        # ----- LANGUAGES -----
        if _is_visible("languages") and resume.languages:
            story.append(Paragraph("LANGUAGES", styles["Heading"]))
            for lang in resume.languages:
                _append_meta_row(f"{lang.name}", lang.proficiency)
            story.append(Spacer(1, section_tail_spacing))

        # ----- SKILLS -----
        if (not use_ordered_sections) and _is_visible("skills") and resume.skills:
            story.append(Paragraph("SKILLS", styles["Heading"]))
            # Bullet list style
            bullet = template_cfg.get("bullet", "-")
            for skill in sorted(resume.skills):
                story.append(Paragraph(f"{bullet} {skill}", styles["Body"]))
            story.append(Spacer(1, section_tail_spacing))

        # ----- ACHIEVEMENTS -----
        if (not use_ordered_sections) and _is_visible("achievements") and resume.achievements:
            story.append(Paragraph("ACHIEVEMENTS", styles["Heading"]))
            for ach in resume.achievements:
                story.append(Paragraph(f"{ach.title}", styles["Body"]))
                if ach.subtitle:
                    story.append(Paragraph(ach.subtitle, styles["BodySmall"]))
                if ach.description:
                    story.append(Paragraph(ach.description, styles["Body"]))
                story.append(Spacer(1, section_tail_spacing))

        # ----- REFERENCES (Two-Column if enabled) -----
        if _is_visible("references") and resume.references:
            story.append(Paragraph("REFERENCES", styles["Heading"]))

            if template_cfg.get("references_two_column", False):
                # Create two-column table for references
                refs = resume.references
                # Pair them up
                rows = []
                for i in range(0, len(refs), 2):
                    row = []
                    # Left reference
                    left = refs[i]
                    left_text = f"{left.name}"
                    if left.title:
                        left_text += f"<br/>{left.title}"
                    if left.company:
                        left_text += f"<br/>{left.company}"
                    if left.phone:
                        left_text += f"<br/>ðŸ“ž {left.phone}"
                    if left.email:
                        left_text += f"<br/>ðŸ“§ {left.email}"
                    if left.website:
                        left_text += f"<br/>ðŸŒ {left.website}"
                    row.append(Paragraph(left_text, styles["Body"]))

                    # Right reference (if exists)
                    if i + 1 < len(refs):
                        right = refs[i + 1]
                        right_text = f"{right.name}"
                        if right.title:
                            right_text += f"<br/>{right.title}"
                        if right.company:
                            right_text += f"<br/>{right.company}"
                        if right.phone:
                            right_text += f"<br/>ðŸ“ž {right.phone}"
                        if right.email:
                            right_text += f"<br/>ðŸ“§ {right.email}"
                        if right.website:
                            right_text += f"<br/>ðŸŒ {right.website}"
                        row.append(Paragraph(right_text, styles["Body"]))
                    else:
                        row.append("")
                    rows.append(row)

                t = Table(rows, colWidths=[doc.width / 2.0 - 12, doc.width / 2.0 - 12])
                t.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 2),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                    ('TOPPADDING', (0, 0), (-1, -1), 2),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ]))
                story.append(t)
            else:
                # Traditional one-per-line
                for ref in resume.references:
                    ref_text = f"{ref.name}"
                    if ref.title:
                        ref_text += f" â€” {ref.title}"
                    if ref.company:
                        ref_text += f", {ref.company}"
                    story.append(Paragraph(ref_text, styles["Body"]))
                    if ref.phone:
                        story.append(Paragraph(f"ðŸ“ž {ref.phone}", styles["Body"]))
                    if ref.email:
                        story.append(Paragraph(f"ðŸ“§ {ref.email}", styles["Body"]))
                    if ref.website:
                        story.append(Paragraph(f"ðŸŒ {ref.website}", styles["Body"]))
                    story.append(Spacer(1, section_tail_spacing))

        # ----- CUSTOM SECTIONS -----
        if (not use_ordered_sections) and _is_visible("custom") and getattr(resume, "custom_sections", None):
            for section in resume.custom_sections:
                title = str(section.get("title", "")).strip()
                items = section.get("items") or []
                if not title or not items:
                    continue
                story.append(Paragraph(title.upper(), styles["Heading"]))
                bullet = template_cfg.get("bullet", "-")
                for item in items:
                    line = str(item).strip()
                    if line:
                        story.append(Paragraph(f"{bullet} {line}", styles["Body"]))
                story.append(Spacer(1, section_tail_spacing))

        # Build the PDF
        doc.build(story, onFirstPage=_draw_page_border, onLaterPages=_draw_page_border)
        return output


