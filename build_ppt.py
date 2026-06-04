"""
E-Commerce Ops Platform PPT — 15 slides, English, Élan design
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
import os

BASE = r'D:\github_product\E-commerce Operations Plugins\E-commerce-Operations-Plugins'
SS = os.path.join(BASE, 'screenshots')

# Colors
G, GL, GP = RGBColor(0xB8,0x94,0x5A), RGBColor(0xE8,0xDC,0xC8), RGBColor(0xF7,0xF0,0xE6)
D, D2 = RGBColor(0x2D,0x3A,0x4A), RGBColor(0x1A,0x25,0x32)
W, LB = RGBColor(0xFF,0xFF,0xFF), RGBColor(0xFA,0xF9,0xF7)
M, E = RGBColor(0x6E,0x68,0x5E), RGBColor(0x5A,0x8A,0x6A)
C, S = RGBColor(0xC4,0x5A,0x5A), RGBColor(0x5A,0x7A,0x9A)
SL, A = RGBColor(0x4A,0x50,0x58), RGBColor(0xB8,0x8A,0x4A)
LT = RGBColor(0xD6,0xD2,0xCA)
BC = RGBColor(0xB0,0xB5,0xBC)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
W_, H_ = prs.slide_width, prs.slide_height


def bg(slide, c=LB):
    slide.background.fill.solid(); slide.background.fill.fore_color.rgb = c

def rect(slide, l, t, w, h, fc=None):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, w, h)
    s.line.fill.background()
    if fc: s.fill.solid(); s.fill.fore_color.rgb = fc
    else: s.line.fill.background()
    return s

def bar(slide, l, t, w=Inches(0.06), h=Inches(0.5), c=G):
    return rect(slide, l, t, w, h, fc=c)

def tb(slide, l, t, w, h, txt, sz=14, b=False, c=SL, al=PP_ALIGN.LEFT, fn='Microsoft YaHei'):
    bx = slide.shapes.add_textbox(l, t, w, h)
    tf = bx.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.text = txt; p.font.size = Pt(sz); p.font.bold = b
    p.font.color.rgb = c; p.font.name = fn; p.alignment = al
    return bx

def rtf(slide, l, t, w, h):
    bx = slide.shapes.add_textbox(l, t, w, h); bx.text_frame.word_wrap = True; return bx.text_frame

def ap(tf, txt, sz=14, b=False, c=SL, al=PP_ALIGN.LEFT, fn='Microsoft YaHei', sa=Pt(6)):
    p = tf.add_paragraph(); p.text = txt; p.font.size = Pt(sz); p.font.bold = b
    p.font.color.rgb = c; p.font.name = fn; p.alignment = al; p.space_after = sa; return p

def title_bar(slide, t, sub=None):
    rect(slide, Inches(0), Inches(0), W_, Inches(0.06), fc=G)
    tb(slide, Inches(0.7), Inches(0.18), Inches(12), Inches(0.45), t, sz=26, b=True, c=D2)
    if sub: tb(slide, Inches(0.7), Inches(0.62), Inches(12), Inches(0.3), sub, sz=12, c=M)
    rect(slide, Inches(0.7), Inches(0.92), Inches(11.5), Inches(0.02), fc=GL)

def ss(slide, name, l, t, w=None, h=None):
    p = os.path.join(SS, name)
    if os.path.exists(p):
        kw = {}
        if w: kw['width'] = w
        if h: kw['height'] = h
        slide.shapes.add_picture(p, l, t, **kw)
        return True
    return False


# ══════════════════════════════════════════
# SLIDE 1 — Cover
# ══════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
bg(slide, D2)
rect(slide, Inches(0), Inches(0), W_, Inches(0.07), fc=G)
rect(slide, Inches(0), H_ - Inches(0.07), W_, Inches(0.07), fc=G)

tb(slide, Inches(0.8), Inches(1.0), Inches(7), Inches(0.5),
   'E-Commerce Operations Platform', sz=38, b=True, c=W)
tb(slide, Inches(0.8), Inches(1.6), Inches(9), Inches(0.35),
   'Unified multi-platform data sync · Intelligent analytics · Automated operations', sz=16, c=G)

tb(slide, Inches(0.8), Inches(2.5), Inches(8.5), Inches(2.5),
   'A production-ready backend platform that aggregates e-commerce data across\n'
   'Taobao, Shopify, Shopee, Lazada, and WooCommerce — providing real-time\n'
   'dashboards, sales analytics, inventory alerts, and AI-powered automation.\n\n'
   'Tech Stack: FastAPI + SQLAlchemy (async) · PostgreSQL / SQLite · Redis · Celery\n'
   'Deployment: Docker Compose · Jinja2 server-side rendering\n'
   'Design: Élan Design System — sand-tone palette with gold accents',
   sz=13.5, c=BC)

tb(slide, Inches(0.8), Inches(6.3), Inches(11), Inches(0.3),
   'Community Edition  v1.0  |  Élan Design System  |  2026', sz=11, c=M)

tags = ['📊 Dashboard', '📈 Sales Analytics', '📦 Inventory Mgmt', '🏪 Stores',
        '🤖 Automation Rules', '🎯 Product Selection', '💬 Auto Reply', '💡 Suggestions', '📋 Retrospectives']
for i, t in enumerate(tags):
    tb(slide, Inches(9.3), Inches(1.15 + i * 0.5), Inches(3.5), Inches(0.4),
       t, sz=12, c=W if i % 2 == 0 else LT)


# ══════════════════════════════════════════
# SLIDE 2 — Challenge & Solution
# ══════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
bg(slide)
title_bar(slide, 'The Challenge & Our Solution',
          'Why this platform? — Real problems faced by every cross-platform e-commerce seller')

pain = [
    ('🔴 Fragmented Management', 'Each platform has its own admin panel — no unified view of orders, products, or customers across Taobao, Shopify, Shopee, and Lazada.'),
    ('🔴 Manual Data Aggregation', 'Export → Excel merge → manual reports. Takes hours, error-prone, stale by the time it\'s done.'),
    ('🔴 No Real-Time Alerts', 'Stock shortages, refund spikes, sales drops discovered too late — after damage has been done.'),
    ('🔴 High AI Integration Barrier', 'Smart suggestions, auto-reply, analytics require complex multi-API integrations beyond most sellers.'),
]
for i, (t, d) in enumerate(pain):
    y = Inches(1.25 + i * 1.02)
    rect(slide, Inches(0.7), y, Inches(5.5), Inches(0.85), fc=W)
    bar(slide, Inches(0.7), y, h=Inches(0.85), c=C)
    tb(slide, Inches(0.9), y + Inches(0.05), Inches(5.1), Inches(0.2), t, sz=13, b=True, c=D2)
    tb(slide, Inches(0.9), y + Inches(0.28), Inches(5.1), Inches(0.5), d, sz=10, c=M)

rect(slide, Inches(6.6), Inches(1.25), Inches(6.1), Inches(4.4), fc=D2)
tb(slide, Inches(6.9), Inches(1.4), Inches(5.5), Inches(0.3), '✨  Platform Value Proposition', sz=17, b=True, c=G)

sols = [
    ('Unified Data Hub', 'Adapter pattern connects 5 platforms into one dashboard. All metrics, one screen.'),
    ('Auto Sync (30min)', 'Celery-powered incremental sync every 30 minutes with automatic retry.'),
    ('Smart Analytics Engine', 'Sales trends, inventory alerts, category distribution — real-time.'),
    ('4 Automation Pillars', 'Product selection · Auto reply · Suggestions · Retrospectives — AI-driven.'),
    ('Enterprise-Grade Security', 'JWT · bcrypt · Fernet encryption · Rate limiting · CSRF · Audit logs.'),
]
for i, (t, d) in enumerate(sols):
    y = Inches(1.9 + i * 0.75)
    tb(slide, Inches(6.9), y, Inches(5.5), Inches(0.22), f'▸ {t}', sz=11.5, b=True, c=W)
    tb(slide, Inches(6.9), y + Inches(0.24), Inches(5.5), Inches(0.45), d, sz=9.5, c=LT)


# ══════════════════════════════════════════
# SLIDE 3 — Tech Stack & Architecture
# ══════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
bg(slide)
title_bar(slide, 'Technology Stack & System Architecture',
          'Production-grade foundations · Adapter pattern · Dual-layer cache · Data isolation')

flows = [('🔌 Adapter Layer\nTaobao/Shopify/Shopee\nLazada/WooCommerce', D),
         ('🔄 Sync Orchestrator\nCelery periodic sync\nIncremental + retry', S),
         ('💾 Storage Layer\nPostgreSQL / SQLite\nRedis · Celery queue', E),
         ('📊 Analytics Engine\nSales · Inventory · Trends\nAggregation + reports', A),
         ('🤖 Automation\nSelection · Reply ·\nSuggest · Retrospect', C),
         ('🖥️ Presentation\nÉlan · Chart.js\nJinja2 SSR', D2)]
for i, (t, c_) in enumerate(flows):
    x = Inches(0.5 + i * 2.1)
    rect(slide, x, Inches(1.2), Inches(1.9), Inches(1.35), fc=W)
    rect(slide, x, Inches(1.2), Inches(1.9), Inches(0.04), fc=c_)
    tb(slide, x + Inches(0.08), Inches(1.32), Inches(1.74), Inches(1.1), t, sz=9.5, b=True, c=D2)
    if i < 5:
        tb(slide, x + Inches(1.9), Inches(1.7), Inches(0.2), Inches(0.3), '→', sz=16, b=True, c=G)

techs = [
    ('Backend', 'Python 3.14 · FastAPI · SQLAlchemy 2.0 (async) · Alembic · Celery', D),
    ('Database', 'PostgreSQL 16 (prod) / SQLite (dev) · Redis 7 (cache + MQ)', S),
    ('Frontend', 'Jinja2 SSR · Chart.js 4.4 · Bootstrap Icons · i18n CN/EN', E),
    ('DevOps', 'Docker Compose · Nginx · Cloudflare Tunnel · Fernet encryption', A),
]
for i, (t, d, c_) in enumerate(techs):
    x = Inches(0.5 + i * 3.15)
    rect(slide, x, Inches(2.75), Inches(2.95), Inches(0.85), fc=W)
    rect(slide, x, Inches(2.75), Inches(2.95), Inches(0.04), fc=c_)
    tb(slide, x + Inches(0.1), Inches(2.85), Inches(2.75), Inches(0.22), t, sz=11, b=True, c=c_)
    tb(slide, x + Inches(0.1), Inches(3.08), Inches(2.75), Inches(0.45), d, sz=9.5, c=M)

atf = rtf(slide, Inches(0.5), Inches(3.85), Inches(12.3), Inches(3.3))
ap(atf, 'Architecture Highlights', sz=14, b=True, c=D2, sa=Pt(5))
ap(atf, '🔹 Adapter Pattern — PlatformAdapter abstract base + AdapterFactory. Add a new platform with 5 method implementations, zero core code changes. Unified models (UnifiedOrder / UnifiedProduct / UnifiedCustomer) shield platform differences.', sz=10, c=SL, sa=Pt(2))
ap(atf, '🔹 Dual-Layer Cache — L1 in-memory (30s TTL / LRU) + L2 Redis, managed via @cached decorator. Dashboard data cached for 6 hours to reduce recomputation.', sz=10, c=SL, sa=Pt(2))
ap(atf, '🔹 Data Isolation — Three-tier model: User → Store → Entity. APIs inject identity via Depends(get_current_user), users only see their own stores.', sz=10, c=SL, sa=Pt(2))
ap(atf, '🔹 Rotatable Encryption — Fernet (AES-128-CBC + HMAC-SHA256) for API key storage, zero-downtime key rotation support.', sz=10, c=SL, sa=Pt(2))


# ══════════════════════════════════════════
# SLIDE 4 — Multi-Platform Integration
# ══════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
bg(slide)
title_bar(slide, 'Multi-Platform Integration',
          'Adapter pattern — one interface, five e-commerce platforms unified')

plats = [
    ('Taobao\n(淘宝)', 'OAuth 2.0 authorization\nHMAC-SHA256 API signing\nProducts / Orders / Customers', D2),
    ('Shopify', 'REST Admin API\nFull CRUD operations\nReal-time inventory sync', E),
    ('Shopee', 'Partner API\nSE Asia localization\nPer-store data isolation', S),
    ('Lazada', 'Open Platform\nMulti-country support\nCategory mapping', A),
    ('WooCommerce', 'WordPress REST API\nSelf-hosted data source\nFlexible extensions', C),
]
for i, (n, d, c_) in enumerate(plats):
    x = Inches(0.5 + i * 2.55)
    rect(slide, x, Inches(1.2), Inches(2.35), Inches(2.35), fc=W)
    rect(slide, x, Inches(1.2), Inches(2.35), Inches(0.05), fc=c_)
    tb(slide, x + Inches(0.12), Inches(1.38), Inches(2.11), Inches(0.55), n, sz=12, b=True, c=D2)
    tb(slide, x + Inches(0.12), Inches(1.95), Inches(2.11), Inches(1.4), d, sz=10, c=SL)

dtf = rtf(slide, Inches(0.5), Inches(3.85), Inches(12.3), Inches(3.4))
ap(dtf, 'How the Adapter Pattern Works', sz=14, b=True, c=D2, sa=Pt(5))
ap(dtf, 'All platforms inherit the same PlatformAdapter abstract base class implementing five core methods: get_orders(), get_products(), get_inventory(), sync_data(), get_analytics(). The AdapterFactory dynamically creates the correct adapter based on store.platform_type.', sz=10.5, c=SL, sa=Pt(3))
ap(dtf, '▸ Adding a new platform: ① Subclass PlatformAdapter  ② Implement 5 methods  ③ Register — zero changes to core code.', sz=10.5, c=D, b=True, sa=Pt(3))
ap(dtf, '▸ SyncOrchestrator manages order/product/customer sync with incremental (updated_since), automatic pagination, and 3x retry on failure. Sync tracked in sync_jobs table.', sz=10.5, c=D, b=True, sa=Pt(3))
ap(dtf, '▸ Unified data models — UnifiedOrder (amount/status/line items), UnifiedProduct (SKU/stock/price), UnifiedCustomer (email/address/order history) — abstract away platform differences.', sz=10.5, c=D, b=True, sa=Pt(3))


# ══════════════════════════════════════════
# SLIDE 5 — Dashboard
# ══════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
bg(slide)
title_bar(slide, 'Dashboard — Business Command Center',
          'Home page: all critical KPIs at a glance')

ss(slide, 'ppt_dashboard.png', Inches(0.55), Inches(1.2), w=Inches(7.2))

dtf = rtf(slide, Inches(8.2), Inches(1.2), Inches(4.6), Inches(5.8))
ap(dtf, 'Dashboard Features', sz=15, b=True, c=D2, sa=Pt(6))
items = [
    ('📊 KPI Cards', 'Total Sales, Orders, Avg. Order Value, Total Products — updated in real time with MoM change indicators.'),
    ('📈 Sales Trend Chart', '30-day sales curve rendered with Chart.js. Hover for daily breakdown.'),
    ('🥧 Category Distribution', 'Pie chart showing revenue share by product category.'),
    ('🏆 Top 10 Products', 'Ranked by revenue with sales volume and amount. Pinpoint star performers.'),
    ('⚠️ Stock Alerts', 'Auto-detected low-stock products highlighted in red. Click through to inventory.'),
    ('🔄 Data Sync Status', 'Last sync time displayed in header. One-click refresh button.'),
    ('🔗 Cross-Page Navigation', 'Dashboard cards link to Orders, Inventory, Sales pages for deep-dive analysis.'),
    ('📱 Desktop Optimized', 'Layout adapts gracefully from 1366px to 1920px — no horizontal scrolling.'),
]
for t, d in items:
    ap(dtf, t, sz=10.5, b=True, c=D, sa=Pt(1))
    ap(dtf, f'  {d}', sz=9, c=M, sa=Pt(3))


# ══════════════════════════════════════════
# SLIDE 6 — Sales + Inventory
# ══════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
bg(slide)
title_bar(slide, 'Sales Analytics & Inventory Management',
          'Multi-dimensional trends + intelligent stock monitoring')

ss(slide, 'ppt_sales.png', Inches(0.5), Inches(1.2), w=Inches(5.6))
ss(slide, 'ppt_inventory.png', Inches(6.4), Inches(1.2), w=Inches(5.6))

dtf = rtf(slide, Inches(0.5), Inches(4.15), Inches(12.3), Inches(3.0))
ap(dtf, 'Core Capabilities', sz=14, b=True, c=D2, sa=Pt(4))
ap(dtf, '▸ Sales Analytics: Three time windows (7/30/90 days) — Total Revenue, Order Count, Avg. Order Value, MoM Growth. Trend chart backed by daily detail table (date/revenue/orders/discount). Filter by platform.', sz=10, c=SL, sa=Pt(2))
ap(dtf, '▸ Inventory Management: Total/Low/Out-of-stock stat cards. Category pie chart for visual distribution. Alert list auto-filters products below configurable threshold.', sz=10, c=SL, sa=Pt(2))
ap(dtf, '💡 Close the Ops Loop: Dashboard daily check → spot sales decline → adjust marketing → inventory restock → measure impact next day.', sz=10.5, c=S, sa=Pt(2))


# ══════════════════════════════════════════
# SLIDE 7 — Orders + Stores
# ══════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
bg(slide)
title_bar(slide, 'Order Management & Store Management',
          'Cross-platform order tracking · One-click store connection')

ss(slide, 'ppt_orders.png', Inches(0.5), Inches(1.2), w=Inches(5.6))
ss(slide, 'ppt_stores.png', Inches(6.4), Inches(1.2), w=Inches(5.6))

dtf = rtf(slide, Inches(0.5), Inches(4.15), Inches(12.3), Inches(3.0))
ap(dtf, 'Core Capabilities', sz=14, b=True, c=D2, sa=Pt(4))
ap(dtf, '▸ Orders: Cross-platform unified order list — status filter (All/Paid/Refunded/Pending), keyword search by order ID or buyer email, paginated (20/page). No more logging into each platform separately.', sz=10, c=SL, sa=Pt(2))
ap(dtf, '▸ Stores: Add Taobao/Shopify/Shopee/Lazada stores with App Key, App Secret, and URL. Status indicators show connection health. Taobao OAuth 2.0 flow pre-built.', sz=10, c=SL, sa=Pt(2))
ap(dtf, '💡 Getting started: Register → Add store → Auto-sync → Dashboard populates → Explore automation. Takes just 5 minutes.', sz=10.5, c=S, sa=Pt(2))


# ══════════════════════════════════════════
# SLIDE 8 — Automation Rules
# ══════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
bg(slide)
title_bar(slide, 'Automation Rules Engine',
          'Condition-triggered workflows — your business, automated 24/7')

ss(slide, 'ppt_automation.png', Inches(0.5), Inches(1.15), w=Inches(6.5))

dtf = rtf(slide, Inches(7.3), Inches(1.15), Inches(5.5), Inches(5.8))
ap(dtf, 'Engine Details', sz=14, b=True, c=D2, sa=Pt(5))
for t, d in [
    ('Trigger Modes', 'Scheduled (cron expression) and event-driven (real-time evaluation on data changes).'),
    ('Condition Evaluation', '8 operators including between/in. Supports inventory, daily revenue, order count.'),
    ('Rule Templates', 'Built-in: Low Stock Alert (qty < 10), Sales Spike (> ¥10,000/day). One-click create.'),
    ('Action System', 'Notify (toast) + Log (audit trail). Extensible to auto-list/unlist, auto-price, coupon dispatch.'),
    ('Status Monitoring', 'Active rules + today\'s executions shown on stat cards. Each rule independently toggled.'),
    ('Audit & Compliance', 'Every rule creation/activation/modification logged to audit trail with timestamp and user ID.'),
]:
    ap(dtf, f'▸ {t}', sz=10.5, b=True, c=D, sa=Pt(1))
    ap(dtf, f'  {d}', sz=9, c=M, sa=Pt(4))


# ══════════════════════════════════════════
# SLIDE 9 — Product Selection + Auto Reply
# ══════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
bg(slide)
title_bar(slide, 'Product Selection & Auto Reply',
          'AI-powered product discovery + intelligent customer service automation')

ss(slide, 'ppt_product_selections.png', Inches(0.5), Inches(1.2), w=Inches(5.6))
ss(slide, 'ppt_auto_reply.png', Inches(6.4), Inches(1.2), w=Inches(5.6))

dtf = rtf(slide, Inches(0.5), Inches(4.1), Inches(12.3), Inches(3.1))
ap(dtf, 'Product Selection', sz=12, b=True, c=D2, sa=Pt(2))
ap(dtf, 'Composite scoring (0-100) from sales data, margin analysis, and market trends. Auto-scan identifies trending products from 30-day sales. Review workflow: pending → approved/rejected. Stats: total, pending, approved, avg score.', sz=9.5, c=SL, sa=Pt(3))
ap(dtf, 'Auto Reply', sz=12, b=True, c=D2, sa=Pt(2))
ap(dtf, 'Three matching modes: contains/exact/regex. Priority ordering — higher priority fires first. Built-in test tool: type a mock message, see which rule matches. Stats: total rules, enabled, total matches.', sz=9.5, c=SL, sa=Pt(3))


# ══════════════════════════════════════════
# SLIDE 10 — Suggestions + Retrospectives
# ══════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
bg(slide)
title_bar(slide, 'Operations Suggestions & Retrospectives',
          'AI-driven decision support + periodic business reviews')

ss(slide, 'ppt_suggestions.png', Inches(0.5), Inches(1.2), w=Inches(5.6))
ss(slide, 'ppt_retrospectives.png', Inches(6.4), Inches(1.2), w=Inches(5.6))

dtf = rtf(slide, Inches(0.5), Inches(4.1), Inches(12.3), Inches(3.1))
ap(dtf, 'Operations Suggestions', sz=12, b=True, c=D2, sa=Pt(2))
ap(dtf, 'Four types: Restock alerts / Price adjustments / Marketing campaigns / Inventory optimization. AI analyzes recent data, generates priority-tagged (High/Med/Low) suggestions. Apply or Dismiss with adoption rate tracking.', sz=9.5, c=SL, sa=Pt(3))
ap(dtf, 'Retrospectives', sz=12, b=True, c=D2, sa=Pt(2))
ap(dtf, 'Weekly/Monthly/Quarterly cycles. Auto-generates standardized reports with KPIs (revenue, orders, AOV, refund rate) and MoM comparisons. AI insights + action items. Lifecycle: Draft → Published → Archived.', sz=9.5, c=SL, sa=Pt(3))


# ══════════════════════════════════════════
# SLIDE 11 — Settings + Logs + Security
# ══════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
bg(slide)
title_bar(slide, 'Settings · Audit Logs · Security',
          'Configuration, compliance, and defense in depth')

ss(slide, 'ppt_settings.png', Inches(0.5), Inches(1.15), w=Inches(5.4))
ss(slide, 'ppt_logs.png', Inches(6.3), Inches(1.15), w=Inches(5.4))

dtf = rtf(slide, Inches(0.5), Inches(4.1), Inches(5.4), Inches(3.0))
ap(dtf, 'System Settings', sz=12, b=True, c=D2, sa=Pt(2))
ap(dtf, 'System name, sync interval (15/30/60 min), report cache TTL (1/3/6/12 h). API key management — OpenAI, Claude, DeepSeek, Qwen, ERNIE — all encrypted at rest with Fernet.', sz=9.5, c=SL, sa=Pt(2))
ap(dtf, 'Audit Logs', sz=12, b=True, c=D2, sa=Pt(2))
ap(dtf, 'Every action (create/update/delete/login/register) logged with timestamp, resource ID, detail, IP. Filter by action/resource type. Paginated for compliance audits.', sz=9.5, c=SL, sa=Pt(2))

stf = rtf(slide, Inches(6.3), Inches(4.1), Inches(6.5), Inches(3.0))
ap(stf, 'Security Protections', sz=12, b=True, c=D2, sa=Pt(2))
secs = [
    ('JWT stateless auth', 'HttpOnly + SameSite=Lax cookies, configurable expiry'),
    ('bcrypt password hashing', 'Built-in strength validation, no plaintext storage'),
    ('Comprehensive rate limiting', 'Login 5/min, register 10/min, API 60/min per user'),
    ('Fernet encryption', 'AES-128-CBC + HMAC-SHA256 for API keys, key rotation support'),
    ('Security headers', 'X-Content-Type-Options=nosniff, X-Frame-Options=DENY, HSTS'),
    ('CSRF protection', 'Double-submit cookie pattern, all POST/PUT/DELETE routes enforced'),
    ('Session management', 'Token expiry configurable (1h / 24h / 7d), refresh on activity'),
    ('Full audit trail', 'All sensitive operations logged for forensics and compliance'),
]
for t, d in secs:
    ap(stf, f'✓  {t}', sz=9.5, b=True, c=E, sa=Pt(1))
    ap(stf, f'    {d}', sz=8.5, c=M, sa=Pt(2))


# ══════════════════════════════════════════
# SLIDE 12 — Pro Module System
# ══════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
bg(slide)
title_bar(slide, 'Pro Module System',
          'Community Edition free + pluggable Pro modules — extensible by design')

rect(slide, Inches(0.6), Inches(1.4), Inches(5.5), Inches(5.4), fc=D2)
tb(slide, Inches(0.9), Inches(1.6), Inches(5), Inches(0.35), '🧩  Community Edition (Free)', sz=18, b=True, c=W)
tb(slide, Inches(0.9), Inches(2.0), Inches(5), Inches(0.25), 'Open-source, ready to use out of the box', sz=11, c=G)
ce = ['✓  Real-time Dashboard (KPI + trends + categories)',
      '✓  Order Management (cross-platform + filter + page)',
      '✓  Inventory Management (distribution + alerts)',
      '✓  Store Management (5 platforms + status)',
      '✓  Automation Rules Engine (templates + toggle)',
      '✓  Operation Audit Logs + System Settings',
      '✓  Encrypted API Key Management',
      '✓  i18n (CN/EN) + Élan Design System',
      '✓  JWT Auth + Rate Limiting + Security Headers']
for i, item in enumerate(ce):
    tb(slide, Inches(0.9), Inches(2.5 + i * 0.36), Inches(5), Inches(0.3), item, sz=10.5, c=LT)

tb(slide, Inches(6.2), Inches(3.6), Inches(0.5), Inches(0.5), '→', sz=28, b=True, c=G)

rect(slide, Inches(6.8), Inches(1.4), Inches(5.9), Inches(5.4), fc=W)
rect(slide, Inches(6.8), Inches(1.4), Inches(5.9), Inches(0.05), fc=G)
tb(slide, Inches(7.1), Inches(1.6), Inches(5.3), Inches(0.35), '⭐  Pro Modules (Commercial)', sz=18, b=True, c=D2)
tb(slide, Inches(7.1), Inches(2.0), Inches(5.3), Inches(0.25), 'Advanced features on top of Community Edition', sz=11, c=M)
pros = [
    ('📊  Sales Analytics Pro', '7/30/90 day multi-dim trends + MoM growth + daily detail'),
    ('🎯  Product Selection', 'Composite score 0-100 + auto-scan + review workflow'),
    ('💬  Auto Reply', '3 match modes + priority + test tool + usage stats'),
    ('💡  Operations Suggestions', '4 suggestion types + AI generation + adoption tracking'),
    ('📋  Retrospectives', 'Weekly/monthly/quarterly + MoM + AI insights + action items'),
    ('🔗  Taobao OAuth', 'Browser-based authorization, self-service store binding'),
]
for i, (t, d) in enumerate(pros):
    y = Inches(2.6 + i * 0.65)
    tb(slide, Inches(7.1), y, Inches(5.3), Inches(0.25), t, sz=11, b=True, c=D)
    tb(slide, Inches(7.3), y + Inches(0.25), Inches(5.1), Inches(0.35), d, sz=10, c=M)


# ══════════════════════════════════════════
# SLIDE 13 — User Guide
# ══════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
bg(slide)
title_bar(slide, 'Quick Start — 5 Steps to Go Live',
          'From registration to full operation in 5 minutes')

steps = [
    ('01', 'Sign Up / Login', 'Register or use demo login (demo@example.com / Demo1234!). Auto-redirect to dashboard.', G),
    ('02', 'Add a Store', 'Stores → Add Store → Select platform. Enter App Key / Secret / URL. Auto-sync begins on first connection.', S),
    ('03', 'Sync Data', 'Wait 1-2 min for initial sync. Dashboard auto-populates. Adjust sync interval in Settings (15/30/60 min).', E),
    ('04', 'Configure Automation', 'Create stock alert / sales spike rules. Set auto-reply keywords. Generate suggestions & retrospectives.', A),
    ('05', 'Daily Operations', 'Monitor dashboard → analyze sales → manage inventory. Run retrospectives to guide strategy. Refine automations.', D2),
]
for i, (num, t, d, c_) in enumerate(steps):
    x = Inches(0.5 + i * 2.5)
    rect(slide, x, Inches(1.25), Inches(2.3), Inches(2.5), fc=W)
    rect(slide, x, Inches(1.25), Inches(2.3), Inches(0.04), fc=c_)
    tb(slide, x + Inches(0.1), Inches(1.38), Inches(0.5), Inches(0.35), num, sz=20, b=True, c=c_)
    tb(slide, x + Inches(0.1), Inches(1.73), Inches(2.1), Inches(0.25), t, sz=12, b=True, c=D2)
    tb(slide, x + Inches(0.1), Inches(2.05), Inches(2.1), Inches(1.4), d, sz=9.5, c=M)

rect(slide, Inches(0.5), Inches(4.1), Inches(12.3), Inches(2.8), fc=D2)
stf = rtf(slide, Inches(0.8), Inches(4.25), Inches(11.7), Inches(2.4))
ap(stf, 'Tips for Best Experience', sz=13, b=True, c=G, sa=Pt(5))
ap(stf, '💡  Use Chrome / Edge for optimal Chart.js rendering and responsive layout.', sz=10.5, c=LT, sa=Pt(2))
ap(stf, '💡  Data sync runs every 30 min by default. Adjust to 15 or 60 min in Settings. Celery auto-retries on failure.', sz=10.5, c=LT, sa=Pt(2))
ap(stf, '💡  On first use, click "Generate Suggestions" and "Generate Retrospective" to establish baseline analysis data.', sz=10.5, c=LT, sa=Pt(2))
ap(stf, '💡  Configure AI provider keys (OpenAI, Claude, DeepSeek, Qwen, ERNIE) to power suggestion/analysis features.', sz=10.5, c=LT, sa=Pt(2))
ap(stf, '💡  Use the built-in demo account for evaluation — it comes pre-loaded with sample sales data and configured stores.', sz=10.5, c=LT, sa=Pt(2))


# ══════════════════════════════════════════
# SLIDE 14 — Roadmap
# ══════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
bg(slide)
title_bar(slide, 'Roadmap', 'Delivered + Planned — continuous evolution')

for i, (t, d, c_) in enumerate([
    ('✅ Phase 1: MVP Foundation', 'FastAPI + 7 tables + 5 platform adapters + analytics engine + Celery sync', G),
    ('✅ Phase 2: 4 Automation Pillars', 'Product Selection + Auto Reply + Suggestions + Retrospectives — full automation loop', E),
]):
    y = Inches(1.3 + i * 0.55)
    rect(slide, Inches(0.6), y, Inches(12.1), Inches(0.45), fc=W)
    bar(slide, Inches(0.6), y, h=Inches(0.45), c=c_)
    tb(slide, Inches(0.85), y + Inches(0.04), Inches(3.5), Inches(0.35), t, sz=11, b=True, c=D2)
    tb(slide, Inches(4.5), y + Inches(0.04), Inches(8), Inches(0.35), d, sz=10.5, c=M)

tb(slide, Inches(0.6), Inches(2.5), Inches(12.1), Inches(0.25), '————  PLANNED  ————', sz=11, c=G, al=PP_ALIGN.CENTER)

for i, (t, d, c_) in enumerate([
    ('🔜 Phase 3: Operations Deepening', 'P0: Product editing (price/listing/title) → P0: Taobao OAuth flow → P1: Auto-action expansion (price/listing/coupon) → P1: Refund/return processing', S),
    ('🔜 Phase 4: Intelligence Enhancement', 'P2: Profit analytics (commissions/insurance/fees for true net profit) → P2: Inventory prediction (consumption-rate-based forecasting) → P2: Notification channels (DingTalk/WeCom/SMS)', A),
    ('🔜 Phase 5: Enterprise Scale', 'P2: HSM integration → P3: Core module test coverage → P3: Kubernetes deployment → P3: Multi-tenant SaaS architecture', C),
]):
    y = Inches(2.9 + i * 1.15)
    rect(slide, Inches(0.6), y, Inches(12.1), Inches(1.0), fc=W)
    bar(slide, Inches(0.6), y, h=Inches(1.0), c=c_)
    tb(slide, Inches(0.85), y + Inches(0.06), Inches(4), Inches(0.25), t, sz=12, b=True, c=D2)
    tb(slide, Inches(0.85), y + Inches(0.32), Inches(11.5), Inches(0.6), d, sz=10, c=M)


# ══════════════════════════════════════════
# SLIDE 15 — Thank You
# ══════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
bg(slide, D2)
rect(slide, Inches(0), Inches(0), W_, Inches(0.07), fc=G)
rect(slide, Inches(0), H_ - Inches(0.07), W_, Inches(0.07), fc=G)

tb(slide, Inches(0.8), Inches(1.5), Inches(11), Inches(0.7),
   'Thank You', sz=44, b=True, c=W)
tb(slide, Inches(0.8), Inches(2.3), Inches(11), Inches(0.4),
   'E-Commerce Operations Platform  ·  Community Edition', sz=18, c=G)

ctf = rtf(slide, Inches(0.8), Inches(3.3), Inches(11), Inches(3.2))
ap(ctf, 'Resources', sz=16, b=True, c=G, sa=Pt(10))
ap(ctf, 'GitHub    https://github.com/veron-spec/E-commerce-Operations-Plugins', sz=13, c=W, sa=Pt(6))
ap(ctf, 'Tech      FastAPI · SQLAlchemy 2.0 · PostgreSQL 16 · Redis 7 · Celery · Chart.js', sz=13, c=W, sa=Pt(6))
ap(ctf, 'Design    Élan Design System — Elegance in every pixel', sz=13, c=W, sa=Pt(6))
ap(ctf, 'License   Community Edition — Open Source', sz=13, c=W, sa=Pt(6))
ap(ctf, '', sz=8)
ap(ctf, 'Star / Fork / Issues welcome — let\'s make e-commerce operations smarter together!', sz=15, b=True, c=G)

# Save
out = os.path.join(BASE, 'ECommerce_Ops_Platform_Presentation.pptx')
if os.path.exists(out): os.remove(out)
prs.save(out)
print(f'✅ PPT saved: {out}')
print(f'   Slides: {len(prs.slides)}')
print(f'   Size: {os.path.getsize(out) / 1024:.0f} KB')
