import { useEffect, useMemo, useRef, useState } from 'react'
import './App.css'

const API_ROOTS = ['http://127.0.0.1:5000/api', '/api']
const CATALOG_ROOTS = ['/templates_catalog.json', 'http://127.0.0.1:5000/templates_catalog.json']
const STEP_LABELS = ['Templates', 'Details', 'AI', 'Review']

const TEMPLATE_CHOICES = [
  'modern', 'corporate', 'classic', 'compact', 'executive', 'snack_gray', 'vision_blue',
  'harsh_minimal', 'javid_split', 'teal_modern', 'astra_clean', 'metro_sidebar',
  'executive_slate', 'creative_split', 'mono_compact', 'classic_clarity', 'impact_panel',
  'contemporary_photo',
]

const FALLBACK_CATALOG = TEMPLATE_CHOICES.map((name) => ({
  id: `tpl-${name}`,
  name: name.replaceAll('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
  category: 'Built-in',
  mood: 'Balanced',
  tagline: 'ResumeForge template',
  settings: { template: name, pageSize: 'letter', font: 'Helvetica', accent: '#0f766e' },
}))

const TEMPLATE_THUMB_BY_NAME = {
  modern: '#0f766e',
  corporate: '#1e3a8a',
  classic: '#374151',
  compact: '#0f766e',
  executive: '#111827',
  snack_gray: '#ea580c',
  vision_blue: '#2563eb',
  harsh_minimal: '#1f2937',
  javid_split: '#6b7280',
  teal_modern: '#0d9488',
  astra_clean: '#0f766e',
  metro_sidebar: '#155e75',
  executive_slate: '#1f2937',
  creative_split: '#9333ea',
  mono_compact: '#111827',
  classic_clarity: '#2563eb',
  impact_panel: '#6b7280',
  contemporary_photo: '#1d4ed8',
}

const TEMPLATE_VISUALS = {
  modern: { tone: 'modern', badge: 'Modern' },
  corporate: { tone: 'corporate', badge: 'Corporate' },
  classic: { tone: 'classic', badge: 'Classic' },
  compact: { tone: 'compact', badge: 'Compact' },
  executive: { tone: 'executive', badge: 'Executive' },
  snack_gray: { tone: 'snack', badge: 'Creative' },
  vision_blue: { tone: 'vision', badge: 'Academic' },
  harsh_minimal: { tone: 'minimal', badge: 'Minimal' },
  javid_split: { tone: 'split', badge: 'Two-Column' },
  teal_modern: { tone: 'teal', badge: 'Fresh' },
  astra_clean: { tone: 'astra', badge: 'ATS Friendly' },
  metro_sidebar: { tone: 'metro', badge: 'Sidebar' },
  executive_slate: { tone: 'slate', badge: 'Executive' },
  creative_split: { tone: 'creative', badge: 'Creative' },
  mono_compact: { tone: 'mono', badge: 'Mono' },
  classic_clarity: { tone: 'clarity', badge: 'Classic' },
  impact_panel: { tone: 'impact', badge: 'Impact' },
  contemporary_photo: { tone: 'photo', badge: 'Photo' },
}

const FLASK_ASSET_BASES = ['http://127.0.0.1:5000', 'http://localhost:5000']

const TEMPLATE_THUMB_VARIANT = {
  modern: 'modern',
  corporate: 'corporate',
  classic: 'classic',
  compact: 'compact',
  executive: 'executive',
  snack_gray: 'creative',
  vision_blue: 'modern',
  harsh_minimal: 'minimal',
  javid_split: 'sidebar',
  teal_modern: 'modern',
  astra_clean: 'minimal',
  metro_sidebar: 'sidebar',
  executive_slate: 'executive',
  creative_split: 'creative',
  mono_compact: 'compact',
  classic_clarity: 'classic',
  impact_panel: 'impact',
  contemporary_photo: 'photo',
}

const makeThumbDataUri = (label, accent, variant = 'modern') => {
  const safe = String(label || 'Template').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
  const body = {
    modern: `
      <rect x="38" y="40" width="220" height="12" rx="6" fill="${accent}" fill-opacity="0.85"/>
      <rect x="38" y="60" width="160" height="8" rx="4" fill="#64748b" fill-opacity="0.75"/>
      <rect x="38" y="90" width="524" height="5" rx="2.5" fill="#cbd5e1"/>
      <rect x="38" y="110" width="250" height="8" rx="4" fill="#94a3b8"/>
      <rect x="38" y="126" width="180" height="8" rx="4" fill="#cbd5e1"/>
      <rect x="318" y="110" width="244" height="90" rx="8" fill="#ffffff" stroke="${accent}" stroke-opacity="0.25"/>
      <rect x="38" y="162" width="240" height="8" rx="4" fill="#94a3b8"/>
      <rect x="38" y="178" width="208" height="8" rx="4" fill="#cbd5e1"/>
      <rect x="38" y="204" width="524" height="5" rx="2.5" fill="#e2e8f0"/>
      <rect x="38" y="224" width="220" height="8" rx="4" fill="#94a3b8"/>
      <rect x="38" y="240" width="170" height="8" rx="4" fill="#cbd5e1"/>
    `,
    corporate: `
      <rect x="26" y="24" width="120" height="312" rx="10" fill="${accent}" fill-opacity="0.14" stroke="${accent}" stroke-opacity="0.3"/>
      <rect x="42" y="46" width="90" height="10" rx="5" fill="${accent}" fill-opacity="0.9"/>
      <rect x="42" y="68" width="74" height="7" rx="3.5" fill="#64748b"/>
      <rect x="164" y="40" width="398" height="14" rx="7" fill="${accent}" fill-opacity="0.8"/>
      <rect x="164" y="66" width="230" height="8" rx="4" fill="#64748b"/>
      <rect x="164" y="92" width="398" height="5" rx="2.5" fill="#cbd5e1"/>
      <rect x="164" y="112" width="220" height="8" rx="4" fill="#94a3b8"/>
      <rect x="164" y="128" width="180" height="8" rx="4" fill="#cbd5e1"/>
      <rect x="164" y="156" width="398" height="5" rx="2.5" fill="#e2e8f0"/>
      <rect x="164" y="176" width="250" height="8" rx="4" fill="#94a3b8"/>
      <rect x="164" y="192" width="200" height="8" rx="4" fill="#cbd5e1"/>
      <rect x="164" y="220" width="398" height="5" rx="2.5" fill="#e2e8f0"/>
      <rect x="164" y="240" width="240" height="8" rx="4" fill="#94a3b8"/>
    `,
    classic: `
      <rect x="38" y="44" width="524" height="2.5" rx="1.2" fill="${accent}" fill-opacity="0.6"/>
      <rect x="38" y="54" width="524" height="1.4" rx="0.7" fill="${accent}" fill-opacity="0.35"/>
      <rect x="188" y="70" width="224" height="13" rx="6.5" fill="#111827" fill-opacity="0.88"/>
      <rect x="232" y="92" width="136" height="8" rx="4" fill="#64748b"/>
      <rect x="38" y="122" width="524" height="5" rx="2.5" fill="#cbd5e1"/>
      <rect x="38" y="144" width="178" height="8" rx="4" fill="#94a3b8"/>
      <rect x="38" y="160" width="130" height="8" rx="4" fill="#cbd5e1"/>
      <rect x="38" y="188" width="524" height="5" rx="2.5" fill="#e2e8f0"/>
      <rect x="38" y="210" width="210" height="8" rx="4" fill="#94a3b8"/>
      <rect x="38" y="226" width="170" height="8" rx="4" fill="#cbd5e1"/>
      <rect x="38" y="254" width="524" height="5" rx="2.5" fill="#e2e8f0"/>
    `,
    compact: `
      <rect x="38" y="38" width="240" height="11" rx="5.5" fill="${accent}" fill-opacity="0.88"/>
      <rect x="38" y="56" width="170" height="7" rx="3.5" fill="#64748b"/>
      <rect x="38" y="76" width="524" height="4" rx="2" fill="#cbd5e1"/>
      <rect x="38" y="92" width="524" height="4" rx="2" fill="#dbe4ee"/>
      <rect x="38" y="108" width="524" height="4" rx="2" fill="#cbd5e1"/>
      <rect x="38" y="124" width="524" height="4" rx="2" fill="#dbe4ee"/>
      <rect x="38" y="140" width="524" height="4" rx="2" fill="#cbd5e1"/>
      <rect x="38" y="156" width="524" height="4" rx="2" fill="#dbe4ee"/>
      <rect x="38" y="172" width="524" height="4" rx="2" fill="#cbd5e1"/>
      <rect x="38" y="188" width="524" height="4" rx="2" fill="#dbe4ee"/>
      <rect x="38" y="204" width="524" height="4" rx="2" fill="#cbd5e1"/>
      <rect x="38" y="220" width="524" height="4" rx="2" fill="#dbe4ee"/>
      <rect x="38" y="236" width="524" height="4" rx="2" fill="#cbd5e1"/>
      <rect x="38" y="252" width="524" height="4" rx="2" fill="#dbe4ee"/>
    `,
    executive: `
      <rect x="24" y="24" width="552" height="36" rx="10" fill="${accent}" fill-opacity="0.82"/>
      <rect x="200" y="36" width="200" height="12" rx="6" fill="#ffffff" fill-opacity="0.95"/>
      <rect x="38" y="82" width="320" height="10" rx="5" fill="#111827" fill-opacity="0.9"/>
      <rect x="38" y="102" width="220" height="7" rx="3.5" fill="#64748b"/>
      <rect x="380" y="82" width="182" height="112" rx="8" fill="#ffffff" stroke="${accent}" stroke-opacity="0.35"/>
      <rect x="38" y="126" width="524" height="5" rx="2.5" fill="#cbd5e1"/>
      <rect x="38" y="146" width="260" height="8" rx="4" fill="#94a3b8"/>
      <rect x="38" y="162" width="220" height="8" rx="4" fill="#cbd5e1"/>
      <rect x="38" y="190" width="524" height="5" rx="2.5" fill="#e2e8f0"/>
      <rect x="38" y="210" width="250" height="8" rx="4" fill="#94a3b8"/>
      <rect x="38" y="226" width="190" height="8" rx="4" fill="#cbd5e1"/>
    `,
    minimal: `
      <rect x="180" y="48" width="240" height="12" rx="6" fill="#111827" fill-opacity="0.88"/>
      <rect x="220" y="72" width="160" height="7" rx="3.5" fill="#64748b"/>
      <rect x="38" y="102" width="524" height="2" rx="1" fill="#94a3b8"/>
      <rect x="80" y="124" width="440" height="6" rx="3" fill="#cbd5e1"/>
      <rect x="110" y="140" width="380" height="6" rx="3" fill="#dbe4ee"/>
      <rect x="80" y="172" width="440" height="6" rx="3" fill="#cbd5e1"/>
      <rect x="110" y="188" width="380" height="6" rx="3" fill="#dbe4ee"/>
      <rect x="80" y="220" width="440" height="6" rx="3" fill="#cbd5e1"/>
      <rect x="110" y="236" width="380" height="6" rx="3" fill="#dbe4ee"/>
    `,
    sidebar: `
      <rect x="24" y="24" width="170" height="312" rx="10" fill="${accent}" fill-opacity="0.14" stroke="${accent}" stroke-opacity="0.35"/>
      <circle cx="109" cy="62" r="24" fill="#ffffff" stroke="${accent}" stroke-opacity="0.6"/>
      <rect x="52" y="96" width="114" height="9" rx="4.5" fill="${accent}" fill-opacity="0.9"/>
      <rect x="52" y="114" width="84" height="7" rx="3.5" fill="#64748b"/>
      <rect x="52" y="148" width="120" height="4" rx="2" fill="#94a3b8"/>
      <rect x="52" y="160" width="105" height="4" rx="2" fill="#94a3b8"/>
      <rect x="52" y="172" width="95" height="4" rx="2" fill="#94a3b8"/>
      <rect x="212" y="42" width="348" height="12" rx="6" fill="#111827" fill-opacity="0.88"/>
      <rect x="212" y="64" width="220" height="8" rx="4" fill="#64748b"/>
      <rect x="212" y="92" width="348" height="5" rx="2.5" fill="#cbd5e1"/>
      <rect x="212" y="114" width="250" height="8" rx="4" fill="#94a3b8"/>
      <rect x="212" y="130" width="220" height="8" rx="4" fill="#cbd5e1"/>
      <rect x="212" y="158" width="348" height="5" rx="2.5" fill="#e2e8f0"/>
      <rect x="212" y="180" width="240" height="8" rx="4" fill="#94a3b8"/>
      <rect x="212" y="196" width="200" height="8" rx="4" fill="#cbd5e1"/>
      <rect x="212" y="224" width="348" height="5" rx="2.5" fill="#e2e8f0"/>
    `,
    creative: `
      <rect x="24" y="24" width="180" height="26" rx="8" fill="${accent}" fill-opacity="0.78"/>
      <rect x="396" y="24" width="180" height="26" rx="8" fill="${accent}" fill-opacity="0.4"/>
      <rect x="38" y="66" width="230" height="12" rx="6" fill="#111827" fill-opacity="0.88"/>
      <rect x="38" y="86" width="170" height="8" rx="4" fill="#64748b"/>
      <rect x="38" y="112" width="524" height="5" rx="2.5" fill="#cbd5e1"/>
      <rect x="38" y="132" width="220" height="8" rx="4" fill="#94a3b8"/>
      <rect x="318" y="132" width="244" height="62" rx="8" fill="#ffffff" stroke="${accent}" stroke-opacity="0.35"/>
      <rect x="38" y="152" width="180" height="8" rx="4" fill="#cbd5e1"/>
      <rect x="38" y="180" width="524" height="5" rx="2.5" fill="#e2e8f0"/>
      <rect x="38" y="200" width="250" height="8" rx="4" fill="#94a3b8"/>
      <rect x="38" y="216" width="190" height="8" rx="4" fill="#cbd5e1"/>
      <rect x="24" y="312" width="120" height="24" rx="8" fill="${accent}" fill-opacity="0.65"/>
      <rect x="456" y="312" width="120" height="24" rx="8" fill="${accent}" fill-opacity="0.45"/>
    `,
    impact: `
      <rect x="0" y="0" width="600" height="52" fill="${accent}" fill-opacity="0.12"/>
      <rect x="0" y="52" width="66" height="308" fill="${accent}" fill-opacity="0.26"/>
      <rect x="86" y="22" width="224" height="12" rx="6" fill="#111827" fill-opacity="0.88"/>
      <rect x="86" y="42" width="160" height="8" rx="4" fill="#64748b"/>
      <rect x="86" y="72" width="490" height="5" rx="2.5" fill="#cbd5e1"/>
      <rect x="86" y="94" width="230" height="8" rx="4" fill="#94a3b8"/>
      <rect x="86" y="110" width="190" height="8" rx="4" fill="#cbd5e1"/>
      <rect x="86" y="138" width="490" height="5" rx="2.5" fill="#e2e8f0"/>
      <rect x="86" y="160" width="260" height="8" rx="4" fill="#94a3b8"/>
      <rect x="86" y="176" width="210" height="8" rx="4" fill="#cbd5e1"/>
      <rect x="86" y="204" width="490" height="5" rx="2.5" fill="#e2e8f0"/>
      <rect x="86" y="226" width="210" height="8" rx="4" fill="#94a3b8"/>
    `,
    photo: `
      <rect x="38" y="34" width="524" height="12" rx="6" fill="${accent}" fill-opacity="0.58"/>
      <circle cx="96" cy="86" r="36" fill="#ffffff" stroke="${accent}" stroke-opacity="0.8" stroke-width="3"/>
      <rect x="148" y="72" width="220" height="12" rx="6" fill="#111827" fill-opacity="0.88"/>
      <rect x="148" y="92" width="170" height="8" rx="4" fill="#64748b"/>
      <rect x="38" y="132" width="524" height="5" rx="2.5" fill="#cbd5e1"/>
      <rect x="38" y="154" width="240" height="8" rx="4" fill="#94a3b8"/>
      <rect x="38" y="170" width="200" height="8" rx="4" fill="#cbd5e1"/>
      <rect x="38" y="198" width="524" height="5" rx="2.5" fill="#e2e8f0"/>
      <rect x="38" y="220" width="250" height="8" rx="4" fill="#94a3b8"/>
      <rect x="38" y="236" width="210" height="8" rx="4" fill="#cbd5e1"/>
      <rect x="398" y="154" width="164" height="96" rx="8" fill="#ffffff" stroke="${accent}" stroke-opacity="0.35"/>
    `,
  }[variant] || ''

  const svg = `
<svg xmlns="http://www.w3.org/2000/svg" width="600" height="360" viewBox="0 0 600 360">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="${accent}" stop-opacity="0.20"/>
      <stop offset="100%" stop-color="#ffffff"/>
    </linearGradient>
  </defs>
  <rect x="0" y="0" width="600" height="360" fill="#f8fafc"/>
  <rect x="16" y="16" width="568" height="328" rx="12" fill="url(#g)" stroke="${accent}" stroke-opacity="0.35"/>
  ${body}
  <rect x="38" y="274" width="160" height="42" rx="9" fill="${accent}" fill-opacity="0.88"/>
  <text x="300" y="328" text-anchor="middle" font-family="Segoe UI, Arial" font-size="16" fill="#334155">${safe}</text>
</svg>`.trim()
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`
}

const EMBEDDED_TEMPLATE_THUMBS = Object.fromEntries(
  TEMPLATE_CHOICES.map((key) => [
    key,
    makeThumbDataUri(
      key,
      TEMPLATE_THUMB_BY_NAME[key] || '#0f766e',
      TEMPLATE_THUMB_VARIANT[key] || 'modern',
    ),
  ]),
)

const EMPTY_FORM = {
  full_name: '',
  profile_title: '',
  email: '',
  phone: '',
  city: '',
  address: '',
  summary: '',
  linkedin: '',
  github: '',
  website: '',
  profile_pic: '',
  experiences: '',
  educations: '',
  projects: '',
  skills: '',
}

const EMPTY_USER_PROFILE = {
  display_name: '',
  email: '',
  phone: '',
  city: '',
  address: '',
  headline: '',
  linkedin: '',
  github: '',
  website: '',
  bio: '',
  profile_pic: '',
}

const DEFAULT_CFG = {
  template_name: 'modern',
  page_size: 'letter',
  accent_color_override: '#0f766e',
  font_override: 'Helvetica',
  compact_mode: false,
  ats_safe_mode: false,
  font_scale: 1,
  margin_preset: 'normal',
  header_layout: 'default',
  layout_override: '',
  heading_align_override: '',
  body_align_override: '',
}

const splitLines = (v) =>
  String(v || '')
    .split('\n')
    .map((s) => s.trim())
    .filter(Boolean)

const parsePipe = (line, n) => {
  const parts = (String(line || '').includes('|') ? String(line).split('|') : String(line).split(',')).map((v) => v.trim())
  while (parts.length < n) parts.push('')
  return parts
}

const expRowsToText = (rows) =>
  (rows || [])
    .map((x) => [x.job_title, x.company, x.start_date, x.end_date, x.description].map((v) => (v || '').trim()).join(' | '))
    .join('\n')

const eduRowsToText = (rows) =>
  (rows || [])
    .map((x) => [x.degree, x.institution, x.start_date, x.end_date, x.description].map((v) => (v || '').trim()).join(' | '))
    .join('\n')

const projRowsToText = (rows) =>
  (rows || [])
    .map((x) => [x.name, x.role, x.technologies, x.start_date, x.end_date, x.description, x.link].map((v) => (v || '').trim()).join(' | '))
    .join('\n')

export default function App() {
  const fileRef = useRef(null)
  const templateSectionRef = useRef(null)
  const templateSearchRef = useRef(null)
  const [health, setHealth] = useState({ status: 'checking', version: '-' })
  const [message, setMessage] = useState('')
  const [assist, setAssist] = useState('')
  const [loading, setLoading] = useState(false)
  const [step, setStep] = useState(0)
  const [templates, setTemplates] = useState([])
  const [templateQuery, setTemplateQuery] = useState('')
  const [jobDesc, setJobDesc] = useState('')
  const [aiPrompt, setAiPrompt] = useState('Tailor resume for this role and improve bullets')
  const [aiPatch, setAiPatch] = useState(null)
  const [resumes, setResumes] = useState([])
  const [selectedResumeId, setSelectedResumeId] = useState('')
  const [pdfPreviewUrl, setPdfPreviewUrl] = useState('')
  const [previewTemplate, setPreviewTemplate] = useState(null)
  const [uploadingPhoto, setUploadingPhoto] = useState(false)
  const [userProfile, setUserProfile] = useState(EMPTY_USER_PROFILE)
  const [showUserCard, setShowUserCard] = useState(false)
  const [theme, setTheme] = useState(() => {
    try {
      const saved = localStorage.getItem('rf_theme')
      if (saved === 'light' || saved === 'dark') return saved
    } catch {
      // no-op
    }
    return 'light'
  })

  const [form, setForm] = useState(EMPTY_FORM)
  const [cfg, setCfgState] = useState(DEFAULT_CFG)

  const skills = useMemo(() => splitLines(form.skills), [form.skills])
  const contact = [form.email, form.phone, form.city, form.address].filter(Boolean).join(' | ')

  const filteredTemplates = useMemo(() => {
    const q = templateQuery.trim().toLowerCase()
    if (!q) return templates
    return templates.filter((t) => `${t.name || ''} ${t.category || ''} ${t.mood || ''} ${t.tagline || ''}`.toLowerCase().includes(q))
  }, [templates, templateQuery])

  const selectedTemplateVisual = useMemo(() => {
    const current = templates.find((t) => String(t?.settings?.template || '').toLowerCase() === String(cfg.template_name || '').toLowerCase())
      || FALLBACK_CATALOG.find((t) => String(t?.settings?.template || '').toLowerCase() === String(cfg.template_name || '').toLowerCase())
      || { settings: { template: cfg.template_name, accent: cfg.accent_color_override }, palette: [cfg.accent_color_override || '#0f766e', '#ecfeff', '#ffffff'] }
    return templateVisual(current)
  }, [templates, cfg.template_name, cfg.accent_color_override])
  const userInitial = useMemo(() => {
    const base = (userProfile.display_name || form.full_name || 'U').trim()
    if (!base) return 'U'
    const parts = base.split(/\s+/).filter(Boolean)
    if (parts.length === 1) return parts[0][0].toUpperCase()
    return `${parts[0][0] || ''}${parts[1][0] || ''}`.toUpperCase()
  }, [userProfile.display_name, form.full_name])

  const setField = (k, v) => setForm((p) => ({ ...p, [k]: v }))
  const setCfgField = (k, v) => setCfgState((p) => ({ ...p, [k]: v }))
  const setUserProfileField = (k, v) => setUserProfile((p) => ({ ...p, [k]: v }))

  function profilePicSrc() {
    if (!form.profile_pic) return ''
    if (String(form.profile_pic).startsWith('data:image')) return form.profile_pic
    return `data:image/png;base64,${form.profile_pic}`
  }

  function templateThumb(item) {
    const toAbsoluteAsset = (rawPath) => {
      const p = String(rawPath || '').trim()
      if (!p) return ''
      if (p.startsWith('http://') || p.startsWith('https://') || p.startsWith('data:')) return p
      if (!p.startsWith('/')) return p
      if (typeof window !== 'undefined' && (window.location.port === '5173' || window.location.port === '5174')) {
        return `${FLASK_ASSET_BASES[0]}${p}`
      }
      return p
    }

    if (item?.thumbnail) return toAbsoluteAsset(item.thumbnail)
    const key = String(item?.settings?.template || item?.id || '').toLowerCase()
    if (EMBEDDED_TEMPLATE_THUMBS[key]) return EMBEDDED_TEMPLATE_THUMBS[key]
    return EMBEDDED_TEMPLATE_THUMBS.modern
  }

  function templateVisual(item) {
    const key = String(item?.settings?.template || item?.id || 'modern').toLowerCase()
    const profile = TEMPLATE_VISUALS[key] || { tone: 'modern', badge: 'Template' }
    const palette = Array.isArray(item?.palette) && item.palette.length >= 2 ? item.palette : ['#0f766e', '#ecfeff', '#ffffff']
    const accent = String(item?.settings?.accent || palette[0] || '#0f766e')
    return {
      ...profile,
      vars: {
        '--tpl-accent': accent,
        '--tpl-bg1': palette[0] || '#0f766e',
        '--tpl-bg2': palette[1] || '#ecfeff',
        '--tpl-bg3': palette[2] || '#ffffff',
      },
    }
  }

  async function smartFetch(urls, options = {}) {
    let lastError = null
    let lastResponse = null
    for (const u of urls) {
      try {
        const r = await fetch(u, options)
        if (r.ok) return r
        lastResponse = r
      } catch (e) {
        lastError = e
      }
    }
    if (lastError) throw lastError
    if (lastResponse) return lastResponse
    throw new Error('Network unavailable')
  }

  async function apiFetch(path, options = {}) {
    const urls = API_ROOTS.map((r) => `${r}${path}`)
    return smartFetch(urls, options)
  }

  async function fetchHealth() {
    try {
      const [h, v] = await Promise.all([
        apiFetch('/health').then((r) => r.json()),
        apiFetch('/version').then((r) => r.json()),
      ])
      setHealth({ status: h?.status || 'unknown', version: v?.version || '-' })
    } catch {
      setHealth({ status: 'offline', version: '-' })
    }
  }

  async function fetchResumes() {
    try {
      const r = await apiFetch('/resumes')
      if (!r.ok) throw new Error(await r.text())
      const d = await r.json()
      setResumes(Array.isArray(d) ? d : [])
    } catch {
      setResumes([])
    }
  }

  async function fetchUserProfile() {
    try {
      const r = await apiFetch('/user-profile')
      if (!r.ok) throw new Error(await r.text())
      const d = await r.json()
      setUserProfile({
        display_name: d.display_name || '',
        email: d.email || '',
        phone: d.phone || '',
        city: d.city || '',
        address: d.address || '',
        headline: d.headline || '',
        linkedin: d.linkedin || '',
        github: d.github || '',
        website: d.website || '',
        bio: d.bio || '',
        profile_pic: d.profile_pic || '',
      })
    } catch {
      setUserProfile(EMPTY_USER_PROFILE)
    }
  }

  async function loadResumeById(id) {
    if (!id) return
    try {
      const r = await apiFetch(`/resumes/${id}`)
      if (!r.ok) throw new Error(await r.text())
      const d = await r.json()
      setForm({
        full_name: d.full_name || '',
        profile_title: d.profile_title || '',
        email: d.email || '',
        phone: d.phone || '',
        city: d.city || '',
        address: d.address || '',
        summary: d.summary || '',
        linkedin: d.linkedin || '',
        github: d.github || '',
        website: d.website || '',
        profile_pic: d.profile_pic || '',
        experiences: expRowsToText(d.experiences),
        educations: eduRowsToText(d.educations),
        projects: projRowsToText(d.projects),
        skills: (d.skills || []).join('\n'),
      })
      setCfgState((p) => ({
        ...p,
        template_name: d.template_name || p.template_name,
        page_size: d.page_size || p.page_size,
        accent_color_override: d.accent_color_override || p.accent_color_override,
        font_override: d.font_override || p.font_override,
        compact_mode: !!d.compact_mode,
        ats_safe_mode: !!d.ats_safe_mode,
        font_scale: Number(d.font_scale || p.font_scale),
        margin_preset: d.margin_preset || p.margin_preset,
        header_layout: d.header_layout || p.header_layout,
        layout_override: d.layout_override || p.layout_override,
        heading_align_override: d.heading_align_override || p.heading_align_override,
        body_align_override: d.body_align_override || p.body_align_override,
      }))
      setMessage('Resume loaded.')
    } catch (e) {
      setMessage(`Load failed: ${e.message || 'unknown error'}`)
    }
  }

  async function fetchTemplates() {
    try {
      const r = await smartFetch(CATALOG_ROOTS)
      if (!r.ok) throw new Error('Template catalog load failed')
      const d = await r.json()
      const arr = Array.isArray(d) && d.length ? d : FALLBACK_CATALOG
      setTemplates(arr)
    } catch {
      setTemplates(FALLBACK_CATALOG)
    }
  }

  function payload() {
    return {
      id: selectedResumeId ? Number(selectedResumeId) : undefined,
      title: form.full_name || 'Untitled',
      full_name: form.full_name,
      profile_title: form.profile_title,
      email: form.email,
      phone: form.phone,
      city: form.city,
      address: form.address,
      summary: form.summary,
      linkedin: form.linkedin,
      github: form.github,
      website: form.website,
      profile_pic: form.profile_pic || undefined,
      experiences: splitLines(form.experiences).map((l) => {
        const [job_title, company, start_date, end_date, description] = parsePipe(l, 5)
        return { job_title, company, start_date, end_date, description }
      }),
      educations: splitLines(form.educations).map((l) => {
        const [degree, institution, start_date, end_date, description] = parsePipe(l, 5)
        return { degree, institution, start_date, end_date, description }
      }),
      projects: splitLines(form.projects).map((l) => {
        const [name, role, technologies, start_date, end_date, description, link] = parsePipe(l, 7)
        return { name, role, technologies, start_date, end_date, description, link }
      }),
      skills,
      certifications: [],
      languages: [],
      achievements: [],
      references: [],
      custom_sections: [],
      ...cfg,
    }
  }

  async function runApi(path, body, onOk) {
    try {
      const r = await apiFetch(path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!r.ok) throw new Error(await r.text())
      const d = await r.json()
      onOk(d)
    } catch (e) {
      setAssist(e.message || 'Action failed')
    }
  }

  async function saveResume() {
    try {
      setLoading(true)
      const r = await apiFetch('/resumes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload()),
      })
      if (!r.ok) throw new Error(await r.text())
      const d = await r.json()
      setMessage(d?.message || 'Saved successfully.')
      if (d?.id) setSelectedResumeId(String(d.id))
      await fetchResumes()
    } catch (e) {
      setMessage(e.message || 'Save failed')
    } finally {
      setLoading(false)
    }
  }

  async function saveUserProfile() {
    try {
      const r = await apiFetch('/user-profile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userProfile),
      })
      if (!r.ok) throw new Error(await r.text())
      const d = await r.json()
      setMessage(d?.message || 'User profile saved.')
    } catch (e) {
      setMessage(e.message || 'User profile save failed')
    }
  }

  async function deleteResume() {
    if (!selectedResumeId) {
      setMessage('Select a saved resume to delete.')
      return
    }
    try {
      setLoading(true)
      const r = await apiFetch(`/resumes/${selectedResumeId}`, { method: 'DELETE' })
      if (!r.ok) throw new Error(await r.text())
      setSelectedResumeId('')
      setMessage('Resume deleted.')
      await fetchResumes()
    } catch (e) {
      setMessage(e.message || 'Delete failed')
    } finally {
      setLoading(false)
    }
  }

  async function exportPdf() {
    const r = await apiFetch('/export-pdf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/pdf' },
      body: JSON.stringify(payload()),
    })
    if (!r.ok) throw new Error(await r.text())
    const blob = await r.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${form.full_name || 'resume'}_resume.pdf`
    a.click()
    URL.revokeObjectURL(url)
  }

  async function exportWord() {
    const r = await apiFetch('/export-word', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/rtf' },
      body: JSON.stringify(payload()),
    })
    if (!r.ok) throw new Error(await r.text())
    const blob = await r.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${form.full_name || 'resume'}_resume.rtf`
    a.click()
    URL.revokeObjectURL(url)
  }

  async function previewPdf() {
    try {
      setLoading(true)
      const r = await apiFetch('/preview-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/pdf' },
        body: JSON.stringify(payload()),
      })
      if (!r.ok) throw new Error(await r.text())
      const blob = await r.blob()
      if (pdfPreviewUrl) URL.revokeObjectURL(pdfPreviewUrl)
      const url = URL.createObjectURL(blob)
      setPdfPreviewUrl(url)
      setStep(3)
      setMessage('Live PDF preview ready.')
    } catch (e) {
      setMessage(e.message || 'PDF preview failed')
    } finally {
      setLoading(false)
    }
  }

  async function generateResume() {
    try {
      setLoading(true)
      await saveResume()
      await exportPdf()
      setMessage('Resume generated successfully.')
    } catch (e) {
      setMessage(e.message || 'Generate failed')
    } finally {
      setLoading(false)
    }
  }

  async function uploadProfilePhoto(file) {
    try {
      setUploadingPhoto(true)
      const reader = new FileReader()
      const dataUrl = await new Promise((resolve, reject) => {
        reader.onload = () => resolve(String(reader.result || ''))
        reader.onerror = () => reject(new Error('Image read failed'))
        reader.readAsDataURL(file)
      })
      const r = await apiFetch('/upload-profile-pic', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: dataUrl }),
      })
      if (!r.ok) throw new Error(await r.text())
      const d = await r.json()
      if (!d?.image) throw new Error('Invalid upload response')
      setField('profile_pic', d.image)
      setMessage('Profile photo uploaded.')
    } catch (e) {
      setMessage(e.message || 'Photo upload failed')
    } finally {
      setUploadingPhoto(false)
    }
  }

  function applyTemplate(t) {
    const settings = t?.settings || {}
    setCfgState((p) => ({
      ...p,
      template_name: settings.template || p.template_name,
      accent_color_override: settings.accent || p.accent_color_override,
      font_override: settings.font || p.font_override,
      page_size: settings.pageSize ? String(settings.pageSize).toLowerCase() : p.page_size,
      compact_mode: !!settings.compactMode,
      ats_safe_mode: !!settings.atsSafeMode,
      layout_override: settings.pageLayout || p.layout_override,
      header_layout: settings.headerLayout || p.header_layout,
      heading_align_override: settings.headingAlign || '',
      body_align_override: settings.bodyAlign || '',
    }))
    setMessage(`Template selected: ${t?.name || '-'}`)
  }

  function autoOnePageFit() {
    const expCount = splitLines(form.experiences).length
    const eduCount = splitLines(form.educations).length
    const projCount = splitLines(form.projects).length
    const skillCount = skills.length
    const summaryLen = (form.summary || '').trim().length
    const totalSignal = (expCount * 18) + (eduCount * 10) + (projCount * 14) + (skillCount * 3) + Math.floor(summaryLen / 26)

    let fontScale = 1
    let compact = false
    let margins = 'normal'

    if (totalSignal > 190) {
      fontScale = 0.86
      compact = true
      margins = 'compact'
    } else if (totalSignal > 145) {
      fontScale = 0.92
      compact = true
      margins = 'compact'
    } else if (totalSignal > 110) {
      fontScale = 0.96
      compact = false
      margins = 'normal'
    } else {
      fontScale = 1
      compact = false
      margins = 'normal'
    }

    setCfgState((p) => ({
      ...p,
      font_scale: fontScale,
      compact_mode: compact,
      margin_preset: margins,
    }))
    setMessage(`Auto 1-Page Fit applied: ${Math.round(fontScale * 100)}% font, ${compact ? 'compact' : 'normal'} mode.`)
  }

  function setFontScalePercent(percent) {
    const raw = Number(percent)
    if (Number.isNaN(raw)) return
    const clamped = Math.min(120, Math.max(80, raw))
    setCfgField('font_scale', clamped / 100)
  }

  function setSpacingMode(mode) {
    const m = String(mode || 'normal')
    if (m === 'tight') {
      setCfgState((p) => ({
        ...p,
        compact_mode: true,
        margin_preset: 'compact',
      }))
      return
    }
    if (m === 'wide') {
      setCfgState((p) => ({
        ...p,
        compact_mode: false,
        margin_preset: 'wide',
      }))
      return
    }
    setCfgState((p) => ({
      ...p,
      compact_mode: false,
      margin_preset: 'normal',
    }))
  }

  const spacingMode = (cfg.compact_mode || cfg.margin_preset === 'compact')
    ? 'tight'
    : (cfg.margin_preset === 'wide' ? 'wide' : 'normal')

  function toggleTheme() {
    setTheme((p) => (p === 'dark' ? 'light' : 'dark'))
  }

  function goToTemplates() {
    setStep(0)
    setTimeout(() => {
      if (templateSectionRef.current && typeof templateSectionRef.current.scrollIntoView === 'function') {
        templateSectionRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
      if (templateSearchRef.current && typeof templateSearchRef.current.focus === 'function') {
        templateSearchRef.current.focus()
      }
    }, 50)
  }

  function applyAiPatch() {
    if (!aiPatch) {
      setAssist('No AI changes available to apply.')
      return
    }
    if (typeof aiPatch.summary === 'string' && aiPatch.summary.trim()) setField('summary', aiPatch.summary)
    if (Array.isArray(aiPatch.skills) && aiPatch.skills.length) setField('skills', aiPatch.skills.join('\n'))
    if (Array.isArray(aiPatch.experiences) && aiPatch.experiences.length) setField('experiences', expRowsToText(aiPatch.experiences))
    if (Array.isArray(aiPatch.projects) && aiPatch.projects.length) setField('projects', projRowsToText(aiPatch.projects))
    setAssist('AI changes applied to form.')
    setAiPatch(null)
  }

  function exportJson() {
    const blob = new Blob([JSON.stringify({ form, cfg }, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${form.full_name || 'resume'}_data.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  function applyImportedFields(fields = {}) {
    setForm((p) => ({
      ...p,
      full_name: fields.fullName || p.full_name,
      profile_title: fields.profileTitle || p.profile_title,
      email: fields.email || p.email,
      phone: fields.phone || p.phone,
      city: fields.city || p.city,
      address: fields.address || p.address,
      summary: fields.summary || p.summary,
      profile_pic: fields.profilePic || p.profile_pic,
      experiences: fields.experiences || p.experiences,
      educations: fields.educations || p.educations,
      projects: fields.projects || p.projects,
      skills: fields.skills || p.skills,
    }))
  }

  function applyUserProfileToResume() {
    setForm((p) => ({
      ...p,
      full_name: userProfile.display_name || p.full_name,
      profile_title: userProfile.headline || p.profile_title,
      email: userProfile.email || p.email,
      phone: userProfile.phone || p.phone,
      city: userProfile.city || p.city,
      address: userProfile.address || p.address,
      linkedin: userProfile.linkedin || p.linkedin,
      github: userProfile.github || p.github,
      website: userProfile.website || p.website,
      summary: userProfile.bio || p.summary,
      profile_pic: userProfile.profile_pic || p.profile_pic,
    }))
    setMessage('User profile applied to resume form.')
  }

  async function importResumeFile(file) {
    const ext = (file.name || '').toLowerCase()
    if (ext.endsWith('.json')) {
      importJson(file)
      return
    }
    try {
      const fd = new FormData()
      fd.append('file', file)
      const r = await apiFetch('/import-resume-file', {
        method: 'POST',
        body: fd,
      })
      if (!r.ok) throw new Error(await r.text())
      const d = await r.json()
      applyImportedFields(d.fields || {})
      setMessage(d.message || 'Resume imported.')
    } catch (e) {
      setMessage(e.message || 'File import failed')
    }
  }

  function importJson(file) {
    const reader = new FileReader()
    reader.onload = () => {
      try {
        const parsed = JSON.parse(String(reader.result || '{}'))
        if (parsed?.form) setForm((p) => ({ ...p, ...parsed.form }))
        if (parsed?.cfg) setCfgState((p) => ({ ...p, ...parsed.cfg }))
        setMessage('Import completed.')
      } catch {
        setMessage('Invalid JSON file.')
      }
    }
    reader.readAsText(file)
  }

  useEffect(() => {
    fetchHealth()
    fetchTemplates()
    fetchResumes()
    fetchUserProfile()
  }, [])

  useEffect(() => {
    try {
      localStorage.setItem('rf_theme', theme)
    } catch {
      // no-op
    }
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  useEffect(() => () => {
    if (pdfPreviewUrl) URL.revokeObjectURL(pdfPreviewUrl)
  }, [pdfPreviewUrl])

  return (
    <div className={`app-shell theme-${theme}`}>
      <header className="topbar card">
        <div>
          <h1>ResumeForge React</h1>
          <p>Professional Resume Builder</p>
        </div>
        <div className="top-actions">
          <select value={selectedResumeId} onChange={(e) => { setSelectedResumeId(e.target.value); if (e.target.value) loadResumeById(e.target.value) }}>
            <option value="">-- Select Resume --</option>
            {resumes.map((r) => <option key={r.id} value={r.id}>{r.title || `Resume ${r.id}`}</option>)}
          </select>
          <button type="button" onClick={saveResume} className="primary" disabled={loading}>Save</button>
          <button type="button" onClick={deleteResume} disabled={loading}>Delete</button>
          <button type="button" onClick={previewPdf}>Preview PDF</button>
          <button type="button" onClick={() => exportPdf().catch((e) => setMessage(e.message || 'PDF failed'))}>PDF</button>
          <button type="button" onClick={() => exportWord().catch((e) => setMessage(e.message || 'Word failed'))}>Word</button>
          <button type="button" onClick={exportJson}>Export</button>
          <button type="button" onClick={() => fileRef.current?.click()}>Import</button>
          <button type="button" onClick={toggleTheme}>{theme === 'dark' ? 'Light Theme' : 'Dark Theme'}</button>
          <input ref={fileRef} type="file" className="hidden-file" onChange={(e) => { const f = e.target.files?.[0]; if (f) importResumeFile(f); e.target.value = '' }} />
          <span className={`pill ${health.status === 'ok' ? 'ok' : 'warn'}`}>API: {health.status}</span>
          <span className="pill">Version: {health.version}</span>
          <button type="button" className="user-chip" onClick={() => setShowUserCard((p) => !p)}>
            <span className="user-avatar">{userInitial}</span>
            <span className="user-chip-name">{userProfile.display_name || form.full_name || 'User'}</span>
          </button>
        </div>
      </header>

      <div className="wizard-tabs card">
        {STEP_LABELS.map((label, i) => (
          <button type="button" key={label} className={`tab-btn ${step === i ? 'active' : ''}`} onClick={() => setStep(i)}>
            {i + 1}. {label}
          </button>
        ))}
      </div>

      <main className="content-grid">
        <section className="card main-card">
          {step === 0 ? (
            <>
              <div ref={templateSectionRef} />
              <h2>Choose Template</h2>
              <div className="row">
                <input ref={templateSearchRef} placeholder="Search template style or mood" value={templateQuery} onChange={(e) => setTemplateQuery(e.target.value)} />
                <button type="button" onClick={fetchTemplates}>Refresh Templates</button>
              </div>
              <div className="template-grid">
                {filteredTemplates.length ? (
                  filteredTemplates.map((t) => {
                    const active = (t.settings?.template || '').toLowerCase() === String(cfg.template_name || '').toLowerCase()
                    const visual = templateVisual(t)
                    return (
                      <button
                        type="button"
                        key={t.id}
                        className={`template-card tone-${visual.tone} ${active ? 'active' : ''}`}
                        style={visual.vars}
                        onClick={() => setPreviewTemplate(t)}
                      >
                        <img
                          src={templateThumb(t)}
                          alt={t.name || 'template'}
                          className="template-thumb"
                          loading="lazy"
                          onError={(e) => {
                            e.currentTarget.onerror = null
                            e.currentTarget.src = templateThumb({ settings: { template: 'modern' } })
                          }}
                        />
                        <div className="template-head">
                          <strong>{t.name}</strong>
                          {active ? <span className="template-live-tag">Active</span> : null}
                        </div>
                        <span className="template-badge">{visual.badge}</span>
                        <span>{t.category || 'General'} | {t.mood || 'Balanced'}</span>
                        <small>{t.tagline || 'Styled template preset'}</small>
                        <div className="template-actions">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation()
                              applyTemplate(t)
                            }}
                          >
                            Use Template
                          </button>
                          <button
                            type="button"
                            className="ghost"
                            onClick={(e) => {
                              e.stopPropagation()
                              setPreviewTemplate(t)
                            }}
                          >
                            Preview
                          </button>
                        </div>
                      </button>
                    )
                  })
                ) : (
                  <p className="muted">No templates found.</p>
                )}
              </div>
            </>
          ) : null}

          {step === 1 ? (
            <>
              <h2>Resume Details</h2>
              <div className="profile-box">
                <h3>User Profile</h3>
                <p className="muted">Save your default details once and reuse for every new resume.</p>
                <div className="form-grid">
                  <label>Name</label><input value={userProfile.display_name} onChange={(e) => setUserProfileField('display_name', e.target.value)} />
                  <label>Headline</label><input value={userProfile.headline} onChange={(e) => setUserProfileField('headline', e.target.value)} />
                  <label>Email</label><input value={userProfile.email} onChange={(e) => setUserProfileField('email', e.target.value)} />
                  <label>Phone</label><input value={userProfile.phone} onChange={(e) => setUserProfileField('phone', e.target.value)} />
                  <label>City</label><input value={userProfile.city} onChange={(e) => setUserProfileField('city', e.target.value)} />
                  <label>Address</label><input value={userProfile.address} onChange={(e) => setUserProfileField('address', e.target.value)} />
                  <label>LinkedIn</label><input value={userProfile.linkedin} onChange={(e) => setUserProfileField('linkedin', e.target.value)} />
                  <label>GitHub</label><input value={userProfile.github} onChange={(e) => setUserProfileField('github', e.target.value)} />
                  <label>Website</label><input value={userProfile.website} onChange={(e) => setUserProfileField('website', e.target.value)} />
                  <label>Bio</label><textarea rows={3} value={userProfile.bio} onChange={(e) => setUserProfileField('bio', e.target.value)} />
                </div>
                <div className="profile-actions">
                  <button type="button" onClick={saveUserProfile}>Save User Profile</button>
                  <button type="button" className="primary" onClick={applyUserProfileToResume}>Apply Profile to Resume</button>
                </div>
              </div>
              <div className="form-grid">
                <label>Full Name</label><input value={form.full_name} onChange={(e) => setField('full_name', e.target.value)} />
                <label>Profile Title</label><input value={form.profile_title} onChange={(e) => setField('profile_title', e.target.value)} />
                <label>Email</label><input value={form.email} onChange={(e) => setField('email', e.target.value)} />
                <label>Phone</label><input value={form.phone} onChange={(e) => setField('phone', e.target.value)} />
                <label>City</label><input value={form.city} onChange={(e) => setField('city', e.target.value)} />
                <label>Address</label><input value={form.address} onChange={(e) => setField('address', e.target.value)} />
                <label>LinkedIn</label><input value={form.linkedin} onChange={(e) => setField('linkedin', e.target.value)} />
                <label>GitHub</label><input value={form.github} onChange={(e) => setField('github', e.target.value)} />
                <label>Website</label><input value={form.website} onChange={(e) => setField('website', e.target.value)} />
                <label>Profile Photo</label>
                <div className="photo-upload-wrap">
                  <label className="photo-picker">
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(e) => {
                        const f = e.target.files?.[0]
                        if (f) uploadProfilePhoto(f)
                        e.target.value = ''
                      }}
                    />
                    {uploadingPhoto ? 'Uploading...' : 'Upload Photo'}
                  </label>
                  {form.profile_pic ? (
                    <>
                      <img className="photo-preview" src={profilePicSrc()} alt="Profile" />
                      <button type="button" className="danger-link" onClick={() => setField('profile_pic', '')}>Remove</button>
                    </>
                  ) : (
                    <span className="muted">Optional: shown in photo templates</span>
                  )}
                </div>
                <label>Summary</label><textarea rows={4} value={form.summary} onChange={(e) => setField('summary', e.target.value)} />
                <label>Experience</label><textarea rows={4} value={form.experiences} onChange={(e) => setField('experiences', e.target.value)} placeholder="Job | Company | Start | End | Description" />
                <label>Education</label><textarea rows={3} value={form.educations} onChange={(e) => setField('educations', e.target.value)} placeholder="Degree | Institution | Start | End | Description" />
                <label>Projects</label><textarea rows={3} value={form.projects} onChange={(e) => setField('projects', e.target.value)} placeholder="Name | Role | Tech | Start | End | Description | Link" />
                <label>Skills (one per line)</label><textarea rows={4} value={form.skills} onChange={(e) => setField('skills', e.target.value)} />
              </div>
            </>
          ) : null}

          {step === 2 ? (
            <>
              <h2>AI Assistant</h2>
              <div className="form-grid">
                <label>Job Description</label>
                <textarea rows={5} value={jobDesc} onChange={(e) => setJobDesc(e.target.value)} />
                <label>AI Prompt</label>
                <textarea rows={3} value={aiPrompt} onChange={(e) => setAiPrompt(e.target.value)} placeholder="Example: tailor resume for data analyst role" />
              </div>
              <div className="btn-wrap">
                <button type="button" onClick={() => runApi('/ats-score', { ...payload(), job_description: jobDesc }, (d) => setAssist(`ATS Score: ${d.score || 0}/100\nMatch: ${d.text_similarity || 0}%`))}>ATS Score</button>
                <button type="button" onClick={() => runApi('/tailor-resume', { ...payload(), job_description: jobDesc }, (d) => {
                  if (d.tailored_summary) setField('summary', d.tailored_summary)
                  if (Array.isArray(d.recommended_skills)) setField('skills', d.recommended_skills.join('\n'))
                  setAssist('Tailor resume applied.')
                })}>Tailor Resume</button>
                <button type="button" onClick={() => runApi('/enhance-bullets', payload(), (d) => {
                  if (Array.isArray(d.experiences)) setField('experiences', expRowsToText(d.experiences))
                  if (Array.isArray(d.projects)) setField('projects', projRowsToText(d.projects))
                  setAssist(d.message || 'Bullets enhanced.')
                })}>Enhance Bullets</button>
                <button type="button" onClick={() => runApi('/ai-assistant', { ...payload(), prompt: aiPrompt, job_description: jobDesc }, (d) => {
                  setAssist(d.answer || 'No answer')
                  setAiPatch(d.apply_patch || null)
                })}>Ask AI Assistant</button>
                <button type="button" onClick={applyAiPatch} disabled={!aiPatch}>Apply AI Changes</button>
              </div>
              <pre className="assist-box">{assist || 'AI output appears here...'}</pre>
            </>
          ) : null}

          {step === 3 ? (
            <>
              <h2>Review & Generate</h2>
              <div className={`preview-box tone-${selectedTemplateVisual.tone}`} style={selectedTemplateVisual.vars}>
                <h3>{form.full_name || 'Your Name'}</h3>
                {form.profile_title ? <p>{form.profile_title}</p> : null}
                {contact ? <p className="muted">{contact}</p> : null}
                {form.summary ? <p>{form.summary}</p> : null}
                {skills.length ? <p><strong>Skills:</strong> {skills.join(', ')}</p> : null}
              </div>
              <div className="action-row">
                <button type="button" className="primary" onClick={generateResume} disabled={loading}>Generate Resume</button>
                <button type="button" onClick={previewPdf} disabled={loading}>Live PDF Preview</button>
                <button type="button" onClick={() => exportPdf().catch((e) => setMessage(e.message || 'PDF failed'))}>Download PDF</button>
              </div>
              <div className={`pdf-preview-wrap ${pdfPreviewUrl ? 'show' : ''}`}>
                {pdfPreviewUrl ? <iframe src={pdfPreviewUrl} title="PDF Preview" /> : <p className="muted">Click Live PDF Preview to load.</p>}
              </div>
            </>
          ) : null}
        </section>

        <aside className="card side-card">
          <h3>PDF Settings</h3>
          <div className="form-grid">
            <label>Template</label>
            <select value={cfg.template_name} onChange={(e) => setCfgField('template_name', e.target.value)}>
              {TEMPLATE_CHOICES.map((t) => <option key={t} value={t}>{t.replaceAll('_', ' ')}</option>)}
            </select>
            <label>Page Size</label>
            <select value={cfg.page_size} onChange={(e) => setCfgField('page_size', e.target.value)}>
              <option value="letter">Letter</option>
              <option value="a4">A4</option>
            </select>
            <label>Font</label>
            <select value={cfg.font_override} onChange={(e) => setCfgField('font_override', e.target.value)}>
              <option value="Helvetica">Default</option>
              <option value="Times">Times</option>
              <option value="Courier">Courier</option>
            </select>
            <label>Accent</label><input type="color" value={cfg.accent_color_override} onChange={(e) => setCfgField('accent_color_override', e.target.value)} />
            <label>Page Layout</label>
            <select value={cfg.layout_override} onChange={(e) => setCfgField('layout_override', e.target.value)}>
              <option value="">Auto</option>
              <option value="single_column">Single Column</option>
              <option value="two_column">Two Column</option>
            </select>
            <label>Header Layout</label>
            <select value={cfg.header_layout} onChange={(e) => setCfgField('header_layout', e.target.value)}>
              <option value="default">Default</option>
              <option value="left">Left</option>
              <option value="center">Center</option>
              <option value="split">Split</option>
            </select>
            <label>Heading Align</label>
            <select value={cfg.heading_align_override} onChange={(e) => setCfgField('heading_align_override', e.target.value)}>
              <option value="">Template Default</option>
              <option value="left">Left</option>
              <option value="center">Center</option>
              <option value="right">Right</option>
            </select>
            <label>Body Align</label>
            <select value={cfg.body_align_override} onChange={(e) => setCfgField('body_align_override', e.target.value)}>
              <option value="">Template Default</option>
              <option value="left">Left</option>
              <option value="justify">Justify</option>
              <option value="center">Center</option>
              <option value="right">Right</option>
            </select>
            <label>Margins</label>
            <select value={cfg.margin_preset} onChange={(e) => setCfgField('margin_preset', e.target.value)}>
              <option value="normal">Normal</option>
              <option value="compact">Compact</option>
              <option value="wide">Wide</option>
            </select>
            <label>Compact PDF</label>
            <input type="checkbox" checked={cfg.compact_mode} onChange={(e) => setCfgField('compact_mode', e.target.checked)} />
            <label>Font Size</label>
            <div className="fit-row">
              <input
                type="range"
                min="80"
                max="120"
                step="1"
                value={Math.round((cfg.font_scale || 1) * 100)}
                onChange={(e) => setFontScalePercent(e.target.value)}
              />
              <span className="muted">{Math.round((cfg.font_scale || 1) * 100)}%</span>
            </div>
            <label>Space Reduce</label>
            <select value={spacingMode} onChange={(e) => setSpacingMode(e.target.value)}>
              <option value="tight">Tight (Less Space)</option>
              <option value="normal">Normal</option>
              <option value="wide">Wide</option>
            </select>
            <label>Auto 1-Page Fit</label>
            <div className="fit-row">
              <button type="button" onClick={autoOnePageFit}>Auto 1-Page Fit</button>
              <span className="muted">{Math.round((cfg.font_scale || 1) * 100)}% font</span>
            </div>
          </div>
        </aside>
      </main>

      <div className="action-row card nav-card">
        <button type="button" onClick={() => setStep((s) => Math.max(0, s - 1))} disabled={step === 0}>Previous</button>
        <button type="button" className="primary" onClick={() => setStep((s) => Math.min(STEP_LABELS.length - 1, s + 1))} disabled={step === STEP_LABELS.length - 1}>Next</button>
      </div>

      {message ? <p className="status">{message}</p> : null}

      {previewTemplate ? (
        <div className="tpl-modal-backdrop" onClick={() => setPreviewTemplate(null)}>
          <div className={`tpl-modal tone-${templateVisual(previewTemplate).tone}`} style={templateVisual(previewTemplate).vars} onClick={(e) => e.stopPropagation()}>
            <div className="tpl-modal-head">
              <h3>{previewTemplate.name || 'Template Preview'}</h3>
              <button type="button" onClick={() => setPreviewTemplate(null)}>Close</button>
            </div>
            <img
              src={templateThumb(previewTemplate)}
              alt={previewTemplate.name || 'template preview'}
              className="tpl-modal-image"
              onError={(e) => {
                e.currentTarget.onerror = null
                e.currentTarget.src = templateThumb({ settings: { template: 'modern' } })
              }}
            />
            <p className="muted">
              {previewTemplate.category || 'General'} | {previewTemplate.mood || 'Balanced'} | {previewTemplate.tagline || 'Styled design'}
            </p>
            <div className="tpl-modal-actions">
              <button
                type="button"
                className="primary"
                onClick={() => {
                  applyTemplate(previewTemplate)
                  setPreviewTemplate(null)
                }}
              >
                Use Template
              </button>
              <button type="button" onClick={() => setPreviewTemplate(null)}>Cancel</button>
            </div>
          </div>
        </div>
      ) : null}

      {showUserCard ? (
        <div className="user-card-backdrop" onClick={() => setShowUserCard(false)}>
          <div className="user-card" onClick={(e) => e.stopPropagation()}>
            <div className="user-card-head">
              <span className="user-avatar large">{userInitial}</span>
              <div>
                <strong>{userProfile.display_name || form.full_name || 'User'}</strong>
                <p>{userProfile.headline || form.profile_title || 'Professional'}</p>
              </div>
            </div>
            <div className="user-card-grid">
              <div><span>Email</span><strong>{userProfile.email || form.email || '-'}</strong></div>
              <div><span>Phone</span><strong>{userProfile.phone || form.phone || '-'}</strong></div>
              <div><span>City</span><strong>{userProfile.city || form.city || '-'}</strong></div>
              <div><span>LinkedIn</span><strong>{userProfile.linkedin || form.linkedin || '-'}</strong></div>
              <div><span>GitHub</span><strong>{userProfile.github || form.github || '-'}</strong></div>
              <div><span>Website</span><strong>{userProfile.website || form.website || '-'}</strong></div>
            </div>
            <div className="user-card-actions">
              <button type="button" onClick={() => { setStep(1); setShowUserCard(false) }}>Edit Profile</button>
              <button type="button" className="primary" onClick={() => { applyUserProfileToResume(); setShowUserCard(false) }}>Apply to Resume</button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}
