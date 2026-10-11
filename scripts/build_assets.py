"""プロフィール README 用の SVG(header / about / stack / footer)を生成する。

使い方: python3 scripts/build_assets.py
アイコンは skillicons.dev と Simple Icons から取得して SVG に埋め込む
(GitHub の画像表示では SVG 内からの外部読み込みができないため)。
"""

import re
import urllib.request
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

SANS = '"Inter","SF Pro Display",-apple-system,"Segoe UI",Roboto,"Helvetica Neue","Hiragino Sans","Noto Sans JP","Yu Gothic",sans-serif'
MONO = '"JetBrains Mono","SFMono-Regular",Menlo,Consolas,"Liberation Mono",monospace'
BG = "#09090b"
ICON_BG = "#1c1c22"

# AWS 公式アーキテクチャアイコンのカテゴリ色
AWS_STORAGE, AWS_COMPUTE, AWS_SECURITY, AWS_FRONTEND, AWS_MESSAGING = "#7AA116", "#ED7100", "#DD344C", "#C7131F", "#E7157B"

# カテゴリキー: (表示名, アクセント色, 補足, [(表示名, 取得元, ID)])
# 取得元: skill=skillicons.dev / si=Simple Icons / text=文字タイル("文字|文字色|背景色")
STACK = {
    "frontend": ("Frontend · React", "#818cf8", "", [
        ("React", "skill", "react"), ("Next.js", "skill", "nextjs"),
        ("Redux", "skill", "redux"), ("Zod", "si", "zod"),
        ("RHF", "si", "reacthookform"), ("MUI", "skill", "materialui"),
        ("Tailwind", "skill", "tailwind"), ("shadcn/ui", "si", "shadcnui"),
        ("NextAuth", "text", "Auth|#ffffff|#7c3aed"), ("Jest", "skill", "jest"),
        ("Vitest", "skill", "vitest"),
    ]),
    "backend": ("Backend", "#f472b6", "", [
        ("PHP", "skill", "php"), ("Laravel", "skill", "laravel"),
        ("PHPUnit", "text", "PU|#ffffff|#3c9cd7"), ("TypeScript", "skill", "ts"),
        ("NestJS", "skill", "nestjs"), ("Prisma", "skill", "prisma"),
        ("GraphQL", "skill", "graphql"), ("Python", "skill", "py"),
        ("FastAPI", "skill", "fastapi"),
    ]),
    "web": ("Web Basics", "#fb923c", "", [
        ("HTML", "skill", "html"), ("CSS", "skill", "css"),
        ("JavaScript", "skill", "js"), ("jQuery", "skill", "jquery"),
    ]),
    "vue": ("Vue.js 2.x", "#4ade80", "Options / Composition API", [
        ("Vue.js", "skill", "vue"), ("Vuetify 2", "skill", "vuetify"),
    ]),
    "mobile": ("Mobile", "#22d3ee", "", [
        ("React Native", "skill", "react"), ("Expo", "si", "expo"),
    ]),
    "database": ("Database", "#60a5fa", "", [
        ("MySQL", "skill", "mysql"), ("PostgreSQL", "skill", "postgres"),
        ("Supabase", "skill", "supabase"),
    ]),
    "aws": ("AWS", "#fbbf24", "", [
        ("AWS", "skill", "aws"), ("S3", "text", "S3|#ffffff|" + AWS_STORAGE),
        ("EC2", "text", "EC2|#ffffff|" + AWS_COMPUTE), ("ECS", "text", "ECS|#ffffff|" + AWS_COMPUTE),
        ("Amplify", "text", "Amp|#ffffff|" + AWS_FRONTEND), ("Cognito", "text", "Cog|#ffffff|" + AWS_SECURITY),
        ("Secrets Mgr", "text", "Sec|#ffffff|" + AWS_SECURITY), ("SES", "text", "SES|#ffffff|" + AWS_MESSAGING),
    ]),
    "devops": ("Deploy / DevOps", "#38bdf8", "Docker での環境構築経験あり", [
        ("Actions", "skill", "githubactions"), ("Vercel", "skill", "vercel"),
        ("Docker", "skill", "docker"), ("Compose", "skill", "docker"),
        ("Makefile", "text", "Mk|#e4e4e7|#3f3f46"), ("pnpm", "skill", "pnpm"),
    ]),
    "ai": ("AI", "#c084fc", "Gemini API 組み込み / Claude Code × git worktree で並行開発", [
        ("Gemini API", "si", "googlegemini"), ("Claude Code", "si", "claude"),
        ("git worktree", "skill", "git"),
        ("Cursor", "si", "cursor"), ("Copilot", "si", "githubcopilot"),
        ("Ollama", "si", "ollama"),
    ]),
    "motion": ("Motion / 3D", "#38bdf8", "勉強中", [
        ("Remotion", "text", "R|#ffffff|#0b84f3"), ("Three.js", "skill", "threejs"),
    ]),
    "task": ("Task Management", "#94a3b8", "", [
        ("Notion", "skill", "notion"), ("Backlog", "text", "B|#ffffff|#42ce9f"),
        ("GitHub Projects", "skill", "github"),
    ]),
}


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "profile-asset-builder"})
    with urllib.request.urlopen(req, timeout=20) as res:
        return res.read().decode()


