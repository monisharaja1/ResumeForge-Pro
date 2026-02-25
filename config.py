"""Configuration and templates for ResumeBuilder."""

import os
from typing import Any, Dict


class AppConfig:
    APP_NAME = "ResumeBuilder Pro"
    APP_VERSION = "3.0.0"
    DB_PATH = "resume.db"
    LOGO_PATH = "assets/logo.png"
    BACKUP_DIR = "backups"
    DEFAULT_TEMPLATE = "modern"
    DEFAULT_FONT = "Helvetica"
    ACCENT_COLOR = "#2c3e50"
    DATE_FORMAT = "%Y-%m-%d"
    MAX_RECENT_FILES = 10

    # PDF templates used by pdf_generator.py
    TEMPLATES: Dict[str, Dict[str, Any]] = {

        # ðŸ”¥ MODERN PREMIUM TEMPLATE
        "modern": {
            "name": "Modern Premium",
            "font_heading": "Helvetica-Bold",
            "font_body": "Helvetica",

            # Better sizing
            "font_size_title": 26,
            "font_size_heading": 13,
            "font_size_body": 10,

            # Professional navy accent
            "accent": "#1e293b",
            "background": "#ffffff",

            # Clean layout
            "section_border": False,
            "layout": "single",

            # Alignment
            "heading_align": "left",
            "body_align": "left",

            # Professional bullet
            "bullet": "-",

            "show_date_on_right": True,
            "date_format": "{start} - {end}",

            "spacing": 14,
            "border_radius": 4,

            # Premium features
            "contact_icons": False,
            "education_table": False,
            "references_two_column": True,
        },

        # CORPORATE TEMPLATE
        "corporate": {
            "name": "Corporate",
            "font_heading": "Helvetica-Bold",
            "font_body": "Helvetica",
            "font_size_title": 28,
            "font_size_heading": 14,
            "font_size_body": 11,
            "accent": "#1e3a5f",
            "background": "#ffffff",
            "section_border": False,
            "layout": "single",
            "heading_align": "left",
            "body_align": "left",
            "bullet": "-",
            "show_date_on_right": True,
            "date_format": "{start} - {end}",
            "spacing": 14,
            "border_radius": 0,
            "contact_icons": False,
            "education_table": False,
            "references_two_column": True,
        },

        # CLASSIC TEMPLATE
        "classic": {
            "name": "Classic",
            "font_heading": "Times-Bold",
            "font_body": "Times-Roman",
            "font_size_title": 27,
            "font_size_heading": 13,
            "font_size_body": 10,
            "accent": "#2b3a55",
            "background": "#ffffff",
            "section_border": False,
            "layout": "single",
            "heading_align": "left",
            "body_align": "left",
            "bullet": "*",
            "show_date_on_right": True,
            "date_format": "{start} - {end}",
            "spacing": 12,
            "border_radius": 0,
            "contact_icons": False,
            "education_table": False,
            "references_two_column": False,
        },

        # COMPACT TEMPLATE
        "compact": {
            "name": "Compact",
            "font_heading": "Helvetica-Bold",
            "font_body": "Helvetica",
            "font_size_title": 22,
            "font_size_heading": 12,
            "font_size_body": 9,
            "accent": "#0f766e",
            "background": "#ffffff",
            "section_border": False,
            "layout": "single",
            "heading_align": "left",
            "body_align": "left",
            "bullet": "-",
            "show_date_on_right": True,
            "date_format": "{start} - {end}",
            "spacing": 10,
            "border_radius": 0,
            "contact_icons": False,
            "education_table": False,
            "references_two_column": False,
        },

        # EXECUTIVE TEMPLATE
        "executive": {
            "name": "Executive",
            "font_heading": "Times-Bold",
            "font_body": "Times-Roman",
            "font_size_title": 30,
            "font_size_heading": 14,
            "font_size_body": 11,
            "accent": "#111827",
            "background": "#ffffff",
            "section_border": False,
            "layout": "single",
            "heading_align": "left",
            "body_align": "left",
            "bullet": "*",
            "show_date_on_right": True,
            "date_format": "{start} - {end}",
            "spacing": 15,
            "border_radius": 2,
            "contact_icons": False,
            "education_table": False,
            "references_two_column": True,
        },

        # GRAY/ORANGE - inspired by visual CV cards
        "snack_gray": {
            "name": "Snack Gray",
            "font_heading": "Helvetica-Bold",
            "font_body": "Helvetica",
            "font_size_title": 25,
            "font_size_heading": 12,
            "font_size_body": 9,
            "accent": "#d65b2e",
            "background": "#f3f4f6",
            "section_border": False,
            "layout": "single",
            "heading_align": "left",
            "body_align": "left",
            "bullet": "-",
            "show_date_on_right": True,
            "date_format": "{start} - {end}",
            "spacing": 11,
            "border_radius": 0,
            "page_border": False,
            "contact_icons": False,
            "education_table": False,
            "references_two_column": False,
        },

        # ACADEMIC BLUE - clean and text-forward
        "vision_blue": {
            "name": "Vision Blue",
            "font_heading": "Helvetica-Bold",
            "font_body": "Helvetica",
            "font_size_title": 24,
            "font_size_heading": 12,
            "font_size_body": 9,
            "accent": "#1f4e96",
            "background": "#ffffff",
            "section_border": False,
            "layout": "single",
            "heading_align": "left",
            "body_align": "left",
            "bullet": "-",
            "show_date_on_right": True,
            "date_format": "{start} - {end}",
            "spacing": 10,
            "border_radius": 0,
            "page_border": False,
            "contact_icons": False,
            "education_table": False,
            "references_two_column": False,
        },

        # MINIMAL MONO - centered header with concise sections
        "harsh_minimal": {
            "name": "Harsh Minimal",
            "font_heading": "Helvetica-Bold",
            "font_body": "Helvetica",
            "font_size_title": 26,
            "font_size_heading": 11,
            "font_size_body": 9,
            "accent": "#111827",
            "background": "#ffffff",
            "section_border": False,
            "layout": "single",
            "heading_align": "center",
            "body_align": "left",
            "bullet": "-",
            "show_date_on_right": True,
            "date_format": "{start} - {end}",
            "spacing": 10,
            "border_radius": 0,
            "page_border": False,
            "contact_icons": False,
            "education_table": False,
            "references_two_column": False,
        },

        # CLEAN TWO-COLUMN - inspired by minimalist profile layout
        "javid_split": {
            "name": "Javid Split",
            "font_heading": "Helvetica-Bold",
            "font_body": "Helvetica",
            "font_size_title": 32,
            "font_size_heading": 10,
            "font_size_body": 9,
            "accent": "#6b7280",
            "background": "#ffffff",
            "section_border": False,
            "layout": "two_column",
            "left_column_ratio": 0.32,
            "heading_align": "left",
            "body_align": "left",
            "bullet": "-",
            "show_date_on_right": True,
            "date_format": "{start} - {end}",
            "spacing": 10,
            "border_radius": 0,
            "page_border": False,
            "contact_icons": False,
            "education_table": False,
            "references_two_column": False,
        },

        # à®ªà¯à®¤à®¿à®¯ à®Ÿà¯†à®®à¯à®ªà¯à®³à¯‡à®Ÿà¯: TEAL MODERN
        "teal_modern": {
            "name": "Teal Modern",
            "font_heading": "Helvetica-Bold",
            "font_body": "Helvetica",
            "font_size_title": 28,
            "font_size_heading": 13,
            "font_size_body": 10,
            "accent": "#008080",       # à®Ÿà¯€à®²à¯ (Teal) à®¨à®¿à®±à®®à¯
            "background": "#ffffff",
            "section_border": False,    # à®¤à®²à¯ˆà®ªà¯à®ªà¯à®•à¯à®•à¯ à®•à¯€à®´à¯‡ à®•à¯‹à®Ÿà¯
            "layout": "single",
            "heading_align": "left",
            "body_align": "left",
            "bullet": "-",             # à®ªà¯à®²à¯à®²à®Ÿà¯ à®¸à¯à®Ÿà¯ˆà®²à¯
            "show_date_on_right": True,
            "date_format": "{start} | {end}",
            "spacing": 13,
            "page_border": False,
            "contact_icons": False,
            "education_table": False,
            "references_two_column": True,
        },
    }

