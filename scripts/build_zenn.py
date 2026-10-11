"""Zenn の最新記事カード(SVG)を生成する。

使い方: python3 scripts/build_zenn.py [出力先]  (既定: assets/zenn.svg)
GitHub Actions で毎日実行し、output ブランチに置いている。
"""

import json
import re
import sys
from pathlib import Path

from build_assets import (BASE_CSS, REDUCED_MOTION_CSS, backdrop, common_defs, escape, fetch, frame_border,
                          glass_card)

USERNAME = "hopetekigozaru"
MAX_ARTICLES = 3
ZENN_BLUE = "#3ea8ff"
TITLE_UNITS = 52  # タイトルの表示幅の上限(全角 1、半角 0.55 で数える)


def truncate(text: str, limit: float) -> str:
    units = 0.0
    for i, ch in enumerate(text):
        units += 0.55 if ord(ch) < 0x2E80 else 1
        if units > limit:
            return text[:i].rstrip() + "…"
    return text


def build(articles: list[dict], user: dict, zenn_path: str) -> str:
    w, pad, gap, top, row_h = 1200, 32, 12, 112, 84
    n = max(len(articles), 1)
    h = top + n * row_h + (n - 1) * gap + pad

    rows = []
    for i, a in enumerate(articles):
        y = top + i * (row_h + gap)
        date = a["published_at"][:10].replace("-", ".")
        rows.append(f'''<g class="rise" style="animation-delay:{.2 + i * .12:.2f}s">
      {glass_card(pad, y, w - pad * 2, row_h, ZENN_BLUE, f"za{i}", 1.5 + i * 1.4)}
      <rect x="{pad + 20}" y="{y + 18}" width="48" height="48" rx="12" fill="#ffffff" fill-opacity=".06" stroke="#fff" stroke-opacity=".08"/>
      <text x="{pad + 44}" y="{y + 51}" text-anchor="middle" font-size="24">{escape(a["emoji"])}</text>
      <text x="{pad + 88}" y="{y + 38}" class="sans" font-size="17" font-weight="600" fill="#fafafa">{escape(truncate(a["title"], TITLE_UNITS))}</text>
      <text x="{pad + 88}" y="{y + 62}" class="mono" font-size="12" fill="#71717a">{date}  ·  ♥ {a["liked_count"]}  ·  {escape(a.get("article_type") or "tech")}</text>
      <text x="{w - pad - 28}" y="{y + 49}" text-anchor="end" class="sans" font-size="20" fill="{ZENN_BLUE}">→</text>
    </g>''')
    if not articles:
        rows.append(f'<text x="{pad}" y="{top + 40}" class="sans" font-size="16" fill="#a1a1aa">まだ記事がありません</text>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">
  <title id="t">Zenn の最新記事</title>
  <desc id="d">{escape(" / ".join(a["title"] for a in articles))}</desc>
  <defs>{common_defs(w, h, 90)}</defs>
  <style>{BASE_CSS}{REDUCED_MOTION_CSS}
  </style>
  <g clip-path="url(#frame)">
    {backdrop(w, h, [(1050, 60, 220, "#1d4ed8", .45), (200, h + 40, 220, "#0891b2", .3)])}
    <text x="{pad}" y="56" class="mono" font-size="12" letter-spacing="3" fill="#71717a">WRITING</text>
    <g transform="translate({pad} 66) scale(1)">
      <svg width="26" height="26" viewBox="0 0 24 24"><path fill="{ZENN_BLUE}" d="{zenn_path}"/></svg>
    </g>
    <text x="{pad + 36}" y="86" class="sans" font-size="26" font-weight="700" letter-spacing="-.5" fill="#fafafa">Latest on Zenn</text>
    <text x="{w - pad}" y="66" text-anchor="end" class="mono" font-size="12" fill="{ZENN_BLUE}">zenn.dev/{USERNAME} →</text>
    <text x="{w - pad}" y="86" text-anchor="end" class="mono" font-size="12" fill="#71717a">{user.get("articles_count", len(articles))} articles  ·  ♥ {user.get("total_liked_count", 0)}</text>
    {"".join(rows)}
    {frame_border(w, h)}
  </g>
</svg>
'''


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "assets" / "zenn.svg"
    articles = json.loads(fetch(f"https://zenn.dev/api/articles?username={USERNAME}&order=latest"))["articles"][:MAX_ARTICLES]
    user = json.loads(fetch(f"https://zenn.dev/api/users/{USERNAME}"))["user"]
    zenn_path = re.search(r'<path d="([^"]+)"', fetch("https://cdn.simpleicons.org/zenn")).group(1)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(articles, user, zenn_path), encoding="utf-8")
    print(f"generated {out}")


if __name__ == "__main__":
    main()