def prefix_ids(svg: str, prefix: str) -> str:
    """アイコン同士で id が衝突しないよう接頭辞を付ける。"""
    for i in set(re.findall(r'id="([^"]+)"', svg)):
        svg = svg.replace(f'id="{i}"', f'id="{prefix}{i}"')
        svg = svg.replace(f"url(#{i})", f"url(#{prefix}{i})")
        svg = svg.replace(f'href="#{i}"', f'href="#{prefix}{i}"')
    return svg


def luminance(hex_color: str) -> float:
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def icon_body(source: str, key: str, uid: str) -> str:
    """viewBox 0 0 256 256 前提のアイコン中身を返す。"""
    if source == "skill":
        raw = fetch(f"https://skillicons.dev/icons?i={key}")
        inner = re.search(r'<g transform="translate\(0, 0\)">\s*(<svg.*</svg>)\s*</g>', raw, re.S)
        if not inner:
            raise RuntimeError(f"skillicons: {key} の取得に失敗")
        return prefix_ids(inner.group(1), uid)
    if source == "si":
        raw = fetch(f"https://cdn.simpleicons.org/{key}")
        color = re.search(r'fill="(#[0-9A-Fa-f]{6})"', raw).group(1)
        if luminance(color) < 0.25:
            color = "#ffffff"
        path = re.search(r'<path d="([^"]+)"', raw).group(1)
        return (f'<rect width="256" height="256" rx="60" fill="{ICON_BG}"/>'
                f'<path transform="translate(56 56) scale(6)" fill="{color}" d="{path}"/>')
    text, color, bg = key.split("|")
    size = {1: 132, 2: 108, 3: 88}.get(len(text), 72)
    return (f'<rect width="256" height="256" rx="60" fill="{bg}"/>'
            f"<text x=\"128\" y=\"128\" dy=\".35em\" text-anchor=\"middle\" font-family='{SANS}' "
            f'font-size="{size}" font-weight="800" letter-spacing="-2" fill="{color}">{text}</text>')


BASE_CSS = f"""
    .sans{{font-family:{SANS}}}.mono{{font-family:{MONO}}}
    .blob{{animation:float 16s ease-in-out infinite alternate}}
    .blob.b2{{animation-duration:21s;animation-direction:alternate-reverse}}
    .blob.b3{{animation-duration:26s}}
    @keyframes float{{from{{transform:translate(0,0) scale(1)}}to{{transform:translate(60px,30px) scale(1.15)}}}}
    .beam{{animation:beam 7s linear infinite}}
    @keyframes beam{{from{{stroke-dashoffset:100}}to{{stroke-dashoffset:0}}}}
    .rise{{animation:rise .8s cubic-bezier(.2,.8,.2,1) backwards}}
    @keyframes rise{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:translateY(0)}}}}"""

REDUCED_MOTION_CSS = """
    @media (prefers-reduced-motion:reduce){*{animation:none!important}}"""


def backdrop(w: int, h: int, blobs: list[tuple[int, int, int, str, float]], grid: int = 48) -> str:
    """黒地 + ぼかした光 + 中心が濃く外側に消えるグリッド。"""
    lines = "".join(f'<line x1="{x}" y1="0" x2="{x}" y2="{h}"/>' for x in range(grid, w, grid))
    lines += "".join(f'<line x1="0" y1="{y}" x2="{w}" y2="{y}"/>' for y in range(grid, h, grid))
    glows = "".join(
        f'<circle class="blob b{i % 3 + 1}" cx="{cx}" cy="{cy}" r="{r}" fill="{c}" opacity="{o}"/>'
        for i, (cx, cy, r, c, o) in enumerate(blobs))
    return f'''<rect width="{w}" height="{h}" fill="{BG}"/>
    <g filter="url(#blur)">{glows}</g>
    <g stroke="#ffffff" stroke-opacity=".06" mask="url(#gridFade)">{lines}</g>
    <rect width="{w}" height="{h}" filter="url(#grain)" opacity=".07"/>'''