# ---------------- Template Architecture ----------------
# Keep existing templates and future custom templates in separate registries.
AppConfig.LEGACY_TEMPLATES: Dict[str, Dict[str, Any]] = dict(AppConfig.TEMPLATES)

AppConfig.SIGNATURE_TEMPLATES: Dict[str, Dict[str, Any]] = {
    # ASTRA CLEAN - ATS-safe minimal with modern teal accent
    "astra_clean": {
        "name": "Astra Clean",
        "font_heading": "Helvetica-Bold",
        "font_body": "Helvetica",
        "font_size_title": 27,
        "font_size_heading": 13,
        "font_size_body": 10,
        "accent": "#0f766e",
        "background": "#ffffff",
        "section_border": False,
        "layout": "single",
        "heading_align": "left",
        "body_align": "left",
        "bullet": "-",
        "show_date_on_right": True,
        "date_format": "{start} - {end}",
        "spacing": 13,
            "page_border": False,
        "border_radius": 0,
        "contact_icons": False,
        "education_table": False,
        "references_two_column": True,
    },
    # METRO SIDEBAR - high-contrast two-column profile
    "metro_sidebar": {
        "name": "Metro Sidebar",
        "font_heading": "Helvetica-Bold",
        "font_body": "Helvetica",
        "font_size_title": 31,
        "font_size_heading": 11,
        "font_size_body": 9,
        "accent": "#155e75",
        "background": "#ffffff",
        "section_border": False,
        "layout": "two_column",
        "left_column_ratio": 0.33,
        "heading_align": "left",
        "body_align": "left",
        "bullet": "-",
        "show_date_on_right": True,
        "date_format": "{start} - {end}",
        "spacing": 10,
        "border_radius": 0,
        "page_border": False,
        "contact_icons": False,
        "education_table": False,
        "references_two_column": False,
    },
    # EXECUTIVE SLATE - premium enterprise profile tone
    "executive_slate": {
        "name": "Executive Slate",
        "font_heading": "Times-Bold",
        "font_body": "Times-Roman",
        "font_size_title": 32,
        "font_size_heading": 14,
        "font_size_body": 11,
        "accent": "#1f2937",
        "background": "#ffffff",
        "section_border": False,
        "layout": "single",
        "heading_align": "left",
        "body_align": "left",
        "bullet": "*",
        "show_date_on_right": True,
        "date_format": "{start} - {end}",
        "spacing": 15,
        "border_radius": 2,
        "contact_icons": False,
        "education_table": False,
        "references_two_column": True,
    },
    # CREATIVE SPLIT - modern profile story layout
    "creative_split": {
        "name": "Creative Split",
        "font_heading": "Helvetica-Bold",
        "font_body": "Helvetica",
        "font_size_title": 30,
        "font_size_heading": 11,
        "font_size_body": 9,
        "accent": "#9333ea",
        "background": "#ffffff",
        "section_border": False,
        "layout": "two_column",
        "left_column_ratio": 0.34,
        "heading_align": "left",
        "body_align": "left",
        "bullet": "-",
        "show_date_on_right": True,
        "date_format": "{start} - {end}",
        "spacing": 10,
        "border_radius": 0,
        "page_border": False,
        "contact_icons": False,
        "education_table": False,
        "references_two_column": False,
    },
    # MONO COMPACT - dense one-page minimalist output
    "mono_compact": {
        "name": "Mono Compact",
        "font_heading": "Helvetica-Bold",
        "font_body": "Helvetica",
        "font_size_title": 23,
        "font_size_heading": 11,
        "font_size_body": 9,
        "accent": "#111827",
        "background": "#ffffff",
        "section_border": False,
        "layout": "single",
        "heading_align": "left",
        "body_align": "left",
        "bullet": "-",
        "show_date_on_right": True,
        "date_format": "{start} - {end}",
        "spacing": 9,
        "border_radius": 0,
        "contact_icons": False,
        "education_table": False,
        "references_two_column": False,
    },
    # CLASSIC CLARITY - clean traditional single-column
    "classic_clarity": {
        "name": "Classic Clarity",
        "font_heading": "Helvetica-Bold",
        "font_body": "Helvetica",
        "font_size_title": 28,
        "font_size_heading": 12,
        "font_size_body": 9,
        "accent": "#2563eb",
        "background": "#ffffff",
        "section_border": False,
        "layout": "single",
        "heading_align": "left",
        "body_align": "left",
        "bullet": "-",
        "show_date_on_right": True,
        "date_format": "{start} - {end}",
        "spacing": 11,
        "border_radius": 0,
        "page_border": True,
        "contact_icons": False,
        "education_table": False,
        "references_two_column": False,
    },
    # IMPACT PANEL - bold two-column block header
    "impact_panel": {
        "name": "Impact Panel",
        "font_heading": "Helvetica-Bold",
        "font_body": "Helvetica",
        "font_size_title": 31,
        "font_size_heading": 11,
        "font_size_body": 9,
        "accent": "#6b7280",
        "background": "#ffffff",
        "section_border": False,
        "layout": "two_column",
        "left_column_ratio": 0.31,
        "heading_align": "left",
        "body_align": "left",
        "bullet": "-",
        "show_date_on_right": True,
        "date_format": "{start} - {end}",
        "spacing": 10,
        "border_radius": 0,
        "page_border": True,
        "contact_icons": False,
        "education_table": False,
        "references_two_column": False,
    },
    # CONTEMPORARY PHOTO - profile photo friendly modern layout
    "contemporary_photo": {
        "name": "Contemporary Photo",
        "font_heading": "Helvetica-Bold",
        "font_body": "Helvetica",
        "font_size_title": 29,
        "font_size_heading": 12,
        "font_size_body": 9,
        "accent": "#1d4ed8",
        "background": "#ffffff",
        "section_border": False,
        "layout": "single",
        "heading_align": "left",
        "body_align": "left",
        "bullet": "-",
        "show_date_on_right": True,
        "date_format": "{start} - {end}",
        "spacing": 11,
        "border_radius": 0,
        "page_border": True,
        "contact_icons": False,
        "education_table": False,
        "references_two_column": False,
    },
}

AppConfig.TEMPLATE_STYLE_GROUPS: Dict[str, tuple[str, ...]] = {
    "legacy": tuple(AppConfig.LEGACY_TEMPLATES.keys()),
    "signature": tuple(AppConfig.SIGNATURE_TEMPLATES.keys()),
}

# Runtime template registry used by PDF generator and API validation.
AppConfig.TEMPLATES = {
    **AppConfig.LEGACY_TEMPLATES,
    **AppConfig.SIGNATURE_TEMPLATES,
}


# Ensure backup directory exists
os.makedirs(AppConfig.BACKUP_DIR, exist_ok=True)

