#!/usr/bin/env bash
# Cloudflare Pages 배포용 폴더(_site) — 사이트에 필요한 파일만 (server/, tests/ 등 제외)
set -e
cd "$(dirname "$0")/.."
rm -rf _site && mkdir _site
for f in index.html feed.json prices.json sunday.png favicon.png apple-touch-icon.png robots.txt sitemap.xml og.png epicbeam_sprite.webp; do [ -f "$f" ] && cp "$f" _site/; done
[ -d ocr ] && cp -r ocr _site/  # b283: 화면 자동 기록 OCR (tesseract.js·kor, Apache-2.0)
[ -f data/bosses_auto.json ] && mkdir -p _site/data && cp data/bosses_auto.json _site/data/  # b251
printf '/*\n  Cache-Control: no-cache\n' > _site/_headers
echo "_site: $(ls _site | tr '\n' ' ')"