def common_defs(w: int, h: int, blur: int = 90) -> str:
    return f'''<filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="{blur}"/></filter>
    <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .9 0"/></filter>
    <radialGradient id="fade" cx=".5" cy=".35" r=".7"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
    <mask id="gridFade"><rect width="{w}" height="{h}" fill="url(#fade)"/></mask>
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".35"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
    <clipPath id="frame"><rect width="{w}" height="{h}" rx="24"/></clipPath>'''


def frame_border(w: int, h: int) -> str:
    return (f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="23.5" fill="none" stroke="#fff" stroke-opacity=".1"/>'
            f'<rect x="{w * .2}" y="0" width="{w * .6}" height="1" fill="url(#edge)"/>')


def glass_card(x: float, y: float, w: float, h: float, accent: str, gid: str, beam_delay: float) -> str:
    """半透明のカード。上辺のハイライト、角の色光、外周を走る光の線を持つ。"""
    return f'''<radialGradient id="{gid}" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate({x} {y}) scale({max(w, h) * .9})">
        <stop offset="0" stop-color="{accent}" stop-opacity=".22"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient>
      <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="#18181b" fill-opacity=".72"/>
      <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="url(#{gid})"/>
      <rect x="{x + .5}" y="{y + .5}" width="{w - 1}" height="{h - 1}" rx="17.5" fill="none" stroke="#fff" stroke-opacity=".09"/>
      <rect x="{x + 24}" y="{y}" width="{w - 48}" height="1" fill="url(#edge)"/>
      <rect class="beam" x="{x + .5}" y="{y + .5}" width="{w - 1}" height="{h - 1}" rx="17.5" fill="none" stroke="{accent}" stroke-width="1.5" stroke-linecap="round" pathLength="100" stroke-dasharray="9 91" style="animation-delay:{beam_delay:.2f}s"/>'''


CODE = [
    [("export const ", "#c084fc"), ("nozomu", "#fafafa"), (" = {", "#a1a1aa")],
    [("  role", "#7dd3fc"), (": ", "#a1a1aa"), ('"Software Engineer"', "#86efac"), (",", "#a1a1aa")],
    [("  builds", "#7dd3fc"), (": [", "#a1a1aa"), ('"web"', "#86efac"), (", ", "#a1a1aa"), ('"mobile"', "#86efac"), (", ", "#a1a1aa"), ('"api"', "#86efac"), ("],", "#a1a1aa")],
    [("  stack", "#7dd3fc"), (": [", "#a1a1aa"), ('"TypeScript"', "#86efac"), (", ", "#a1a1aa"), ('"Next.js"', "#86efac"), (", ", "#a1a1aa"), ('"NestJS"', "#86efac"), ("],", "#a1a1aa")],
    [("  workflow", "#7dd3fc"), (": ", "#a1a1aa"), ('"Claude Code × git worktree"', "#86efac"), (",", "#a1a1aa")],
    [("  writes", "#7dd3fc"), (": ", "#a1a1aa"), ('"zenn.dev/hopetekigozaru"', "#86efac"), (",", "#a1a1aa")],
    [("} ", "#a1a1aa"), ("as const", "#c084fc"), (";", "#a1a1aa")],
]


def build_header() -> str:
    w, h = 1200, 440
    cx, cy, cw, ch = 690, 78, 466, 286
    code_lines = []
    for i, tokens in enumerate(CODE):
        spans = "".join(f'<tspan fill="{c}">{escape(t)}</tspan>' for t, c in tokens)
        y = cy + 86 + i * 27
        code_lines.append(
            f'<g class="rise" style="animation-delay:{1.0 + i * .18:.2f}s">'
            f'<text x="{cx + 24}" y="{y}" class="mono" font-size="13" fill="#52525b" text-anchor="end" dx="8">{i + 1}</text>'
            f'<text x="{cx + 48}" y="{y}" class="mono" font-size="14" xml:space="preserve">{spans}</text></g>')
    last_y = cy + 86 + (len(CODE) - 1) * 27
    caret_x = cx + 48 + len("} as const;") * 8.43 + 4

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">
  <title id="t">NOZOMU — Software Engineer</title>
  <desc id="d">Web / Mobile / API。Claude Code × git worktree で並行開発。個人開発で undug をつくっている。</desc>
  <defs>
    {common_defs(w, h)}
    <linearGradient id="titleFill" x1="0" y1="0" x2="0" y2="1"><stop offset=".15" stop-color="#ffffff"/><stop offset="1" stop-color="#a1a1aa"/></linearGradient>
    <linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="-260" y1="0" x2="0" y2="0">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".9"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
      <animateTransform attributeName="gradientTransform" type="translate" values="0 0;900 0;900 0" keyTimes="0;.4;1" dur="7s" begin="1.6s" repeatCount="indefinite"/>
    </linearGradient>
    <linearGradient id="pill" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#818cf8" stop-opacity=".18"/><stop offset="1" stop-color="#f472b6" stop-opacity=".12"/></linearGradient>
  </defs>
  <style>{BASE_CSS}
    .dot{{animation:pulse 2s ease-in-out infinite}}@keyframes pulse{{50%{{opacity:.35}}}}
    .ring{{transform-box:fill-box;transform-origin:center;animation:ring 2s ease-out infinite}}
    @keyframes ring{{from{{opacity:.6;transform:scale(1)}}to{{opacity:0;transform:scale(2.6)}}}}
    .caret{{animation:caret 1.1s steps(1) infinite}}@keyframes caret{{50%{{opacity:0}}}}{REDUCED_MOTION_CSS}
  </style>
  <g clip-path="url(#frame)">
    {backdrop(w, h, [(980, 40, 220, "#6366f1", .55), (260, 470, 240, "#db2777", .35), (1160, 420, 180, "#06b6d4", .35)])}

    <g class="rise" style="animation-delay:.1s">
      <rect x="72" y="78" width="252" height="32" rx="16" fill="url(#pill)" stroke="#fff" stroke-opacity=".12"/>
      <circle class="ring" cx="92" cy="94" r="4" fill="#34d399"/>
      <circle class="dot" cx="92" cy="94" r="4" fill="#34d399"/>
      <text x="106" y="99" class="mono" font-size="13" fill="#d4d4d8" letter-spacing=".5">github.com/hosokaSfi</text>
    </g>
    <g class="rise" style="animation-delay:.25s">
      <text x="66" y="236" class="sans" font-size="124" font-weight="800" letter-spacing="-4" fill="url(#titleFill)">NOZOMU</text>
      <text x="66" y="236" class="sans" font-size="124" font-weight="800" letter-spacing="-4" fill="url(#shine)" opacity=".5">NOZOMU</text>
    </g>
    <g class="rise" style="animation-delay:.45s">
      <text x="72" y="284" class="sans" font-size="28" font-weight="600" fill="#f4f4f5" letter-spacing="-.5">Software Engineer</text>
      <text x="72" y="318" class="mono" font-size="15" fill="#a1a1aa" letter-spacing="1">Web  ·  Mobile  ·  API</text>
    </g>
    <g class="rise" style="animation-delay:.65s">
      <rect x="72" y="350" width="28" height="1.5" fill="#818cf8"/>
      <text x="112" y="356" class="sans" font-size="14" fill="#a1a1aa">Claude Code × git worktree で並行開発<tspan fill="#52525b">  /  </tspan>個人開発 undug</text>
    </g>

    <g class="rise" style="animation-delay:.5s">
      {glass_card(cx, cy, cw, ch, "#818cf8", "codeGlow", 2)}
      <circle cx="{cx + 24}" cy="{cy + 26}" r="5.5" fill="#ff5f57"/><circle cx="{cx + 44}" cy="{cy + 26}" r="5.5" fill="#febc2e"/><circle cx="{cx + 64}" cy="{cy + 26}" r="5.5" fill="#28c840"/>
      <text x="{cx + cw / 2}" y="{cy + 31}" text-anchor="middle" class="mono" font-size="12.5" fill="#a1a1aa">nozomu.ts</text>
      <rect x="{cx}" y="{cy + 50}" width="{cw}" height="1" fill="#fff" fill-opacity=".07"/>
      {"".join(code_lines)}
      <rect class="caret" x="{caret_x:.1f}" y="{last_y - 14}" width="8" height="18" fill="#818cf8"/>
    </g>

    {frame_border(w, h)}
  </g>
</svg>
'''


def build_stack() -> str:
    w, pad, gap, top = 1200, 32, 16, 112
    col = (w - pad * 2 - gap * 3) / 4
    # 行ごとに (高さ, [(カテゴリ, 横に使う列数, アイコンの列数)])
    rows_spec = [
        (270, [("frontend", 2, 6), ("backend", 2, 5)]),
        (250, [("web", 1, 2), ("vue", 1, 2), ("mobile", 1, 2), ("database", 1, 2)]),
        (270, [("aws", 2, 4), ("devops", 2, 3)]),
        (250, [("ai", 2, 3), ("motion", 1, 2), ("task", 1, 2)]),
    ]
    h = top + sum(rh for rh, _ in rows_spec) + gap * (len(rows_spec) - 1) + pad

    layout, y = [], top
    for rh, cells in rows_spec:
        c = 0
        for key, span_cols, icon_cols in cells:
            x = pad + c * (col + gap)
            layout.append((key, x, y, col * span_cols + gap * (span_cols - 1), rh, icon_cols))
            c += span_cols
        y += rh + gap

    cards, labels, uid = [], [], 0
    for idx, (key, x, y, cw, ch, cols) in enumerate(layout):
        name, accent, note, items = STACK[key]
        rows = -(-len(items) // cols)
        size = 46
        cell_w = (cw - 40) / cols
        head = 82 if note else 64
        area_top, area_h = y + head, ch - head - 14
        cell_h = area_h / rows
        icons = []
        for i, (label, source, ikey) in enumerate(items):
            uid += 1
            r, c = divmod(i, cols)
            ix = x + 20 + cell_w * c + cell_w / 2
            iy = area_top + cell_h * r + cell_h / 2 - 10
            body = icon_body(source, ikey, f"i{uid}-")
            icons.append(
                f'<svg x="{ix - size / 2:.1f}" y="{iy - size / 2:.1f}" width="{size}" height="{size}" viewBox="0 0 256 256">{body}</svg>'
                f'<text x="{ix:.1f}" y="{iy + size / 2 + 18:.1f}" text-anchor="middle" class="sans" font-size="12" fill="#a1a1aa">{escape(label)}</text>')
            labels.append(label)
        delay = .15 + idx * .12
        cards.append(f'''<g class="rise" style="animation-delay:{delay:.2f}s">
      {glass_card(x, y, cw, ch, accent, f"g{key}", 1.2 + idx * 1.1)}
      <circle cx="{x + 26}" cy="{y + 32}" r="4" fill="{accent}"/>
      <text x="{x + 40}" y="{y + 37}" class="sans" font-size="15" font-weight="600" fill="#fafafa">{escape(name)}</text>
      <text x="{x + cw - 22}" y="{y + 37}" text-anchor="end" class="mono" font-size="12" fill="#71717a">{len(items):02d}</text>
      <text x="{x + 26}" y="{y + 60}" class="sans" font-size="12" fill="#71717a">{escape(note)}</text>
      {"".join(icons)}
    </g>''')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">
  <title id="t">Tech Stack</title>
  <desc id="d">使用技術: {escape("、".join(labels))}</desc>
  <defs>{common_defs(w, h, 110)}</defs>
  <style>{BASE_CSS}{REDUCED_MOTION_CSS}
  </style>
  <g clip-path="url(#frame)">
    {backdrop(w, h, [(200, 140, 260, "#4f46e5", .45), (1050, 300, 240, "#be185d", .3), (700, 760, 260, "#0891b2", .3)])}
    <text x="{pad}" y="56" class="mono" font-size="12" letter-spacing="3" fill="#71717a">TECH STACK</text>
    <text x="{pad}" y="86" class="sans" font-size="26" font-weight="700" letter-spacing="-.5" fill="#fafafa">Tools I build with</text>
    <text x="{w - pad}" y="86" text-anchor="end" class="mono" font-size="12" fill="#71717a">{len(labels)} technologies</text>
    {"".join(cards)}
    {frame_border(w, h)}
  </g>
</svg>
'''


# lucide のアイコン形状(24x24)
ICON_PATHS = {
    "monitor": '<rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/>',
    "server": '<rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><path d="M6 6h.01M6 18h.01"/>',
    "cloud": '<path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>',
    "branch": '<line x1="6" x2="6" y1="3" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/>',
    "clapper": '<path d="M20.2 6 3 11l-.9-2.4c-.3-1.1.3-2.2 1.3-2.5l13.5-4c1.1-.3 2.2.3 2.5 1.3Z"/><path d="m6.2 5.3 3.1 3.9M12.4 3.4l3.1 4"/><path d="M3 11h18v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/>',
    "music": '<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>',
    "sparkles": '<path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/>',
}

# (タイトル, アイコン, アクセント色, 説明 2 行, タグ)
ABOUT_CARDS = [
    ("Frontend", "monitor", "#818cf8", ("React / Next.js を中心に、", "Vue.js や Expo のアプリも。"), ("Next.js", "Vue.js", "Expo")),
    ("Backend", "server", "#f472b6", ("Laravel・NestJS・FastAPI で", "API と業務ロジックを実装。"), ("Laravel", "NestJS", "FastAPI")),
    ("Infra", "cloud", "#fbbf24", ("AWS と Docker で環境を構築し、", "GitHub Actions でデプロイ。"), ("AWS", "Docker", "Actions")),
    ("AI", "sparkles", "#c084fc", ("Gemini API で生成 AI 機能を", "プロダクトに組み込む。"), ("Gemini API", "FastAPI", "Ollama")),
]

PROFILE_ROWS = [
    ("role", "Software Engineer"), ("focus", "Web / Mobile / API / AI"),
    ("langs", "TypeScript / PHP / Python"), ("writes", "zenn.dev/hopetekigozaru"), ("hobby", "guitar 🎸"),
]

# (ラベル, タイトル, アイコン, アクセント色, 説明 2 行, タグ, 演出, 幅)
HIGHLIGHTS = [
    ("SPECIALTY", "Parallel Development", "branch", "#34d399",
     ("Claude Code と git worktree で、", "複数のタスクを同時並行で開発する。"), ("Claude Code", "git worktree"), "worktree", 480),
    ("SIDE PROJECT", "undug", "music", "#f472b6",
     ("インディーズバンドの音楽・ライブ・", "リリースに出会えるプラットフォーム。"), ("Next.js", "NestJS", "Expo"), None, 312),
    ("LEARNING", "Video Generation", "clapper", "#38bdf8",
     ("Remotion と Three.js で、", "コードから動画をつくる勉強中。"), ("Remotion", "Three.js"), "cube", 312),
]


def worktree_visual(x: float, y: float, w: float, h: float) -> str:
    """main から worktree が分かれて戻る様子と、その上を走るエージェント。"""
    main_y = y + h / 2
    x0, x1 = x, x + w
    lanes = [(-44, 8, 36, "#818cf8"), (44, 36, 8, "#f472b6"), (-20, 62, 56, "#22d3ee")]
    out = [f'<line x1="{x0}" y1="{main_y}" x2="{x1}" y2="{main_y}" stroke="#a1a1aa" stroke-opacity=".5" stroke-width="2"/>',
           f'<text x="{x0}" y="{main_y + 18}" class="mono" font-size="10" fill="#71717a">main</text>']
    for i, (dy, ls, rs, color) in enumerate(lanes):
        sx, ex, ly = x0 + ls, x1 - rs, main_y + dy
        d = f"M{sx} {main_y} C{sx + 16} {main_y} {sx + 14} {ly} {sx + 32} {ly} L{ex - 32} {ly} C{ex - 14} {ly} {ex - 16} {main_y} {ex} {main_y}"
        out.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-opacity=".6" stroke-width="2"/>')
        straight = ex - sx - 88
        for k in range(3 if straight > 60 else 1):
            cx = sx + 44 + (k * straight / 2 if straight > 60 else straight / 2)
            out.append(f'<circle cx="{cx:.1f}" cy="{ly}" r="3.5" fill="{BG}" stroke="{color}" stroke-width="2"/>')
        out.append(f'<text x="{ex - 32}" y="{ly - 8}" text-anchor="end" class="mono" font-size="10" fill="{color}" fill-opacity=".8">wt-{i + 1}</text>')
        out.append(f'<circle r="5" fill="{color}"><animateMotion dur="{3.2 + i * .6:.1f}s" begin="{i * .9:.1f}s" repeatCount="indefinite" path="{d}"/></circle>')
    out += [f'<circle cx="{x0 + 4}" cy="{main_y}" r="4" fill="#a1a1aa"/>', f'<circle cx="{x1 - 4}" cy="{main_y}" r="4" fill="#a1a1aa"/>']
    return "".join(out)


def cube_visual(x: float, y: float, w: float, h: float) -> str:
    """Y 軸回転する立方体のワイヤーフレーム。"""
    import math
    cx, cy, size = x + w / 2, y + h / 2, min(w, h) / 3.4
    verts = [(a, b, c) for a in (-1, 1) for b in (-1, 1) for c in (-1, 1)]
    edges = [(i, j) for i in range(8) for j in range(i + 1, 8) if sum(p != q for p, q in zip(verts[i], verts[j])) == 1]
    tilt = math.radians(-24)
    frames = []
    for f in range(25):
        t = math.radians(30 + f * 90 / 24)
        pts = []
        for vx, vy, vz in verts:
            rx, rz = vx * math.cos(t) + vz * math.sin(t), -vx * math.sin(t) + vz * math.cos(t)
            ry = vy * math.cos(tilt) - rz * math.sin(tilt)
            pts.append((cx + rx * size, cy + ry * size))
        frames.append(" ".join(f"M{pts[i][0]:.1f} {pts[i][1]:.1f}L{pts[j][0]:.1f} {pts[j][1]:.1f}" for i, j in edges))
    return (f'<path d="{frames[0]}" fill="none" stroke="#38bdf8" stroke-width="2" stroke-linejoin="round">'
            f'<animate attributeName="d" values="{";".join(frames)}" dur="3s" repeatCount="indefinite"/></path>')


def card_head(x: float, y: float, icon: str, accent: str, title: str) -> str:
    return (f'<rect x="{x + 24}" y="{y + 22}" width="40" height="40" rx="11" fill="{accent}" fill-opacity=".14" stroke="{accent}" stroke-opacity=".4"/>'
            f'<g transform="translate({x + 34} {y + 32}) scale(.8333)" fill="none" stroke="{accent}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{ICON_PATHS[icon]}</g>'
            f'<text x="{x + 78}" y="{y + 48}" class="sans" font-size="18" font-weight="700" fill="#fafafa">{title}</text>')


def chips_row(x: float, y: float, tags: tuple[str, ...], accent: str) -> str:
    out, cx = [], x
    for t in tags:
        cw = len(t) * 7.2 + 20
        out.append(f'<rect x="{cx:.1f}" y="{y}" width="{cw:.1f}" height="22" rx="11" fill="{accent}" fill-opacity=".1" stroke="{accent}" stroke-opacity=".35"/>'
                   f'<text x="{cx + cw / 2:.1f}" y="{y + 15}" text-anchor="middle" class="mono" font-size="11.5" fill="#e4e4e7">{escape(t)}</text>')
        cx += cw + 8
    return "".join(out)


def build_about() -> str:
    w, pad, gap, top = 1200, 32, 16, 112
    card_h = 170
    intro_w, intro_h = 400, card_h * 2 + gap
    spec_h = 190
    h = top + intro_h + gap + spec_h + pad
    ix, iy = pad, top

    rows = "".join(
        f'<text x="{ix + 28}" y="{iy + 232 + i * 26}" class="mono" font-size="13.5" xml:space="preserve">'
        f'<tspan fill="#7dd3fc">{k}</tspan><tspan fill="#52525b" x="{ix + 100}">→</tspan>'
        f'<tspan fill="#e4e4e7" x="{ix + 124}">{escape(v)}</tspan></text>'
        for i, (k, v) in enumerate(PROFILE_ROWS))
    intro = f'''<g class="rise" style="animation-delay:.1s">
      {glass_card(ix, iy, intro_w, intro_h, "#818cf8", "gintro", 1)}
      <text x="{ix + 28}" y="{iy + 44}" class="mono" font-size="12" letter-spacing="2" fill="#71717a">HELLO, WORLD</text>
      <text x="{ix + 26}" y="{iy + 96}" class="sans" font-size="40" font-weight="800" letter-spacing="-1.5" fill="#fafafa">Hi, I’m Nozomu.</text>
      <text x="{ix + 28}" y="{iy + 140}" class="sans" font-size="15" fill="#a1a1aa">画面・API・インフラ・生成 AI まで、</text>
      <text x="{ix + 28}" y="{iy + 166}" class="sans" font-size="15" fill="#a1a1aa">つくるものに合わせて手を動かしています。</text>
      <rect x="{ix + 28}" y="{iy + 196}" width="{intro_w - 56}" height="1" fill="#fff" fill-opacity=".08"/>
      {rows}
    </g>'''

    cards = []
    cw = (w - pad * 2 - intro_w - gap * 2) / 2
    for i, (title, icon, accent, desc, tags) in enumerate(ABOUT_CARDS):
        r, c = divmod(i, 2)
        x = ix + intro_w + gap + c * (cw + gap)
        y = top + r * (card_h + gap)
        cards.append(f'''<g class="rise" style="animation-delay:{.25 + i * .12:.2f}s">
      {glass_card(x, y, cw, card_h, accent, f"gabout{i}", 2 + i * 1.3)}
      {card_head(x, y, icon, accent, title)}
      <text x="{x + cw - 24}" y="{y + 46}" text-anchor="end" class="mono" font-size="12" fill="#52525b">{i + 1:02d}</text>
      <text x="{x + 24}" y="{y + 92}" class="sans" font-size="14" fill="#a1a1aa">{escape(desc[0])}</text>
      <text x="{x + 24}" y="{y + 114}" class="sans" font-size="14" fill="#a1a1aa">{escape(desc[1])}</text>
      {chips_row(x + 24, y + 128, tags, accent)}
    </g>''')

    sy, x = top + intro_h + gap, pad
    visuals = {"worktree": lambda bx, bw: worktree_visual(bx + bw - 214, sy + 26, 190, spec_h - 52),
               "cube": lambda bx, bw: cube_visual(bx + bw - 76, sy + 112, 56, 56)}
    for i, (label, title, icon, accent, desc, tags, visual, bw) in enumerate(HIGHLIGHTS):
        cards.append(f'''<g class="rise" style="animation-delay:{.75 + i * .12:.2f}s">
      {glass_card(x, sy, bw, spec_h, accent, f"gspec{i}", 3 + i * 1.5)}
      {card_head(x, sy, icon, accent, title)}
      <rect x="{x + 78}" y="{sy + 62}" width="{len(label) * 7.6 + 18:.1f}" height="18" rx="9" fill="{accent}" fill-opacity=".14"/>
      <text x="{x + 87}" y="{sy + 75}" class="mono" font-size="10" letter-spacing="1.5" fill="{accent}">{label}</text>
      <text x="{x + 24}" y="{sy + 114}" class="sans" font-size="14" fill="#d4d4d8">{escape(desc[0])}</text>
      <text x="{x + 24}" y="{sy + 136}" class="sans" font-size="14" fill="#d4d4d8">{escape(desc[1])}</text>
      {chips_row(x + 24, sy + 152, tags, accent)}
      {visuals[visual](x, bw) if visual else ""}
    </g>''')
        x += bw + gap

    summary = "。".join(f"{t}: {d[0]}{d[1]}" for t, _, _, d, _ in ABOUT_CARDS)
    summary += "。" + "。".join(f"{lb}: {t} — {d[0]}{d[1]}" for lb, t, _, _, d, *_ in HIGHLIGHTS)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">
  <title id="t">About — Hi, I’m Nozomu.</title>
  <desc id="d">画面・API・インフラ・生成 AI まで、つくるものに合わせて手を動かしています。{escape(summary)}</desc>
  <defs>{common_defs(w, h, 100)}</defs>
  <style>{BASE_CSS}{REDUCED_MOTION_CSS}
  </style>
  <g clip-path="url(#frame)">
    {backdrop(w, h, [(1000, 80, 240, "#7c3aed", .4), (180, 520, 220, "#0891b2", .3), (620, 300, 200, "#db2777", .18)])}
    <text x="{pad}" y="56" class="mono" font-size="12" letter-spacing="3" fill="#71717a">ABOUT</text>
    <text x="{pad}" y="86" class="sans" font-size="26" font-weight="700" letter-spacing="-.5" fill="#fafafa">What I do</text>
    {intro}
    {"".join(cards)}
    {frame_border(w, h)}
  </g>
</svg>
'''


def build_footer() -> str:
    w, h = 1200, 120
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t">
  <title id="t">Thanks for visiting</title>
  <defs>{common_defs(w, h, 60)}</defs>
  <style>{BASE_CSS}{REDUCED_MOTION_CSS}
  </style>
  <g clip-path="url(#frame)">
    {backdrop(w, h, [(300, 160, 160, "#4f46e5", .45), (900, -40, 160, "#be185d", .35)], grid=40)}
    <text x="{w / 2}" y="58" text-anchor="middle" class="sans" font-size="20" font-weight="600" fill="#fafafa" letter-spacing="-.3">Thanks for visiting</text>
    <text x="{w / 2}" y="84" text-anchor="middle" class="mono" font-size="12" fill="#71717a" letter-spacing="1.5">github.com/hosokaSfi  ·  zenn.dev/hopetekigozaru</text>
    {frame_border(w, h)}
  </g>
</svg>
'''


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    for name, build in (("header", build_header), ("about", build_about), ("stack", build_stack), ("footer", build_footer)):
        (ASSETS / f"{name}.svg").write_text(build(), encoding="utf-8")
        print(f"generated assets/{name}.svg")


if __name__ == "__main__":
    main()
